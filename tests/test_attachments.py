#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import base64
from flask import url_for

@pytest.fixture
def app_with_attachments(create_app):
    # create test page
    message = "Test.md commit"
    filename = "test.md"
    author = ("Example Author", "mail@example.com")
    # create attachment
    create_app.storage.store(
        filename, content="# Test\nAttachment Test.", author=author, message=message
    )
    assert True == create_app.storage.exists(filename)
    # create txt attachment
    message = "Test/attachment0.txt attach0-commit"
    create_app.storage.store(
        "test/attachment0.txt",
        content="attachment0-content0",
        author=author,
        message=message,
    )
    assert True == create_app.storage.exists("test/attachment0.txt")
    # create gif attachment
    message = "Test/attachment1.gif attach1-commit"
    content_b64 = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
    create_app.storage.store(
        "test/attachment1.gif",
        content=base64.b64decode(content_b64),
        author=author,
        message=message,
        mode="wb",
    )
    assert True == create_app.storage.exists("test/attachment1.gif")
    yield create_app


@pytest.fixture
def test_client(app_with_attachments):
    client = app_with_attachments.test_client()
    client._app = app_with_attachments
    yield client


def test_app_with_attachments(test_client):
    response = test_client.get("/Test/view")
    assert response.status_code == 200


def test_list_attachments(test_client):
    response = test_client.get("/Test/attachments")
    assert response.status_code == 200
    assert "attachment0.txt" in response.data.decode()


def test_get_attachment0_legcay(test_client):
    response = test_client.get("/Test/a/attachment0.txt")
    assert response.status_code == 200
    assert "attachment0-content0" in response.data.decode()


def test_get_attachment0(test_client):
    response = test_client.get("/Test/attachment0.txt")
    assert response.status_code == 200
    assert "attachment0-content0" in response.data.decode()


def test_edit_attachment0(test_client):
    response = test_client.get("/Test/attachment/attachment0.txt")
    assert response.status_code == 200
    assert "attach0-commit" in response.data.decode()


def test_thumbnail_legacy(test_client):
    response = test_client.get("/Test/attachment/attachment1.gif")
    assert response.status_code == 200
    assert "attach1-commit" in response.data.decode()
    # test download
    response = test_client.get("/Test/a/attachment1.gif")
    assert response.status_code == 200
    # test thumbnail
    response = test_client.get("/Test/t/attachment1.gif")
    assert response.status_code == 200


def test_thumbnail(test_client):
    # test download
    response = test_client.get("/Test/attachment1.gif")
    assert response.status_code == 200
    # test thumbnail
    response = test_client.get("/Test/attachment1.gif?thumbnail")
    assert response.status_code == 200
    # test thumbnail
    response = test_client.get("/Test/attachment1.gif?thumbnail=10")
    assert response.status_code == 200


def test_rename_attachment(test_client, req_ctx):
    response = test_client.get("/Test/attachments")
    assert response.status_code == 200
    assert "attachment0.txt" in response.data.decode()
    response = test_client.post(
        url_for("edit_attachment",pagepath="Test",filename="attachment0.txt"),
        data={
            "new_filename": "attachment0_renamed.txt",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "attachment0_renamed.txt" in response.data.decode()
