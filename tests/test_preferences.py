#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import os
import re
import otterwiki
from datetime import datetime
from flask import url_for

@pytest.fixture
def admin_client(app_with_user, test_client):
    result = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "password1234",
        },
        follow_redirects=True,
    )
    html = result.data.decode()
    assert "You logged in successfully." in html
    yield test_client

def test_preference_form(app_with_user, admin_client, req_ctx):
    rv = admin_client.get(url_for("settings"))
    assert rv.status_code == 200

def test_preferences_testmail(app_with_user, admin_client, req_ctx):
    # workaround since MAIL_SUPPRESS_SEND doesn't work as expected
    app_with_user.test_mail.state.suppress = True
    # record outbox
    with app_with_user.test_mail.record_messages() as outbox:
        rv = admin_client.post(
                url_for("preferences"),
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
                url_for("preferences"),
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
                url_for("preferences"),
                data = {
                    "mail_recipient" : "example.org",
                    "test_mail_preferences" : "true",
                    },
                follow_redirects=True,
            )
        assert rv.status_code == 200
        html = rv.data.decode()
        assert "invalid email address" in html.lower()

def test_update_preferences(app_with_user, admin_client, req_ctx):
    new_name = "Test Wiki 4711"
    assert app_with_user.config['SITE_NAME'] != new_name
    rv = admin_client.post(
            url_for("preferences"),
            data = {
                "site_name" : new_name,
                "update_preferences" : "true",
            },
            follow_redirects=True,
        )
    assert rv.status_code == 200
    assert app_with_user.config['SITE_NAME'] == new_name
    assert app_with_user.config['SITE_LOGO'] == ""
