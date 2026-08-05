#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import re
import subprocess
import sys

import pytest

from otterwiki.plugins import hookimpl


@pytest.fixture
def test_client(create_app):
    return create_app.test_client()


def _get_plugin_manager():
    """Get the current plugin_manager, even after module reloads by other
    tests."""
    return sys.modules["otterwiki.plugins"].plugin_manager


class RenameHookRecorder:
    """Test plugin recording the hooks fired while backlinks are rewritten."""

    def __init__(self):
        self.saved = []
        self.renamed = []
        self.repository_changed_calls = []

    @hookimpl
    def page_saved(self, pagepath, content, author, message):
        self.saved.append(
            {
                "pagepath": pagepath,
                "content": content,
                "author": author,
                "message": message,
            }
        )

    @hookimpl
    def page_renamed(self, old_pagepath, new_pagepath, author, message):
        self.renamed.append(
            {"old_pagepath": old_pagepath, "new_pagepath": new_pagepath}
        )

    @hookimpl
    def repository_changed(self, changed_files):
        self.repository_changed_calls.append(list(changed_files))


@pytest.fixture
def hook_recorder():
    recorder = RenameHookRecorder()
    _get_plugin_manager().register(recorder)
    yield recorder
    _get_plugin_manager().unregister(recorder)


