#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import re
import pytest
import os
import otterwiki.gitstorage
from datetime import datetime
from flask.testing import FlaskClient

# Snapshot of app.config, captured the first time create_app runs (before any
# test has mutated it). app.config is a module-level singleton just like storage
# and db, so config a test sets leaks into the following tests unless it is
# restored. See create_app below.
_config_snapshot = None


class CSRFTestClient(FlaskClient):
    """Test client that automatically injects CSRF tokens."""

    def _get_csrf_token(self):
        response = super().get('/', follow_redirects=True)
        match = re.search(
            r'name="csrf-token" content="([^"]+)"',
            response.data.decode(),
        )
        return match.group(1) if match else None

    def post(self, *args, **kwargs):
        data = kwargs.get('data')
        if data is None:
            token = self._get_csrf_token()
            if token:
                kwargs['data'] = {'csrf_token': token}
        elif isinstance(data, dict) and 'csrf_token' not in data:
            token = self._get_csrf_token()
            if token:
                data['csrf_token'] = token
        return super().post(*args, **kwargs)


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
                "REPOSITORY = '{}'\n".format(str(_storage.path)),
                "SITE_NAME = 'TEST WIKI'\n",
                "DEBUG = True\n",  # enable test and debug settings
                "TESTING = True\n",
                "MAIL_SUPPRESS_SEND = True\n",
                "SECRET_KEY = 'Testing Testing Testing'\n",
            ]
        )
    # configure environment
    os.environ["OTTERWIKI_SETTINGS"] = settings_cfg
    # get app
    from otterwiki.server import app, db, mail, storage

    # app.config is a module-level singleton, so any config a test sets leaks
    # into the following tests. Capture a baseline snapshot the first time and
    # restore it for every test so each starts from the same configuration.
    global _config_snapshot
    if _config_snapshot is None:
        _config_snapshot = dict(app.config)
    else:
        app.config.clear()
        app.config.update(_config_snapshot)
    # keep REPOSITORY pointing at this test's repository
    app.config["REPOSITORY"] = _storage.path

    # otterwiki.server runs its setup once at import time, so app, db and
    # storage are module-level singletons shared by every test. Without a
    # reset the first test's repository and database leak into all the
    # following ones (untracked files, users, preferences, ...). Re-point the
    # shared objects at this test's fresh repository and database so each test
    # runs in isolation. All modules hold a reference to this same storage
    # object, so mutating it in place reaches every one of them.
    storage.path = _storage.path  # pyright: ignore
    storage.repo = _storage.repo  # pyright: ignore
    # give each test a clean database
    with app.app_context():
        db.drop_all()
        db.create_all()
    # a fresh repository is empty; recreate the initial home page just like a
    # real instance does on first start (see otterwiki/server.py)
    if (
        len(storage.list()[0]) < 1 and len(storage.log()) < 1
    ):  # pyright: ignore
        with open(os.path.join(app.root_path, "initial_home.md")) as f:
            storage.store(  # pyright: ignore
                filename="home.md",
                content=f.read(),
                author=("Otterwiki Robot", "noreply@otterwiki"),
                message="Initial commit",
            )

    # for debugging
    app._otterwiki_tempdir = storage.path  # pyright: ignore
    # for other tests
    app.storage = storage  # pyright: ignore
    # store mail in app for testing
    app.test_mail = mail  # pyright: ignore
    # enable test and debug settings
    app.config["TESTING"] = True
    app.config["DEBUG"] = True
    app.test_client_class = CSRFTestClient
    yield app
    # make sure GIT_REMOTE_*_ENABLED is false to avoid weird side effects
    app.config["GIT_REMOTE_PULL_ENABLED"] = False
    app.config["GIT_REMOTE_PUSH_ENABLED"] = False


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
