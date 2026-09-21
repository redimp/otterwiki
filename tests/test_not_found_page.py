#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:
"""
Tests for the configurable 404 page (NOT_FOUND_PAGE).
"""
import pytest


@pytest.fixture
def not_found_page(app_with_user):
    original = app_with_user.config.get("NOT_FOUND_PAGE")
    app_with_user.config["READ_ACCESS"] = "ANONYMOUS"
    yield app_with_user
    app_with_user.config["NOT_FOUND_PAGE"] = original


def _save(client, path, content):
    rv = client.post(
        f"/{path}/save",
        data={"content": content, "commit": f"create {path}"},
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert rv.request.path == f"/{path}"


def test_default_404(not_found_page, test_client):
    not_found_page.config["NOT_FOUND_PAGE"] = ""
    rv = test_client.get("/DoesNotExist")
    assert rv.status_code == 404
    html = rv.data.decode()
    assert "404 Page not found" in html
    assert "/DoesNotExist?edit" in html


def test_custom_404(not_found_page, test_client):
    _save(
        test_client,
        "Meta/NotFound",
        "# Moved\n\nWe migrated from **Trac**, some pages moved.",
    )
    not_found_page.config["NOT_FOUND_PAGE"] = "Meta/NotFound"
    rv = test_client.get("/Old/Trac/Page")
    assert rv.status_code == 404
    html = rv.data.decode()
    assert "<strong>Trac</strong>" in html
    assert "404 Page not found" not in html
    # the link to create the missing page is kept
    assert "/Old/Trac/Page?edit" in html


def test_custom_404_leading_slash(not_found_page, test_client):
    _save(test_client, "Meta/NotFound", "custom not found text 4711")
    not_found_page.config["NOT_FOUND_PAGE"] = "/Meta/NotFound/"
    rv = test_client.get("/Missing")
    assert rv.status_code == 404
    assert "custom not found text 4711" in rv.data.decode()


def test_custom_404_configured_page_missing(not_found_page, test_client):
    # configured page does not exist -> fall back to the default
    not_found_page.config["NOT_FOUND_PAGE"] = "Meta/DoesNotExistEither"
    rv = test_client.get("/Missing")
    assert rv.status_code == 404
    assert "404 Page not found" in rv.data.decode()


def test_custom_404_is_the_missing_page(not_found_page, test_client):
    # visiting the missing 404 page itself must not recurse
    not_found_page.config["NOT_FOUND_PAGE"] = "Meta/NotFound"
    rv = test_client.get("/Meta/NotFound")
    assert rv.status_code == 404
    assert "404 Page not found" in rv.data.decode()


def test_custom_404_on_history(not_found_page, test_client):
    _save(test_client, "Meta/NotFound", "custom not found text 0815")
    not_found_page.config["NOT_FOUND_PAGE"] = "Meta/NotFound"
    rv = test_client.get("/Missing/history")
    assert rv.status_code == 404
    assert "custom not found text 0815" in rv.data.decode()


#
# the admin preferences
#
def test_admin_sets_not_found_page(app_with_user, admin_client):
    site_name = app_with_user.config["SITE_NAME"]
    rv = admin_client.post(
        "/-/admin",
        data={
            "site_name": site_name,
            "not_found_page": "/Meta/NotFound",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert app_with_user.config["NOT_FOUND_PAGE"] == "Meta/NotFound"
    assert app_with_user.config["SITE_NAME"] == site_name
    assert 'value="Meta/NotFound"' in rv.data.decode()


@pytest.mark.parametrize(
    "value,message",
    [
        ("Meta/NotFound.md", "should not include the .md extension"),
        ("/-/index", "must be a regular wiki page"),
    ],
)
def test_admin_rejects_invalid_not_found_page(
    app_with_user, admin_client, value, message
):
    original = app_with_user.config.get("NOT_FOUND_PAGE")
    site_name = app_with_user.config["SITE_NAME"]
    rv = admin_client.post(
        "/-/admin",
        data={
            "site_name": "changed but not saved",
            "not_found_page": value,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert message in rv.data.decode()
    assert app_with_user.config.get("NOT_FOUND_PAGE") == original
    assert app_with_user.config["SITE_NAME"] == site_name