def save_shortcut(test_client, pagename, content, commit_message):
    rv = test_client.post(
        "/{}/save".format(pagename),
        data={
            "content": content,
            "commit": commit_message,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200


def rename_shortcut(
    test_client, pagename, new_pagename, update_backlinks=True
):
    data = {
        "new_pagename": new_pagename,
        "message": "",
    }
    # an unchecked checkbox is not submitted by the browser at all
    if update_backlinks:
        data["update_backlinks"] = "1"
    rv = test_client.post(
        "/{}/rename".format(pagename),
        data=data,
        follow_redirects=True,
    )
    assert rv.status_code == 200


def find_link_href(html, text):
    """Return the href of the rendered anchor with the given link text,
    or None if the link was not rendered as an anchor at all."""
    m = re.search(
        r'<a[^>]*href="([^"]*)"[^>]*>{}</a>'.format(re.escape(text)),
        html,
    )
    return m.group(1) if m else None


def _git_show(storage, filename, revision="HEAD"):
    """Return the committed content of ``filename`` at ``revision``."""
    return subprocess.check_output(
        ["git", "-C", storage.path, "show", f"{revision}:{filename}"],
    ).decode()


def _git_status(storage):
    """Return the porcelain status of the storage repository."""
    return subprocess.check_output(
        ["git", "-C", storage.path, "status", "--porcelain"],
    ).decode()


def test_rename_commits_the_rewritten_backlinks(test_client):
    """The rewritten backlinks must be part of the rename commit, not just
    written to the working tree. rename_backlinks() writes the pages with
    storage.update() (working tree only, no ``git add``) and the rename is
    committed with ``no_add=True``, so the rewritten content never makes it
    into git history."""
    storage = test_client.application.storage
    save_shortcut(
        test_client, "CommitTarget", "# CommitTarget\n", "created target"
    )
    save_shortcut(
        test_client,
        "CommitLinker",
        "# CommitLinker\n\n[a link](/CommitTarget)\n",
        "created linker",
    )
    rename_shortcut(test_client, "CommitTarget", "CommitRenamed")

    # the working tree is rewritten ...
    assert "/CommitRenamed" in storage.load("commitlinker.md")
    # ... but the committed version must be rewritten too
    committed = _git_show(storage, "commitlinker.md")
    assert "/CommitRenamed" in committed, (
        "backlink rewrite was not committed: HEAD:commitlinker.md still reads "
        f"{committed!r}"
    )


def test_rename_without_update_backlinks_leaves_links_untouched(test_client):
    """With the 'Update backlinks' checkbox unchecked the field is not
    submitted at all. The rename must still happen, but no other page may be
    touched and no extra commit may show up in the history."""
    storage = test_client.application.storage
    save_shortcut(test_client, "OptOutTarget", "# OptOutTarget\n", "target")
    linker = (
        "# OptOutLinker\n\n"
        "[a link](/OptOutTarget)\n"
        "[[OptOutTarget]]\n"
        "![](/OptOutTarget/otter.png)\n"
    )
    save_shortcut(test_client, "OptOutLinker", linker, "linker")
    log_before = storage.log("optoutlinker.md")

    rename_shortcut(
        test_client, "OptOutTarget", "OptOutRenamed", update_backlinks=False
    )

    # the rename itself happened ...
    assert storage.exists("optoutrenamed.md")
    assert not storage.exists("optouttarget.md")
    # ... the linking page is untouched in the working tree ...
    assert storage.load("optoutlinker.md") == linker
    # ... and in git history, no new commit touched it ...
    assert _git_show(storage, "optoutlinker.md") == linker
    assert len(storage.log("optoutlinker.md")) == len(log_before)
    # ... and nothing is left dangling.
    assert _git_status(storage) == ""


def test_rename_leaves_no_uncommitted_changes(test_client):
    """After a rename with backlink updates the repository must be clean.
    Because the rewritten backlinks are only written to the working tree and
    never staged, they are left dangling as uncommitted modifications."""
    storage = test_client.application.storage
    save_shortcut(
        test_client, "StatusTarget", "# StatusTarget\n", "created target"
    )
    save_shortcut(
        test_client,
        "StatusLinker",
        "# StatusLinker\n\n[a link](/StatusTarget)\n",
        "created linker",
    )
    rename_shortcut(test_client, "StatusTarget", "StatusRenamed")

    status = _git_status(storage)
    assert status == "", (
        "repository left dirty after rename; uncommitted changes:\n" + status
    )


def test_rename_rolls_back_when_backlink_rewrite_fails(
    test_client, monkeypatch
):
    """If any step fails after the rename has been staged, the repository
    must be rolled back to its previous state - neither the staged rename nor
    the partially rewritten backlinks may be left in the working tree."""
    storage = test_client.application.storage
    save_shortcut(
        test_client, "RollbackTarget", "# RollbackTarget\n", "created target"
    )
    save_shortcut(
        test_client,
        "RollbackLinker",
        "# RollbackLinker\n\n[a link](/RollbackTarget)\n",
        "created linker",
    )
    head_before = _git_show(storage, "rollbacktarget.md")

    def boom(*args, **kwargs):
        raise RuntimeError("simulated backlink rewrite failure")

    monkeypatch.setattr("otterwiki.wiki.rename_backlinks", boom)

    # the rename must fail gracefully (handle_rename catches and toasts)
    rv = test_client.post(
        "/RollbackTarget/rename",
        data={
            "new_pagename": "RollbackRenamed",
            "message": "",
            "update_backlinks": "1",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # the repository must be clean ...
    status = _git_status(storage)
    assert status == "", (
        "repository left dirty after failed rename; uncommitted changes:\n"
        + status
    )
    # ... the original page must still exist under its old name ...
    assert storage.exists("rollbacktarget.md")
    assert not storage.exists("rollbackrenamed.md")
    # ... and the backlink must be untouched.
    assert _git_show(storage, "rollbacktarget.md") == head_before


def test_rename_updates_percent_encoded_markdown_link(test_client):
    """Markdown links to a page with a space in its name are commonly
    written percent-encoded, e.g. [a link](/Target%20Page). Renaming
    'Target Page' must update these links, too."""
    save_shortcut(
        test_client,
        "Target Page",
        "# Target Page\n",
        "created target",
    )
    save_shortcut(
        test_client,
        "Linker",
        "# Linker\n\n[a link](/Target%20Page)\n",
        "created linker",
    )
    rename_shortcut(test_client, "Target Page", "RenamedTarget")
    # the encoded link to the old name must be gone from the linking page
    content = test_client.application.storage.load("linker.md")
    assert "target%20page" not in content.lower()
    # and the rendered link must resolve to the renamed page
    html = test_client.get("/Linker/view").data.decode()
    href = find_link_href(html, "a link")
    assert href is not None, "link is no longer rendered as an anchor"
    rv = test_client.get(href)
    assert rv.status_code == 200
    assert "Target Page" in rv.data.decode()


def test_rename_to_name_with_space_keeps_link_parseable(test_client):
    """When a page is renamed to a name containing a space, the
    rewritten link destination must not contain a raw space:
    [a link](/New Name) is not parsed as a markdown link."""
    save_shortcut(
        test_client,
        "Source",
        "# Source\n",
        "created source",
    )
    save_shortcut(
        test_client,
        "Linker",
        "# Linker\n\n[a link](/Source)\n",
        "created linker",
    )
    rename_shortcut(test_client, "Source", "New Name")
    # a raw space in the link destination breaks the markdown link
    content = test_client.application.storage.load("linker.md")
    assert "](/New Name)" not in content
    # the rendered link must still be an anchor and resolve to the
    # renamed page
    html = test_client.get("/Linker/view").data.decode()
    href = find_link_href(html, "a link")
    assert href is not None, "link is no longer rendered as an anchor"
    rv = test_client.get(href)
    assert rv.status_code == 200
    assert "Source" in rv.data.decode()


def test_page_saved_hook_fired_for_each_updated_backlink(
    test_client, hook_recorder
):
    """Every page whose backlinks were rewritten must be announced via the
    page_saved hook - and only those, pages left untouched must not fire."""
    save_shortcut(test_client, "HookTarget", "# HookTarget\n", "target")
    save_shortcut(
        test_client,
        "HookLinkerOne",
        "# HookLinkerOne\n\n[a link](/HookTarget)\n",
        "linker one",
    )
    save_shortcut(
        test_client,
        "HookLinkerTwo",
        "# HookLinkerTwo\n\n[[HookTarget]]\n",
        "linker two",
    )
    save_shortcut(
        test_client,
        "HookUnrelated",
        "# HookUnrelated\n\n[elsewhere](/SomewhereElse)\n",
        "unrelated",
    )
    # only the hooks fired by the rename itself are of interest
    hook_recorder.saved.clear()

    rename_shortcut(test_client, "HookTarget", "HookRenamed")

    # page_saved must carry a pagepath, like Page.save() does, not the
    # on-disk filename
    assert {call["pagepath"] for call in hook_recorder.saved} == {
        "Hooklinkerone",
        "Hooklinkertwo",
    }
    by_page = {call["pagepath"]: call for call in hook_recorder.saved}
    # the hook must carry the rewritten content, not the old one
    assert "[a link](/HookRenamed)" in by_page["Hooklinkerone"]["content"]
    assert "[[HookRenamed]]" in by_page["Hooklinkertwo"]["content"]
    # and the commit message of the rename
    assert by_page["Hooklinkerone"]["message"] == (
        "Renamed HookTarget to HookRenamed."
    )
    # the reported pagepath must be usable as one: it has to address the
    # page it belongs to
    for pagepath in by_page:
        rv = test_client.get("/{}/view".format(pagepath))
        assert rv.status_code == 200, f"{pagepath} does not address a page"
    # the rename itself is still announced separately
    assert hook_recorder.renamed == [
        {"old_pagepath": "HookTarget", "new_pagepath": "HookRenamed"}
    ]


def test_page_saved_hook_not_fired_without_update_backlinks(
    test_client, hook_recorder
):
    """With the 'Update backlinks' checkbox unchecked no page is rewritten,
    so no page_saved hook may fire - only page_renamed."""
    save_shortcut(test_client, "QuietTarget", "# QuietTarget\n", "target")
    save_shortcut(
        test_client,
        "QuietLinker",
        "# QuietLinker\n\n[a link](/QuietTarget)\n",
        "linker",
    )
    hook_recorder.saved.clear()

    rename_shortcut(
        test_client, "QuietTarget", "QuietRenamed", update_backlinks=False
    )

    assert hook_recorder.saved == []
    assert len(hook_recorder.renamed) == 1


def test_repository_changed_hook_includes_rewritten_backlinks(
    test_client, hook_recorder
):
    """The rename and the rewritten backlinks land in a single commit, so
    repository_changed must fire once and list all of them together."""
    save_shortcut(test_client, "RepoTarget", "# RepoTarget\n", "target")
    save_shortcut(
        test_client,
        "RepoLinker",
        "# RepoLinker\n\n[a link](/RepoTarget)\n",
        "linker",
    )
    save_shortcut(
        test_client,
        "RepoUnrelated",
        "# RepoUnrelated\n",
        "unrelated",
    )
    hook_recorder.repository_changed_calls.clear()

    rename_shortcut(test_client, "RepoTarget", "RepoRenamed")

    assert len(hook_recorder.repository_changed_calls) == 1, (
        "rename and backlink rewrites must be committed once, got "
        f"{hook_recorder.repository_changed_calls!r}"
    )
    changed_files = hook_recorder.repository_changed_calls[0]
    assert set(changed_files) == {"reporenamed.md", "repolinker.md"}


def test_repository_changed_hook_not_fired_when_rename_rolls_back(
    test_client, hook_recorder, monkeypatch
):
    """A rename that fails is rolled back, so no commit happens and neither
    repository_changed nor page_saved may be announced."""
    save_shortcut(test_client, "FailTarget", "# FailTarget\n", "target")
    save_shortcut(
        test_client,
        "FailLinker",
        "# FailLinker\n\n[a link](/FailTarget)\n",
        "linker",
    )

    def boom(*args, **kwargs):
        raise RuntimeError("simulated backlink rewrite failure")

    monkeypatch.setattr("otterwiki.wiki.rename_backlinks", boom)
    # the two saves above prove the recorder is wired up, so the emptiness
    # asserted below cannot pass vacuously
    assert len(hook_recorder.saved) == 2
    saved_before = len(hook_recorder.saved)
    changes_before = len(hook_recorder.repository_changed_calls)

    rename_shortcut(test_client, "FailTarget", "FailRenamed")

    assert len(hook_recorder.repository_changed_calls) == changes_before
    assert len(hook_recorder.saved) == saved_before
    assert hook_recorder.renamed == []
