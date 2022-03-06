#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import base64
import otterwiki.gitstorage
from test_otterwiki import create_app


@pytest.fixture
def app_with_attachments(create_app):
    storage = otterwiki.gitstorage.GitStorage(
        path=create_app._otterwiki_tempdir, initialize=True
    )
    # create test page
    message = "Test.md commit"
    filename = "test.md"
    author = ("Example Author", "mail@example.com")
    # create attachment
    assert True == create_app.storage.store(
        "test.md", content="# Test\nAttachment Test.", author=author, message=message
    )
    # create txt attachment
    message = "Test/attachment0.txt attach0-commit"
    assert True == create_app.storage.store(
        "test/attachment0.txt",
        content="attachment0-content0",
        author=author,
        message=message,
    )
    # create gif attachment
    message = "Test/attachment1.gif attach1-commit"
    content_b64 = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
    assert True == create_app.storage.store(
        "test/attachment1.gif",
        content=base64.b64decode(content_b64),
        author=author,
        message=message,
        mode="wb",
    )
    yield create_app


@pytest.fixture
def test_client(app_with_attachments):
    yield app_with_attachments.test_client()


def test_app_with_attachments(test_client):
    response = test_client.get("/Test/view")
    assert response.status_code == 200


def test_list_attachments(test_client):
    response = test_client.get("/Test/attachments")
    assert response.status_code == 200
    assert "attachment0.txt" in response.data.decode()


def test_get_attachment0(test_client):
    response = test_client.get("/Test/a/attachment0.txt")
    assert response.status_code == 200
    assert "attachment0-content0" in response.data.decode()


def test_edit_attachment0(test_client):
    response = test_client.get("/Test/attachment/attachment0.txt")
    assert response.status_code == 200
    assert "attach0-commit" in response.data.decode()


def test_thumbnail(test_client):
    response = test_client.get("/Test/attachment/attachment1.gif")
    assert response.status_code == 200
    assert "attach1-commit" in response.data.decode()
    # test download
    response = test_client.get("/Test/a/attachment1.gif")
    assert response.status_code == 200
    # test thumbnail
    response = test_client.get("/Test/t/attachment1.gif")
    assert response.status_code == 200
