#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import re
import subprocess

import pytest


@pytest.fixture
def test_client(create_app):
    return create_app.test_client()


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


def rename_shortcut(test_client, pagename, new_pagename):
    rv = test_client.post(
        "/{}/rename".format(pagename),
        data={
            "new_pagename": new_pagename,
            "message": "",
            "update_backlinks": "1",
        },
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
