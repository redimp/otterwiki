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
            ]
        )
    # configure environment
    os.environ["OTTERWIKI_SETTINGS"] = settings_cfg
    # get app
    from otterwiki.server import app

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


def test_create_app_with_user(app_with_user):
    test_client = app_with_user.test_client()
    result = test_client.get("/")
    assert "<!DOCTYPE html>" in result.data.decode()
    assert "<title>" in result.data.decode()
    assert "</html>" in result.data.decode()


def test_db(app_with_user, db):
    from otterwiki.auth import SimpleAuth, check_password_hash

    # check that table 'user' exists
    from sqlalchemy import inspect

    inspector = inspect(db.engine)
    assert "user" in [str(x) for x in inspector.get_table_names()]

    # query all user
    all_user = SimpleAuth.User.query.all()
    assert len(all_user) == 1

    # query created user
    user = SimpleAuth.User.query.filter_by(email="mail@example.org").first()
    assert user.email == "mail@example.org"
    assert user.name == "Test User"
    # check hash
    assert True is check_password_hash(user.password_hash, "password1234")


def test_generate_and_check_hash(create_app):
    from otterwiki.auth import generate_password_hash, check_password_hash

    for password in ["abc123.!äüöß", "aedaiPaesh8ie5Iu", "┳━┳ ヽ(ಠل͜ಠ)ﾉ"]:
        for method in ["sha256", "sha512"]:
            hash = generate_password_hash(password, method=method)
            assert True is check_password_hash(hash, password)


def test_minimal_auth(app_with_user):
    # check auth defaults
    assert app_with_user.config.get("AUTH_METHOD") == ""


def login(client):
    return client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "password1234",
        },
        follow_redirects=True,
    )


def test_login(app_with_user, test_client):
    result = login(test_client)
    html = result.data.decode()
    assert "You logged in successfully." in html


def test_login_fail_without_app(test_client):
    html = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "",
        },
        follow_redirects=True,
    ).data.decode()
    assert "Invalid email address or password." in html


def test_login_fail_wrong_username(app_with_user, test_client):
    html = test_client.post(
        "/-/login",
        data={
            "email": "x@x.x",
            "password": "",
        },
        follow_redirects=True,
    ).data.decode()
    assert "Invalid email address or password." in html


def test_login_fail_wrong_password(app_with_user, test_client):
    html = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "xxx",
        },
        follow_redirects=True,
    ).data.decode()
    assert "Invalid email address or password." in html


def test_logout(test_client):
    result = login(test_client)
    html = test_client.get(
        "/-/logout",
        follow_redirects=True,
    ).data.decode()
    assert "You logged out successfully." in html


def test_login_required(test_client):
    html = test_client.get(
        "/-/settings",
        follow_redirects=True,
    ).data.decode()
    assert "Change Password" not in html
    assert "Please log in to access this page." in html


def test_settins_minimal(app_with_user, test_client):
    result = login(test_client)
    html = test_client.get(
        "/-/settings",
        follow_redirects=True,
    ).data.decode()
    assert "Change Password" in html


#
# test permissions
#
@pytest.fixture
def app_with_permissions(app_with_user, test_client):
    app_with_user.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_user.config["WRITE_ACCESS"] = "ANONYMOUS"
    # create a Home
    html = test_client.post(
        "/Home/save",
        data={
            "content_update": "There is no place like Home.",
            "commit": "Home: initial test commit.",
        },
        follow_redirects=True,
    ).data.decode()
    html = test_client.get("/Home").data.decode()
    assert "There is no place like Home." in html
    # update permissions
    app_with_user.config["READ_ACCESS"] = "REGISTERED"
    # and fetch again
    html = test_client.get("/Home").data.decode()
    assert "There is no place like Home." not in html

    with app_with_user.test_request_context() as ctx:
        yield app_with_user


def test_page_view_permissions(app_with_permissions, test_client):
    fun = "view"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun, path="Home"))
    assert "There is no place like Home." in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun, path="Home"), follow_redirects=True)
    assert "There is no place like Home." not in rv.data.decode()
    # check for the toast
    assert "lack the permissions to access" in rv.data.decode()
    # check for the login form
    assert url_for("login") in rv.data.decode()
    assert 'name="password"' in rv.data.decode()
    assert rv.status_code == 200
    login(test_client)
    rv = test_client.get(url_for(fun, path="Home"))
    assert "There is no place like Home." in rv.data.decode()
    assert rv.status_code == 200


def test_page_blame_permissions(app_with_permissions, test_client):
    fun = "blame"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "There is no place like Home." in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 403
    assert "There is no place like Home." not in rv.data.decode()
    login(test_client)
    rv = test_client.get(url_for(fun, path="Home"))
    assert "There is no place like Home." in rv.data.decode()


def test_page_history_permissions(app_with_permissions, test_client):
    fun = "history"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "initial test commit" in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 403
    assert "initial test commit" not in rv.data.decode()
    login(test_client)
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "initial test commit" in rv.data.decode()


