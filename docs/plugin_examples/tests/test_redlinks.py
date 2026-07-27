#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
Tests for the redlinks plugin example. The plugin is loaded straight from
its file via the example_plugin_loader fixture, it does not need to be
installed.
"""

import re

import pytest


def save_page(client, pagename, content, message="test"):
    rv = client.post(
        "/{}/save".format(pagename),
        data={"content": content, "commit": message},
        follow_redirects=True,
    )
    assert rv.status_code == 200


@pytest.fixture(autouse=True)
def retain_page_name_case_off(create_app):
    # pin the config other tests may have changed, the assertions below
    # rely on the default lower case page names
    saved = create_app.config["RETAIN_PAGE_NAME_CASE"]
    create_app.config["RETAIN_PAGE_NAME_CASE"] = False
    yield
    create_app.config["RETAIN_PAGE_NAME_CASE"] = saved


@pytest.fixture
def plugin(create_app, retain_page_name_case_off, example_plugin_loader):
    from otterwiki.server import db

    _, plugins = example_plugin_loader("plugin_redlinks")
    (plugin,) = plugins
    plugin.setup(app=create_app, db=db, storage=create_app.storage)
    return plugin


def test_missing_page_link_is_marked_red(plugin, test_client):
    save_page(
        test_client,
        "Redsourcepage",
        "see [[Redmissingpage]] and [[Redexistingpage]]",
    )
    save_page(test_client, "Redexistingpage", "# Redexistingpage")
    html = test_client.get("/Redsourcepage").data.decode()
    # the link to the missing page is marked red
    assert re.search(r'<a class="redlink"[^>]*href="/Redmissingpage"', html)
    # the link to the existing page is not
    existing = re.search(r'<a[^>]*href="/Redexistingpage"[^>]*>', html)
    assert existing is not None
    assert "redlink" not in existing.group(0)


def test_wikilinks_untouched_without_plugin(test_client):
    save_page(test_client, "Rednopluginpage", "see [[Redmissingpage]]")
    html = test_client.get("/Rednopluginpage").data.decode()
    assert "redlink" not in html
