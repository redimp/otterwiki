#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""Tests for the navbar and admin menu template plugin hooks."""

import sys

import pytest

from otterwiki.plugins import hookimpl


def _get_plugin_manager():
    """Get the current plugin_manager, even after module reloads by other tests."""
    return sys.modules["otterwiki.plugins"].plugin_manager


class NavbarPlugin:
    """Test plugin that injects markers via the template hooks."""

    @hookimpl
    def template_html_navbar_inject(self, page):
        return '<span id="navbar-marker"></span>'

    @hookimpl
    def template_html_navbar_dropdown_inject(self, page):
        return '<span id="dropdown-marker"></span>'

    @hookimpl
    def template_html_admin_menu_inject(self):
        return '<span id="admin-menu-marker"></span>'


@pytest.fixture
def navbar_plugin():
    plugin = NavbarPlugin()
    _get_plugin_manager().register(plugin)
    yield plugin
    _get_plugin_manager().unregister(plugin)


def test_navbar_inject(navbar_plugin, test_client):
    html = test_client.get("/").data.decode()
    assert '<span id="navbar-marker"></span>' in html
    assert '<span id="dropdown-marker"></span>' in html
    # the plugin content is placed at the top of the dropdown menu
    assert html.index('id="dropdown-marker"') < html.index(
        'fa-question-circle'
    )


def test_admin_menu_inject(navbar_plugin, admin_client):
    html = admin_client.get("/-/admin").data.decode()
    assert '<span id="admin-menu-marker"></span>' in html


def test_admin_menu_inject_not_for_users(navbar_plugin, other_client):
    html = other_client.get("/-/settings").data.decode()
    assert "admin-menu-marker" not in html


def test_no_inject_without_plugin(test_client):
    rv = test_client.get("/")
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "navbar-marker" not in html
    assert "dropdown-marker" not in html
