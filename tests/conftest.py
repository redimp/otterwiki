#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import os
import re
import otterwiki
import otterwiki.gitstorage
from flask import url_for
from datetime import datetime


@pytest.fixture
def create_app(tmpdir):
    tmpdir.mkdir("repo")
    storage = otterwiki.gitstorage.GitStorage(
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
    from otterwiki.server import app, mail
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
def db():
    from otterwiki.auth import db
    yield db


@pytest.fixture
def test_client(create_app):
    return create_app.test_client()


@pytest.fixture
def app_with_user(create_app, db):
    from otterwiki.auth import SimpleAuth, generate_password_hash

    # delete all users
    db.session.query(SimpleAuth.User).delete()
    db.session.commit()
    # create a user
    user = SimpleAuth.User(
        name="Test User",
        email="mail@example.org",
        password_hash=generate_password_hash("password1234", method="sha256"),
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        is_admin=True,
    )
    db.session.add(user)
    db.session.commit()
    yield create_app


@pytest.fixture
def create_app_with_user(app_with_user, db):
    yield app_with_user, db


@pytest.fixture
def req_ctx(create_app):
    with create_app.test_request_context() as ctx:
        yield ctx
