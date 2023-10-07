#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import flask
import os
import contextlib
import otterwiki
import otterwiki.gitstorage


@pytest.fixture
def test_client(create_app):
    return create_app.test_client()


@pytest.fixture
def req_ctx(create_app):
    with create_app.test_request_context() as ctx:
        yield ctx


def test_toast(create_app, req_ctx, test_client):
    test_string = "aa bb cc dd"
    from otterwiki.helper import toast

    assert not flask.session.modified
    # test toast
    toast(test_string)
    assert flask.session.modified
    assert list(flask.get_flashed_messages()) == [test_string]


def test_toast_session(create_app, req_ctx, test_client):
    test_string = "aa bb cc dd"
    from otterwiki.helper import toast
    from flask import session

    html = test_client.get("/").data.decode()
    assert "<!DOCTYPE html>" in html
    assert test_string not in html
    # test toast
    toast(test_string)
    assert test_string in [x[1] for x in session["_flashes"]]
    toast(test_string, "non-existing-category")
    assert ("alert-primary", test_string) in session["_flashes"]


def test_serializer(create_app, req_ctx):
    s = "Hello World"
    from otterwiki.helper import serialize, deserialize, SerializeError

    assert s == deserialize(serialize(s))
    # check max_age
    with pytest.raises(SerializeError):
        deserialize(serialize(s), max_age=-1)
    # check salt
    with pytest.raises(SerializeError):
        deserialize(serialize(s), salt=s)

def test_health_check_ok(create_app, req_ctx):
    from otterwiki.helper import health_check

    healthy, messages = health_check()
    assert healthy is True
    assert messages == ["ok"]

def test_health_check_error_storage(create_app, req_ctx, tmpdir):
    from otterwiki.helper import health_check
    from otterwiki.gitstorage import GitStorage
    # update the Storage object with a storage on a not initialized directory
    _working_dir = create_app.storage.repo.git._working_dir
    create_app.storage.repo.git._working_dir = str(tmpdir.mkdir("test_health_check_error_storage"))

    healthy, messages = health_check()
    assert healthy is False
    assert True in [m.startswith("StorageError") for m in messages]
    # restore _working_dir FIXME: no idea why the pytest fixture doesn't work in scope=session
    create_app.storage.repo.git._working_dir = _working_dir

def test_health_check_error_storage(create_app, req_ctx, tmpdir):
    from otterwiki.helper import health_check
    from otterwiki.gitstorage import GitStorage
    # update the Storage object with a storage on a not initialized directory
    _working_dir = create_app.storage.repo.git._working_dir
    create_app.storage.repo.git._working_dir = str(tmpdir.mkdir("test_health_check_error_storage"))

    healthy, messages = health_check()
    assert healthy is False
    assert True in [m.startswith("StorageError") for m in messages]
    # restore _working_dir
    create_app.storage.repo.git._working_dir = _working_dir

def test_auto_url(create_app, req_ctx):
    name, path = otterwiki.helper.auto_url("home.md")
    assert name == "Home"
    assert path == "/Home"
    name, path = otterwiki.helper.auto_url("subspace/example.md")
    assert name == "Subspace/Example"
    assert path == "/Subspace/Example"
    name, path = otterwiki.helper.auto_url("page/example.mp4")
    assert name == "page/example.mp4"
    assert path == "/Page/a/example.mp4"
