#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import os
import otterwiki.gitstorage
from datetime import datetime

from fakeldap import MockLDAP
import ldap


DIRECTORY = {
    # bind user first
    "cn=manager,dc=ldap,dc=org": {"userPassword": ["admin123"]},
    "cn=user directory,dc=ldap,dc=org": {
        "mail": ["user@ldap.org"],
        "objectClass": ["person"],
        "userPassword": ["12345678"],
        "cn": [b"User Ldap"],
    },
    "cn=staff directory,dc=ldap,dc=org": {
        "mail": ["staff@ldap.org"],
        "objectClass": ["person"],
        "userPassword": ["password"],
        "cn": [b"Staff Ldap"],
    },
}


@pytest.fixture
def create_app(tmpdir):
    tmpdir.mkdir("repo")
    _storage = otterwiki.gitstorage.GitStorage(
        path=str(tmpdir.join("repo")), initialize=True
    )
    settings_cfg = str(tmpdir.join("settings.cfg"))
    ldap_user = list(DIRECTORY.keys())[0]
    ldap_pass = DIRECTORY[ldap_user]["userPassword"][0]
    ldap_base = ldap_user.split(",", 1)[-1]
    ldap_domain = ldap_base.replace("dc=", "").replace(",", ".")
    # write config file
    with open(settings_cfg, "w") as f:
        f.writelines(
            [
                "REPOSITORY = '{}'\n".format(str(_storage.path)),
                "SITE_NAME = 'TEST WIKI'\n",
                "DEBUG = True\n",  # enable test and debug settings
                "TESTING = True\n",
                "MAIL_SUPPRESS_SEND = True\n",
                "SECRET_KEY = 'Testing Testing Testing'\n",
                "LDAP_URI = 'ldap://localhost:389'\n",
                "LDAP_USERNAME = '{}'\n".format(ldap_user),
                "LDAP_PASSWORD = '{}'\n".format(ldap_pass),
                "LDAP_BASE = '{}'\n".format(ldap_base),
                "LDAP_SCOPE = 'onelevel'\n",
                "LDAP_DOMAIN = '{}'\n".format(ldap_domain),
            ]
        )
    # configure environment
    os.environ["OTTERWIKI_SETTINGS"] = settings_cfg
    # get app
    from otterwiki.server import app, db, mail, storage

    # for debugging
    app._otterwiki_tempdir = storage.path  # pyright: ignore
    # for other tests
    app.storage = storage  # pyright: ignore
    # store mail in app for testing
    app.test_mail = mail  # pyright: ignore
    # enable test and debug settings
    app.config["TESTING"] = True
    app.config["DEBUG"] = True
    yield app


@pytest.fixture
def test_client(create_app):
    client = create_app.test_client()
    return client


@pytest.fixture
def req_ctx(create_app):
    with create_app.test_request_context() as ctx:
        yield ctx


@pytest.fixture
def app_with_user(create_app, req_ctx):
    from otterwiki.auth import SimpleAuth, generate_password_hash, db

    mock = MockLDAP(DIRECTORY)
    ldap.initialize = mock.initialize

    # delete all users
    db.session.query(SimpleAuth.User).delete()
    db.session.commit()
    # create a user
    user = SimpleAuth.User(  # pyright: ignore
        name="Test User",
        email="mail@example.org",
        password_hash=generate_password_hash("password1234", method="scrypt"),
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        is_admin=True,
    )
    db.session.add(user)

    # create a non admin user
    user = SimpleAuth.User(  # pyright: ignore
        name="Another User",
        email="another@user.org",
        password_hash=generate_password_hash("password4567", method="scrypt"),
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        is_admin=False,
        is_approved=True,
        email_confirmed=True,
    )
    db.session.add(user)

    # create a ldap user
    user = SimpleAuth.User(  # pyright: ignore
        name="Directory User",
        email="user@ldap.org",
        password_hash="",
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        is_admin=False,
        is_approved=True,
        email_confirmed=True,
        provider="ldap",
    )
    db.session.add(user)
    db.session.commit()
    yield create_app


@pytest.fixture(scope="function")
def admin_client(app_with_user):
    client = app_with_user.test_client()
    result = client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "password1234",
        },
        follow_redirects=True,
    )
    html = result.data.decode()
    assert "You logged in successfully." in html
    return client


@pytest.fixture(scope="function")
def other_client(app_with_user):
    client = app_with_user.test_client()
    result = client.post(
        "/-/login",
        data={
            "email": "another@user.org",
            "password": "password4567",
        },
        follow_redirects=True,
    )
    html = result.data.decode()
    assert "You logged in successfully." in html
    return client
