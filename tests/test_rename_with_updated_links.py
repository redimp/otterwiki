#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import re

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
        data={"new_pagename": new_pagename, "message": ""},
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