def test_page_index_permissions(app_with_permissions, test_client):
    fun = "pageindex"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun))
    assert rv.status_code == 200
    assert "Page Index" in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun))
    assert rv.status_code == 403
    assert "Page Index" not in rv.data.decode()
    login(test_client)
    rv = test_client.get(url_for(fun))
    assert rv.status_code == 200
    assert "Page Index" in rv.data.decode()


def test_page_changelog_permissions(app_with_permissions, test_client):
    fun = "changelog"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "initial test commit" in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 403
    assert "initial test commit" not in rv.data.decode()
    login(test_client)
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "initial test commit" in rv.data.decode()


def test_page_edit_permissions(app_with_permissions, test_client):
    # update permissions
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_permissions.config["WRITE_ACCESS"] = "ANONYMOUS"
    # helper
    pagename = "RandomEdit"
    # try to edit anonymous
    rv = test_client.get(url_for("edit", path=pagename))
    assert rv.status_code == 200
    html = rv.data.decode()
    # check that there is an editor in the html
    assert 'action="/{}/preview"'.format(pagename) in html
    assert "<textarea" in html
    # update permissions
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    app_with_permissions.config["WRITE_ACCESS"] = "REGISTERED"
    # try edit
    rv = test_client.get(url_for("edit", path=pagename))
    html = rv.data.decode()
    # check that there is an editor in the html
    assert rv.status_code == 403
    assert 'action="/{}/preview"'.format(pagename) not in html
    assert "<textarea" not in html
    # login
    login(test_client)
    # try edit
    rv = test_client.get(url_for("edit", path=pagename))
    html = rv.data.decode()
    assert rv.status_code == 200
    assert 'action="/{}/preview"'.format(pagename) in html
    assert "<textarea" in html


def test_page_save_permissions(app_with_permissions, test_client):
    # update permissions
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_permissions.config["WRITE_ACCESS"] = "ANONYMOUS"
    # helper
    pagename = "RandomSaveTest"
    content = "Random Content"
    # try to edit anonymous
    rv = test_client.post(
        url_for("save", path=pagename),
        data={
            "content_update": content,
            "commit": "Home: initial test commit.",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert content in rv.data.decode()
    # change permissions
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    app_with_permissions.config["WRITE_ACCESS"] = "REGISTERED"
    # try to edit anonymous (and fail)
    rv = test_client.post(
        url_for("save", path=pagename),
        data={
            "content_update": content,
            "commit": "Home: initial test commit.",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 403
    # try to create (and fail)
    rv = test_client.post("/-/create", data={"pagename": "example"})
    assert rv.status_code == 403


def test_page_revert_permissions(app_with_permissions, test_client):
    # update permissions
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_permissions.config["WRITE_ACCESS"] = "ANONYMOUS"
    # helper
    pagename = "Random Revert Test 0"
    old_content = "Random Content 0"
    # try to edit anonymous
    rv = test_client.post(
        url_for("save", path=pagename),
        data={
            "content_update": old_content,
            "commit": "initial test commit.",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert old_content in rv.data.decode()
    # test view
    html = test_client.get("/{}/view".format(pagename)).data.decode()
    assert old_content in html
    # update content
    content = "Random Content 1"
    rv = test_client.post(
        url_for("save", path=pagename),
        data={
            "content_update": content,
            "commit": "updated content.",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert content in rv.data.decode()

    # find revision
    rv = test_client.get("/{}/history".format(pagename))
    html = rv.data.decode()
    revisions = re.findall(r"class=\"btn revision-small\">([A-z0-9]+)</a>", html)
    assert len(revisions) == 2
    latest_revision = revisions[0]

    # change permissions
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    app_with_permissions.config["WRITE_ACCESS"] = "REGISTERED"

    # try to revert non existing commit
    rv = test_client.get("/-/revert/{}".format(0000000))
    assert rv.status_code == 403

    # try revert form
    rv = test_client.get("/-/revert/{}".format(latest_revision))
    assert rv.status_code == 403
    # try to revert latest commit
    rv = test_client.post("/-/revert/{}".format(latest_revision))
    assert rv.status_code == 403

    # change permissions again
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_permissions.config["WRITE_ACCESS"] = "ANONYMOUS"

    # check revert form
    rv = test_client.get("/-/revert/{}".format(latest_revision))
    html = rv.data.decode()
    assert rv.status_code == 200
    assert "Revert commit [{}]".format(latest_revision) in html

    # try to revert latest commit
    rv = test_client.post("/-/revert/{}".format(latest_revision), follow_redirects=True)
    assert rv.status_code == 200

    # check if content changed
    html = test_client.get("/{}/view".format(pagename)).data.decode()
    assert old_content in html


#     # try to edit anonymous (and fail)
#     rv = test_client.post( url_for('save', path=pagename),
#             data={
#                 'content_update' : content,
#                 'commit' : 'Home: initial test commit.',
#                 },
#             follow_redirects=True,
#         )
#     assert rv.status_code == 403


#
# lost_password
#


def test_lost_password_form(test_client):
    rv = test_client.get("/-/lost_password")
    assert rv.status_code == 200
