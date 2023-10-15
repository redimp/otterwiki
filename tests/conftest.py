#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import os
import re
import otterwiki.gitstorage
from datetime import datetime


@pytest.fixture
def create_app(tmpdir):
    tmpdir.mkdir("repo")
    _storage = otterwiki.gitstorage.GitStorage(
        path=str(tmpdir.join("repo")), initialize=True
    )
    settings_cfg = str(tmpdir.join("settings.cfg"))
    # write config file
    with open(settings_cfg, "w") as f:
        f.writelines(
            [
                "REPOSITORY = '{}'\n".format(str(tmpdir.join("repo"))),
                "SITE_NAME = 'TEST WIKI'\n",
                "DEBUG = True\n", # enable test and debug settings
                "TESTING = True\n",
                "MAIL_SUPPRESS_SEND = True\n",
            ]
        )
    # configure environment
    os.environ["OTTERWIKI_SETTINGS"] = settings_cfg
    # get app
    from otterwiki.server import app, db, mail, storage
    # for debugging
    app._otterwiki_tempdir = storage.path
    # for other tests
    app.storage = storage
    # store mail in app for testing
    app.test_mail = mail
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

    # delete all users
    db.session.query(SimpleAuth.User).delete()
    db.session.commit()
    # create a user
    user = SimpleAuth.User(
        name="Test User",
        email="mail@example.org",
        password_hash=generate_password_hash("password1234", method="scrypt"),
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        is_admin=True,
    )
    db.session.add(user)

    # create a non admin user
    user = SimpleAuth.User(
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
