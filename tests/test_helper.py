#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import flask
import os
import contextlib
from test_otterwiki import create_app
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
