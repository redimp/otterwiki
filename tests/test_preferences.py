#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import os
import re
from datetime import datetime

def test_admin_form(app_with_user, admin_client):
    rv = admin_client.get("/-/admin")
    assert rv.status_code == 200

def test_preferences_testmail(app_with_user, admin_client):
    # workaround since MAIL_SUPPRESS_SEND doesn't work as expected
    app_with_user.test_mail.state.suppress = True
    # record outbox
    with app_with_user.test_mail.record_messages() as outbox:
        rv = admin_client.post(
                "/-/admin",
                data = {
                    "mail_recipient" : "",
                    "test_mail_preferences" : "true",
                },
                follow_redirects=True,
            )
        assert rv.status_code == 200
        assert len(outbox) == 1
        assert "test mail" in outbox[0].subject.lower()
        assert "mail@example.org" in outbox[0].recipients

    with app_with_user.test_mail.record_messages() as outbox:
        rv = admin_client.post(
                "/-/admin",
                data = {
                    "mail_recipient" : "mail2@example.org",
                    "test_mail_preferences" : "true",
                },
                follow_redirects=True,
            )
        assert rv.status_code == 200
        assert len(outbox) == 1
        assert "test mail" in outbox[0].subject.lower()
        assert "mail2@example.org" in outbox[0].recipients

    with app_with_user.test_mail.record_messages() as outbox:
        rv = admin_client.post(
                "/-/admin",
                data = {
                    "mail_recipient" : "example.org",
                    "test_mail_preferences" : "true",
                    },
                follow_redirects=True,
            )
        assert rv.status_code == 200
        html = rv.data.decode()
        assert "invalid email address" in html.lower()

def test_update_preferences(app_with_user, admin_client):
    new_name = "Test Wiki 4711"
    new_description = "another Test Wiki 4711"
    assert app_with_user.config['SITE_NAME'] != new_name
    assert app_with_user.config['SITE_DESCRIPTION'] != new_description
    rv = admin_client.post(
            "/-/admin",
            data = {
                "site_name" : new_name,
                "site_description" : new_description,
                "update_preferences" : "true",
            },
            follow_redirects=True,
        )
    assert rv.status_code == 200
    assert app_with_user.config['SITE_NAME'] == new_name
    assert app_with_user.config['SITE_DESCRIPTION'] == new_description
    assert app_with_user.config['SITE_LOGO'] == ""
    assert app_with_user.config['SITE_ICON'] == ""

def test_update_preferences_logo_and_icon(app_with_user, admin_client):
    new_logo = '/Home/a/logo.png'
    new_icon = '/Random/a/favicon.png'
    assert app_with_user.config['SITE_LOGO'] != new_logo
    assert app_with_user.config['SITE_ICON'] != new_icon
    rv = admin_client.post(
            "/-/admin",
            data = {
                "site_logo" : new_logo,
                "site_icon" : new_icon,
                "update_preferences" : "true",
            },
            follow_redirects=True,
        )
    assert rv.status_code == 200
    assert app_with_user.config['SITE_LOGO'] == new_logo
    assert app_with_user.config['SITE_ICON'] == new_icon
    # check html
    html = rv.data.decode()
    assert f"<link rel=\"icon\" href=\"{new_icon}\">" in html
    assert f"<img src=\"{new_logo}\" alt=\"\" id=\"site_logo\"/>" in html

def test_update_mail_preferences(app_with_user, admin_client):
    new_sender = "mail@example.com"
    new_server = "mail.example.com"
    new_port = "25"
    data = {
        "mail_sender" : new_sender,
        "mail_server" : new_server,
        "mail_port" : new_port,
        "update_mail_preferences" : "true",
    }
    assert app_with_user.config['MAIL_DEFAULT_SENDER'] != new_sender
    assert app_with_user.config['MAIL_SERVER'] != new_server
    rv = admin_client.post(
            "/-/admin",
            data = data,
            follow_redirects=True,
        )
    assert rv.status_code == 200
    assert app_with_user.config['MAIL_DEFAULT_SENDER'] == new_sender
    assert app_with_user.config['MAIL_SERVER'] == new_server
    assert app_with_user.config['MAIL_PORT'] != new_port
    assert app_with_user.config['MAIL_USE_TLS'] == False
    assert app_with_user.config['MAIL_USE_SSL'] == False
    # modify data to test tls/ssl settings
    data["mail_security"] = "tls"
    rv = admin_client.post(
            "/-/admin",
            data = data,
            follow_redirects=True,
        )
    assert app_with_user.config['MAIL_USE_TLS'] == True
    assert app_with_user.config['MAIL_USE_SSL'] == False
    # modify data to test tls/ssl settings
    data["mail_security"] = "ssl"
    rv = admin_client.post(
            "/-/admin",
            data = data,
            follow_redirects=True,
        )
    assert app_with_user.config['MAIL_USE_TLS'] == False
    assert app_with_user.config['MAIL_USE_SSL'] == True

def test_update_mail_preferences_errors(app_with_user, admin_client):
    wrong_sender = "mail.example.com"
    assert app_with_user.config['MAIL_DEFAULT_SENDER'] != wrong_sender
    wrong_port = "twentyfive"
    assert app_with_user.config['MAIL_PORT'] != wrong_port
    # post wrong values to the form
    rv = admin_client.post(
            "/-/admin",
            data = {
                "mail_sender" : wrong_sender,
                "mail_port" : wrong_port,
                "update_mail_preferences" : "true",
            },
            follow_redirects=True,
        )
    # check that the form was submitted
    assert rv.status_code == 200
    html = rv.data.decode()
    # check messages
    assert "is not a valid email address" in html.lower()
    # and that the setting was not applied
    assert app_with_user.config['MAIL_DEFAULT_SENDER'] != wrong_sender
    assert "mail port must be a valid port" in html.lower()
    assert app_with_user.config['MAIL_PORT'] != wrong_port

    # post empty values
    rv = admin_client.post(
            "/-/admin",
            data = {
                "update_mail_preferences" : "true",
            },
            follow_redirects=True,
        )
    # check that the form was submitted
    assert rv.status_code == 200
    html = rv.data.decode()
    # MAIL_PORT can be empty
    assert "mail port must be a valid port" not in html.lower()
    # check required values
    assert "is not a valid email address" in html.lower()
    assert "mail server must not be empty" in html.lower()

    # post wrong port
    rv = admin_client.post(
            "/-/admin",
            data = {
                "mail_port" : "1",
                "update_mail_preferences" : "true",
            },
            follow_redirects=True,
        )
    # check that the form was submitted
    assert rv.status_code == 200
    html = rv.data.decode()
    # MAIL_PORT can be empty
    assert "mail port must be a valid port" in html.lower()
