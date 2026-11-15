#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
Tests for the userinfo plugin example. The plugin is loaded straight from
its file via the example_plugin_loader fixture, it does not need to be
installed.
"""

import hashlib

import pytest

SETTINGS_URL = "/-/admin/plugin/userinfo/settings"


def delete_preferences(app):
    from otterwiki.server import db, Preferences

    with app.app_context():
        Preferences.query.filter(
            Preferences.name.startswith("PLUGIN_USERINFO_")
        ).delete()
        db.session.commit()


@pytest.fixture
def plugin(create_app, example_plugin_loader):
    from otterwiki.server import db

    _, plugins = example_plugin_loader("plugin_userinfo")
    (plugin,) = plugins
    plugin.setup(app=create_app, db=db, storage=create_app.storage)
    delete_preferences(create_app)
    yield plugin
    delete_preferences(create_app)


def save_settings(client, **values):
    rv = client.post(SETTINGS_URL, data=values, follow_redirects=True)
    assert rv.status_code == 200
    return rv.data.decode()


def test_anonymous_user(plugin, test_client):
    html = test_client.get("/").data.decode()
    assert "userinfo-navbar" not in html
    assert "Logged in as" not in html


def test_user_in_navbar_and_dropdown(plugin, other_client):
    html = other_client.get("/").data.decode()
    assert "userinfo-navbar" in html
    assert (
        '<span class="userinfo-text d-none d-sm-inline">Another User</span>'
        in html
    )
    assert "Logged in as<br><strong>Another User</strong>" in html
    assert "another@user.org" in html
    assert "fa-user-shield" not in html
    assert "gravatar.com" not in html


def test_admin_marker_and_menu(plugin, admin_client):
    html = admin_client.get("/").data.decode()
    assert "userinfo-admin" in html
    html = admin_client.get("/-/admin").data.decode()
    assert 'href="{}"'.format(SETTINGS_URL) in html


def test_admin_page(plugin, admin_client):
    rv = admin_client.get(SETTINGS_URL)
    assert rv.status_code == 200
    html = rv.data.decode()
    assert '<h2 class="card-title">User Info</h2>' in html
    assert 'name="display"' in html


def test_admin_page_forbidden_for_users(plugin, other_client):
    assert other_client.get(SETTINGS_URL).status_code == 403
    rv = other_client.post(SETTINGS_URL, data={"display": "email"})
    assert rv.status_code == 403


def test_save_settings(plugin, admin_client):
    html = save_settings(
        admin_client,
        display="email",
        gravatar="True",
        gravatar_default="identicon",
    )
    assert "Preferences saved." in html
    html = admin_client.get("/").data.decode()
    assert (
        '<span class="userinfo-text d-none d-sm-inline">mail@example.org</span>'
        in html
    )
    digest = hashlib.sha256(b"mail@example.org").hexdigest()
    assert (
        'src="https://gravatar.com/avatar/{}?s=48&amp;d=identicon"'.format(
            digest
        )
        in html
    )
    # show_admin was not sent, so the admin marker is disabled
    assert "userinfo-admin" not in html


def test_save_settings_initial(plugin, admin_client):
    save_settings(admin_client, display="initial", show_admin="True")
    html = admin_client.get("/").data.decode()
    assert '<span class="userinfo-initials">T</span>' in html
    assert "userinfo-text" not in html
    assert "userinfo-admin" in html


def test_save_settings_initials(plugin, admin_client):
    save_settings(admin_client, display="initials", show_admin="True")
    html = admin_client.get("/").data.decode()
    assert '<span class="userinfo-initials">TU</span>' in html


def test_gravatar_and_initials(plugin, admin_client):
    save_settings(admin_client, display="initials", gravatar="True")
    html = admin_client.get("/").data.decode()
    assert 'class="userinfo-avatar"' in html
    assert '<span class="userinfo-initials">TU</span>' in html


@pytest.mark.parametrize(
    "name, initials",
    [
        ("Test User", "TU"),
        ("Ada King Lovelace", "AL"),
        ("  ada   lovelace ", "AL"),
        ("john.doe", "JD"),
        ("jane_doe-smith", "JS"),
        ("Otter", "O"),
        ("", ""),
        ("...", ""),
    ],
)
def test_initials(plugin, name, initials):
    assert plugin.initials(name) == initials


def test_invalid_settings_are_rejected(plugin, admin_client):
    save_settings(admin_client, display="email", show_admin="True")
    save_settings(
        admin_client,
        display="<script>",
        gravatar="True",
        gravatar_default="<script>",
        show_admin="True",
    )
    # the invalid values are ignored, the previous values are kept
    html = admin_client.get("/").data.decode()
    assert (
        '<span class="userinfo-text d-none d-sm-inline">mail@example.org</span>'
        in html
    )
    assert "d=mp" in html


def test_user_name_is_escaped(plugin, app_with_user, other_client):
    from otterwiki.auth import SimpleAuth, db

    user = SimpleAuth.User.query.filter_by(email="another@user.org").first()
    user.name = "<b>Evil</b>"
    db.session.commit()
    try:
        html = other_client.get("/").data.decode()
        assert "<b>Evil</b>" not in html
        assert "&lt;b&gt;Evil&lt;/b&gt;" in html
    finally:
        user.name = "Another User"
        db.session.commit()


def test_help(plugin, test_client):
    html = test_client.get("/-/help/plugins").data.decode()
    assert "User Info" in html
    assert "Displays the logged-in user in the navbar. Depending" in html
