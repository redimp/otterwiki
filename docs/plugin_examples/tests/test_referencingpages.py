#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
Tests for the referencingpages plugin example. The plugin is loaded
straight from its file via the example_plugin_loader fixture, it does not
need to be installed.
"""

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

    _, plugins = example_plugin_loader("plugin_referencingpages")
    (plugin,) = plugins
    plugin.setup(app=create_app, db=db, storage=create_app.storage)
    return plugin


def test_setup_builds_index_from_existing_pages(
    create_app, test_client, example_plugin_loader
):
    from otterwiki.server import db

    # pages exist before the plugin is loaded
    save_page(
        test_client, "Refexistingsource", "link to [[Refexistingtarget]]"
    )
    save_page(test_client, "Refexistingtarget", "# target")

    _, plugins = example_plugin_loader("plugin_referencingpages")
    (plugin,) = plugins
    plugin.setup(app=create_app, db=db, storage=create_app.storage)

    assert "refexistingsource" in plugin.references["refexistingtarget"]


def test_repository_changed_updates_index(plugin, test_client):
    assert "reflivetarget" not in plugin.references
    save_page(test_client, "Reflivesource", "see [[Reflivetarget]]")
    assert plugin.references["reflivetarget"] == ["reflivesource"]
    # editing the link away removes the entry from the index
    save_page(test_client, "Reflivesource", "no more links")
    assert "reflivetarget" not in plugin.references


def test_page_deleted_removes_references(plugin, test_client):
    save_page(test_client, "Refdeletesource", "see [[Refdeletetarget]]")
    assert plugin.references["refdeletetarget"] == ["refdeletesource"]
    rv = test_client.post(
        "/Refdeletesource/delete",
        data={"message": "delete page"},
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "refdeletetarget" not in plugin.references


def test_sidebar_lists_referencing_pages(plugin, test_client):
    save_page(test_client, "Refsidebarsource", "link to [[Refsidebartarget]]")
    save_page(test_client, "Refsidebartarget", "# target")
    html = test_client.get("/Refsidebartarget").data.decode()
    assert "Referencing pages" in html
    assert 'href="/Refsidebarsource"' in html


def test_sidebar_absent_without_references(plugin, test_client):
    save_page(test_client, "Refplainpage", "no links here")
    html = test_client.get("/Refplainpage").data.decode()
    assert "Referencing pages" not in html


def test_self_reference_is_ignored(plugin, test_client):
    save_page(test_client, "Refselfpage", "i link [[Refselfpage]]")
    assert "refselfpage" not in plugin.references
