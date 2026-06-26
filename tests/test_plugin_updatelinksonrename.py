#!/usr/bin/env python

"""Tests for the plugin_updatelinksonrename example plugin.

The plugin rewrites WikiLinks that point to a page when the page is renamed
(https://github.com/redimp/otterwiki/discussions/210, issue #228).

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


def _setup_plugin(create_app):
    cls = _load_example_plugin(
        "plugin_updatelinksonrename",
        "otterwiki_updatelinksonrename.py",
        "UpdateLinksOnRename",
    )
    from otterwiki.server import db

    plugin = cls()
    plugin.setup(app=create_app, db=db, storage=create_app.storage)
    return plugin


def test_rewrites_wikilinks_on_rename(test_client, create_app):
    save_page(test_client, "RenameTarget", "# Target")
    # default WIKILINK_STYLE: the link is the right-hand side of [[title|link]]
    save_page(
        test_client,
        "Referrer",
        "A [[RenameTarget]] B [[click here|RenameTarget#sec]] "
        "C [[Unrelated]]",
    )

    plugin = _setup_plugin(create_app)
    pm = _get_plugin_manager()
    pm.register(plugin)
    try:
        rv = test_client.post(
            "/RenameTarget/rename",
            data={"new_pagename": "RenamedTarget", "message": "renaming"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
    finally:
        pm.unregister(plugin)

    content = create_app.storage.load("referrer.md", mode="r")
    # link target rewritten, anchor and explicit title preserved
    assert "[[RenamedTarget]]" in content
    assert "[[click here|RenamedTarget#sec]]" in content
    # the old target name is gone, the unrelated link is untouched
    assert "[[RenameTarget]]" not in content
    assert "RenameTarget#sec" not in content
    assert "[[Unrelated]]" in content


def test_can_be_disabled(test_client, create_app):
    save_page(test_client, "KeepTarget", "# Target")
    save_page(test_client, "KeepReferrer", "Link [[KeepTarget]]")

    plugin = _setup_plugin(create_app)
    create_app.config["UPDATE_LINKS_ON_RENAME"] = False
    pm = _get_plugin_manager()
    pm.register(plugin)
    try:
        rv = test_client.post(
            "/KeepTarget/rename",
            data={"new_pagename": "KeepRenamed", "message": "renaming"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
    finally:
        pm.unregister(plugin)
        create_app.config.pop("UPDATE_LINKS_ON_RENAME", None)

    content = create_app.storage.load("keepreferrer.md", mode="r")
    # disabled: the link must be left untouched
    assert "[[KeepTarget]]" in content
