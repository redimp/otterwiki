#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
Tests for the noemojis plugin example. The plugin is loaded straight from
its file via the example_plugin_loader fixture, it does not need to be
installed.
"""

import pytest


def save_page(client, pagename, content, message="test"):
    rv = client.post(
        "/{}/save".format(pagename),
        data={"content": content, "commit": message},
        follow_redirects=True,
    )
    assert rv.status_code == 200


@pytest.fixture
def plugin(example_plugin_loader):
    _, plugins = example_plugin_loader("plugin_noemojis")
    (plugin,) = plugins
    return plugin


def test_markdown_preprocess_strips_emojis(plugin):
    assert plugin.renderer_markdown_preprocess("👴") == ""
    assert (
        plugin.renderer_markdown_preprocess("🕶H🦴ello, W🎲orld😇!")
        == "Hello, World!"
    )


def test_rendered_page_has_no_emojis(plugin, test_client):
    save_page(test_client, "Emojipage", "# Emojipage\n\nHello 🦦 World!")
    html = test_client.get("/Emojipage").data.decode()
    assert "🦦" not in html
    assert "Hello" in html
    assert "World!" in html
