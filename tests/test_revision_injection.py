#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
Regression tests for git argument injection via user-supplied revision
parameters (CWE-88). A revision that git would parse as a CLI option
(leading '-') must never reach the git binary. These drive the real
HTTP routes with anonymous READ access (the default).
"""

import os
import pytest


def save_shortcut(test_client, pagename, content, commit_message):
    rv = test_client.post(
        "/{}/save".format(pagename),
        data={"content": content, "commit": commit_message},
        follow_redirects=True,
    )
    assert rv.status_code == 200


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
