#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""Tests for the template_folders plugin hook."""

import sys

import pytest
from flask import render_template

from otterwiki.plugins import hookimpl


def _get_plugin_manager():
    """Get the current plugin_manager, even after module reloads by other tests."""
    return sys.modules["otterwiki.plugins"].plugin_manager


class TemplatePlugin:
    """Test plugin that renders a page from its own template folder."""

    def __init__(self, folder):
        self.folder = folder

    @hookimpl
    def template_folders(self):
        return [str(self.folder)]

    @hookimpl
    def url_request(self, plugin, extra, method="GET", values=None):
        if plugin != "templatetest":
            return None
        return render_template("templatetest/{}.html".format(extra))


@pytest.fixture
def template_plugin(tmp_path):
    folder = tmp_path / "templates"
    (folder / "templatetest").mkdir(parents=True)
    (folder / "templatetest" / "plain.html").write_text(
        "plain plugin template"
    )
    (folder / "templatetest" / "extends.html").write_text(
        '{% extends "wiki.html" %}'
        "{% block content %}extended plugin template{% endblock %}"
    )
    # a template with the name of a core template must not override it
    (folder / "layout.html").write_text("plugin layout override")
    plugin = TemplatePlugin(folder)
    _get_plugin_manager().register(plugin)
    yield plugin
    _get_plugin_manager().unregister(plugin)


def test_render_plugin_template(template_plugin, test_client):
    rv = test_client.get("/-/plugin/templatetest/plain")
    assert rv.status_code == 200
    assert rv.data.decode() == "plain plugin template"


def test_plugin_template_extends_core_template(template_plugin, test_client):
    rv = test_client.get("/-/plugin/templatetest/extends")
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "extended plugin template" in html
    # the core layout.html is used via wiki.html, not the one of the plugin
    assert "plugin layout override" not in html
    assert 'id="site_logo"' in html


def test_core_templates_are_not_overridden(template_plugin, test_client):
    html = test_client.get("/").data.decode()
    assert "plugin layout override" not in html
