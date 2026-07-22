#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import pytest


def save_shortcut(test_client, pagename, content, commit_message):
    rv = test_client.post(
        "/{}/save".format(pagename),
        data={"content": content, "commit": commit_message},
        follow_redirects=True,
    )
    assert rv.status_code == 200


# Security regression tests for user-supplied revision parameters. Covers
# git argument injection (CWE-88) -- a revision git would parse as a CLI
# option (leading '-') must never reach the git binary -- and the file
# disclosure / page corruption it would otherwise enable. These drive the
# real HTTP routes with anonymous READ access (the default).


def test_diff_route_output_injection_does_not_corrupt_page(
    test_client, create_app
):
    storage = create_app.storage
    save_shortcut(test_client, "Home", "# Welcome\n\nHome page.\n", "initial")
    commit = storage.log()[0]["revision"]

    before = storage.load("Home.md")

    rv = test_client.get("/Home/diff/--output=Home.md/{}".format(commit))
    assert rv.status_code == 404
    # the page on disk must be untouched, not overwritten with diff output
    assert storage.load("Home.md") == before
    assert "diff --git" not in storage.load("Home.md")


def test_blame_route_contents_injection_does_not_leak_file(
    test_client, create_app
):
    storage = create_app.storage
    save_shortcut(test_client, "Home", "# Home\n", "initial")
    # a secret file at the repository root
    with open(os.path.join(storage.path, ".env"), "w") as f:
        f.write("DB_PASSWORD=supersecret123\nAPI_KEY=sk-abc123456\n")

    rv = test_client.get("/Home/blame/--contents=.env")
    assert rv.status_code == 404
    assert b"supersecret123" not in rv.data


@pytest.mark.parametrize(
    "revision", ["--output=x.md", "--contents=.env", "-p", "HEAD~1", "main"]
)
def test_view_route_rejects_invalid_revision(
    test_client, create_app, revision
):
    save_shortcut(test_client, "Home", "# Home\n", "initial")
    rv = test_client.get("/Home/view/{}".format(revision))
    assert rv.status_code == 404


# every revision-bearing read endpoint, hit with a --contents= payload that
# would read a file from the working directory (not the git tree). No endpoint
# may disclose an uncommitted secret sitting at the repository root or inside
# .git (e.g. credentials embedded in a remote URL in .git/config). The
# attachment route takes the revision from a query parameter, so it is the
# only one able to carry a '/' and reach a nested path like .git/config.
CONTENTS_DISCLOSURE_URLS = [
    "/Home/blame/--contents=.env",
    "/Home/blame/--contents=/etc/hostname",
    "/Home/view/--contents=.env",
    "/Home/source/--contents=.env",
    "/Home/edit/--contents=.env",
    "/-/commit/--contents=.env",
    "/Home/a/x/--contents=.env",
    "/Home/a/x?revision=--contents=.git/config",
    "/Home/diff/--output=x/--contents=.env",
]


@pytest.mark.parametrize("url", CONTENTS_DISCLOSURE_URLS)
def test_no_filesystem_disclosure_via_revision(test_client, create_app, url):
    storage = create_app.storage
    save_shortcut(test_client, "Home", "# Home\nline2\n", "initial")
    # an uncommitted secret on the filesystem at the repository root ...
    with open(os.path.join(storage.path, ".env"), "w") as f:
        f.write("DB_PASSWORD=uncommitted_secret\n")
    # ... and one embedded in .git/config, as a remote URL password would be
    with open(os.path.join(storage.path, ".git", "config"), "a") as f:
        f.write(
            '\n[remote "origin"]\n'
            '\turl = https://user:uncommitted_secret@example.com/x.git\n'
        )

    rv = test_client.get(url)
    assert b"uncommitted_secret" not in rv.data


# a committed, non-page file at the repository root must not be readable by
# crafting the page path (dots are stripped, a .md suffix is forced).
@pytest.mark.parametrize(
    "url",
    [
        "/.env/view/HEAD",
        "/secret.txt/view/HEAD",
        "/secret/source/HEAD",
        "/Home/a/secret.txt?revision=HEAD",
        "/Home/a/.env?revision=HEAD",
    ],
)
def test_no_disclosure_of_nonpage_files(test_client, create_app, url):
    storage = create_app.storage
    save_shortcut(test_client, "Home", "# Home\n", "initial")
    with open(os.path.join(storage.path, "secret.txt"), "w") as f:
        f.write("COMMITTED_SECRET=abc\n")
    storage.commit(["secret.txt"], message="add secret")

    rv = test_client.get(url)
    assert b"COMMITTED_SECRET" not in rv.data


def test_valid_revision_routes_still_work(test_client, create_app):
    storage = create_app.storage
    save_shortcut(test_client, "Home", "# Home\nline2\n", "initial")
    save_shortcut(test_client, "Home", "# Home\nline2\nline3\n", "second")
    log = storage.log()
    rev_b, rev_a = log[0]["revision"], log[1]["revision"]

    # diff between two valid revisions
    rv = test_client.get("/Home/diff/{}/{}".format(rev_a, rev_b))
    assert rv.status_code == 200

    # blame at a valid revision
    rv = test_client.get("/Home/blame/{}".format(rev_a))
    assert rv.status_code == 200

    # view an older revision
    rv = test_client.get("/Home/view/{}".format(rev_a))
    assert rv.status_code == 200
