#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import base64
import pathlib
from io import BytesIO
from flask import url_for


@pytest.fixture
def app_with_attachments(create_app):
    # create test page
    message = "Test.md commit"
    filename = "test.md"
    author = ("Example Author", "mail@example.com")
    # create attachment
    create_app.storage.store(
        filename,
        content="# Test\nAttachment Test.",
        author=author,
        message=message,
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
    # create svg attachment
    message = "Test/attachment2.svg attach2-commit"
    svg_content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        '<rect width="10" height="10" fill="red"/></svg>'
    )
    create_app.storage.store(
        "test/attachment2.svg",
        content=svg_content,
        author=author,
        message=message,
    )
    assert True == create_app.storage.exists("test/attachment2.svg")
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


def test_thumbnail_svg(test_client):
    # SVG cannot be processed by PIL; the original file must be served
    response = test_client.get("/Test/attachment2.svg?thumbnail")
    assert response.status_code == 200
    assert b"<svg" in response.data
    response = test_client.get("/Test/attachment2.svg?thumbnail=10")
    assert response.status_code == 200
    assert b"<svg" in response.data


def test_rename_attachment(test_client, req_ctx):
    response = test_client.get("/Test/attachments")
    assert response.status_code == 200
    assert "attachment0.txt" in response.data.decode()
    response = test_client.post(
        url_for(
            "edit_attachment", pagepath="Test", filename="attachment0.txt"
        ),
        data={
            "new_filename": "attachment0_renamed.txt",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "attachment0_renamed.txt" in response.data.decode()


def _gif_bytes():
    content_b64 = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
    return base64.b64decode(content_b64)


def test_upload_attachment_unicode_filename(test_client):
    # issue #560: unicode characters must be preserved on upload
    filename = "Градове.gif"
    data = {"file": (BytesIO(_gif_bytes()), filename)}
    response = test_client.post(
        "/Test/attachments",
        content_type="multipart/form-data",
        data=data,
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert filename in response.data.decode()
    # the file exists on disk with its unicode name preserved
    storage_path = test_client._app.storage.path
    assert pathlib.Path(storage_path, "test", filename).exists()


def test_upload_attachment_path_traversal(test_client):
    # a traversal filename must land safely inside the attachment dir
    data = {"file": (BytesIO(_gif_bytes()), "../../evil.gif")}
    response = test_client.post(
        "/Test/attachments",
        content_type="multipart/form-data",
        data=data,
        follow_redirects=True,
    )
    assert response.status_code == 200
    storage_path = test_client._app.storage.path
    # stored inside the page's attachment directory, not outside the repo
    assert pathlib.Path(storage_path, "test", "evil.gif").exists()
    assert not pathlib.Path(storage_path).parent.joinpath("evil.gif").exists()


def test_rename_attachment_unicode(test_client, req_ctx):
    response = test_client.post(
        url_for(
            "edit_attachment", pagepath="Test", filename="attachment0.txt"
        ),
        data={"new_filename": "Градове.txt"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Градове.txt" in response.data.decode()
    storage_path = test_client._app.storage.path
    assert pathlib.Path(storage_path, "test", "Градове.txt").exists()


def test_rename_page_with_attachment(app_with_attachments, test_client):
    # create test page
    filename = "testa.md"
    author = ("Example Author", "mail@example.com")
    # create attachment
    app_with_attachments.storage.store(
        filename,
        content="# Test AB\nAttachment Test.",
        author=author,
        message="create testa",
    )
    assert True == app_with_attachments.storage.exists(filename)
    # create txt attachment
    app_with_attachments.storage.store(
        "testa/attachment0.txt",
        content="attachment0-content0",
        author=author,
        message="added attachment to testa",
    )
    # test attachment exists
    rv = test_client.get("/Testa/a/attachment0.txt")
    assert rv.status_code == 200
    # rename page
    rv = test_client.post(
        "/{}/rename".format("Testa"),
        data={"new_pagename": "Testb", "message": "renamed testa to testb"},
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # check that the attachment has been renamed, too
    rv = test_client.get("/Testb/a/attachment0.txt")
    assert rv.status_code == 200
    rv = test_client.get("/Testb/attachment0.txt")
    assert rv.status_code == 200

    # get log to find the revisions
    log = app_with_attachments.storage.log()[:3]
    assert log[1]["message"] == "added attachment to testa"

    rv = test_client.get(
        f"/Testb/attachment0.txt?revision={log[0]['revision']}"
    )
    assert rv.status_code == 200
    rv = test_client.get(f"/Testb/a/attachment0.txt/{log[0]['revision']}")
    assert rv.status_code == 200
    rv = test_client.get(
        f"/Testb/a/attachment0.txt?revision={log[0]['revision']}"
    )
    assert rv.status_code == 200

    # without a revision the attachment can not be found
    rv = test_client.get("/Testa/a/attachment0.txt")
    assert rv.status_code == 404

    # with the revision the attachment is found
    rv = test_client.get(f"/Testa/a/attachment0.txt/{log[1]['revision']}")
    assert rv.status_code == 200
    rv = test_client.get(
        f"/Testa/a/attachment0.txt?revision={log[1]['revision']}"
    )
    assert rv.status_code == 200
