#!/usr/bin/env python

"""Tests for the example plugin docs/plugin_examples/plugin_referencingpages.

The plugin builds the "referenced by" backlink index shown in the right
sidebar. This is a regression test for links that carry a #anchor or a
leading slash, which previously were not matched against the page path.

The example plugins live under docs/ and are not installed, so the plugin
module is loaded by path. Importing it auto-registers an instance; that
instance is removed again so each test controls registration explicitly.
"""

import importlib.util
import os
import sys

DOCS_PLUGINS = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "docs", "plugin_examples")
)


def _get_plugin_manager():
    return sys.modules["otterwiki.plugins"].plugin_manager


def _load_example_plugin(subdir, filename, class_name):
    path = os.path.join(DOCS_PLUGINS, subdir, filename)
    spec = importlib.util.spec_from_file_location(filename[:-3], path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pm = _get_plugin_manager()
    for plugin in list(pm.get_plugins()):
        if type(plugin).__name__ == class_name:
            pm.unregister(plugin)
    return getattr(module, class_name)


def save_page(client, pagename, content, commit_message="create"):
    rv = client.post(
        "/{}/save".format(pagename),
        data={"content": content, "commit": commit_message},
        follow_redirects=True,
    )
    assert rv.status_code == 200


def _build_plugin(create_app):
    cls = _load_example_plugin(
        "plugin_referencingpages",
        "otterwiki_referencingpages.py",
        "ReferencingPages",
    )
    from otterwiki.server import db

    plugin = cls()
    plugin.setup(app=create_app, db=db, storage=create_app.storage)
    return plugin


def test_indexes_anchored_and_plain_links(test_client, create_app):
    save_page(test_client, "BacklinkTarget", "# Target")
    save_page(test_client, "PlainReferrer", "See [[BacklinkTarget]]")
    save_page(test_client, "AnchorReferrer", "See [[BacklinkTarget#hello]]")

    plugin = _build_plugin(create_app)
    html = plugin.template_html_sidebar_right_inject(page="BacklinkTarget")

    assert html is not None
    # the plain link was always found; the anchored link is the regression
    assert "plainreferrer" in html.lower()
    assert "anchorreferrer" in html.lower()


def test_ignores_pure_anchor_links(test_client, create_app):
    save_page(test_client, "SoloTarget", "# Target")
    # a self/in-page anchor link must not crash or create a backlink
    save_page(test_client, "SoloReferrer", "Jump [[#section]] only")

    plugin = _build_plugin(create_app)
    html = plugin.template_html_sidebar_right_inject(page="SoloTarget")

    assert html is None
