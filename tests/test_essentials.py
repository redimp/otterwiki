#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest


def test_robots(test_client):
    response = test_client.get("/robots.txt")
    assert response.status_code == 200
    assert "User-agent: *\nAllow: /" in response.data.decode()


def test_favicon(test_client):
    response = test_client.get("/favicon.ico")
    assert response.status_code == 200


def test_about(test_client):
    response = test_client.get("/-/about")
    assert response.status_code == 200
    assert "markdown" in response.data.decode().lower()


def test_fatal_error():
    from otterwiki import fatal_error

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fatal_error("test_fatal_error")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
