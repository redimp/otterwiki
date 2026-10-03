#!/usr/bin/env python

"""Tests for the url_request and url_admin_request plugin hooks."""

import sys

from otterwiki.plugins import hookimpl


def _get_plugin_manager():
    """Get the current plugin_manager, even after module reloads by other tests."""
    return sys.modules["otterwiki.plugins"].plugin_manager


class EchoPlugin:
    """Test plugin that echoes the request values it receives."""

    @hookimpl
    def url_request(self, plugin, extra, method="GET", values=None):
        if plugin != "echo":
            return None
        return "url_request {} {} foo={}".format(
            method, extra, values.get("foo")
        )

    @hookimpl
    def url_admin_request(self, plugin, extra, method="GET", values=None):
        if plugin != "echo":
            return None
        return "url_admin_request {} {} foo={}".format(
            method, extra, values.get("foo")
        )


def make_echo_plugin():
    plugin = EchoPlugin()
    _get_plugin_manager().register(plugin)
    return plugin


def test_url_request_receives_values(test_client):
    plugin = make_echo_plugin()
    try:
        rv = test_client.get("/-/plugin/echo/action?foo=bar")
        assert rv.status_code == 200
        assert rv.data.decode() == "url_request GET action foo=bar"
    finally:
        _get_plugin_manager().unregister(plugin)


def test_url_admin_request_receives_values(admin_client):
    plugin = make_echo_plugin()
    try:
        rv = admin_client.get("/-/admin/plugin/echo/action?foo=bar")
        assert rv.status_code == 200
        assert rv.data.decode() == "url_admin_request GET action foo=bar"
    finally:
        _get_plugin_manager().unregister(plugin)


def test_url_request_receives_post_method(test_client):
    plugin = make_echo_plugin()
    try:
        rv = test_client.post("/-/plugin/echo/action", data={"foo": "bar"})
        assert rv.status_code == 200
        assert rv.data.decode() == "url_request POST action foo=bar"
    finally:
        _get_plugin_manager().unregister(plugin)


def test_url_admin_request_receives_post_method(admin_client):
    plugin = make_echo_plugin()
    try:
        rv = admin_client.post(
            "/-/admin/plugin/echo/action", data={"foo": "bar"}
        )
        assert rv.status_code == 200
        assert rv.data.decode() == "url_admin_request POST action foo=bar"
    finally:
        _get_plugin_manager().unregister(plugin)


def test_url_admin_request_requires_admin(test_client):
    plugin = make_echo_plugin()
    try:
        rv = test_client.get("/-/admin/plugin/echo/action?foo=bar")
        assert rv.status_code == 403
    finally:
        _get_plugin_manager().unregister(plugin)
