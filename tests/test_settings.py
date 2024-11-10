#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import os
import re
import otterwiki
from pprint import pprint


def test_settings_update_name(app_with_user, test_client):
    rv = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "password1234",
        },
        follow_redirects=True,
    )
    assert 200 == rv.status_code

    # check name
    rv = test_client.get("/-/settings")
    assert 200 == rv.status_code
    assert (
        '<input name="name" type="text" class="form-control" id="name" value="Test User"'
        in rv.data.decode()
    )

    # update name
    rv = test_client.post(
        "/-/settings",
        data={
            "name": "Updated Name",
        },
        follow_redirects=True,
    )
    assert (
        '<input name="name" type="text" class="form-control" id="name" value="Updated Name"'
        in rv.data.decode()
    )
    assert 'Your name was updated successfully' in rv.data.decode()
    # restore name
    rv = test_client.post(
        "/-/settings",
        data={
            "name": "Test User",
        },
        follow_redirects=True,
    )
    assert 200 == rv.status_code
    assert (
        '<input name="name" type="text" class="form-control" id="name" value="Test User"'
        in rv.data.decode()
    )


def test_settings_update_name_failed(app_with_user, test_client):
    rv = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "password1234",
        },
        follow_redirects=True,
    )
    assert 200 == rv.status_code

    # check name
    rv = test_client.get("/-/settings")
    assert 200 == rv.status_code
    assert (
        '<input name="name" type="text" class="form-control" id="name" value="Test User"'
        in rv.data.decode()
    )

    # update name
    rv = test_client.post(
        "/-/settings",
        data={
            "name": "",
        },
        follow_redirects=True,
    )
    assert (
        '<input name="name" type="text" class="form-control" id="name" value="Test User"'
        in rv.data.decode()
    )
    assert 'Your name must be at least one character.' in rv.data.decode()


def test_settings_change_password(app_with_user, test_client):
    rv = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "password1234",
        },
        follow_redirects=True,
    )
    assert 200 == rv.status_code
    # update password
    rv = test_client.post(
        "/-/settings",
        data={
            "password1": "changedpassword",
            "password2": "changedpassword",
        },
        follow_redirects=True,
    )
    assert 200 == rv.status_code
    assert 'Your password was updated successfully.' in rv.data.decode()
    # change password back
    rv = test_client.post(
        "/-/settings",
        data={
            "password1": "password1234",
            "password2": "password1234",
        },
        follow_redirects=True,
    )
    assert 200 == rv.status_code
    assert 'Your password was updated successfully.' in rv.data.decode()
    # fail to change the password
    rv = test_client.post(
        "/-/settings",
        data={
            "password1": "1234",
            "password2": "1234",
        },
        follow_redirects=True,
    )
    assert 200 == rv.status_code
    assert (
        'The password must be at least 8 characters long.' in rv.data.decode()
    )
