#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest

PROXY_USER = {
    "name": "Proxy User",
    "email": "proxy@example.org",
}


@pytest.fixture
def proxy_auth_app(create_app):
    """create_app with the auth_manager swapped for a ProxyHeaderAuth.

    The auth_manager is chosen at import time of otterwiki.auth based on
    AUTH_METHOD, so for testing the ProxyHeaderAuth is patched in (and the
    request_loader registered with the login_manager) and restored
    afterwards.
    """
    import otterwiki.auth
    from otterwiki.auth import ProxyHeaderAuth, login_manager

    app = create_app
    original_auth_manager = otterwiki.auth.auth_manager
    original_auth_method = app.config.get("AUTH_METHOD")
    original_features = app.jinja_env.globals.get("auth_supported_features")

    app.config["AUTH_METHOD"] = "PROXY_HEADER"
    proxy_auth = ProxyHeaderAuth(
        username_header=app.config["AUTH_HEADERS_USERNAME"],
        email_header=app.config["AUTH_HEADERS_EMAIL"],
        permissions_header=app.config["AUTH_HEADERS_PERMISSIONS"],
    )
    otterwiki.auth.auth_manager = proxy_auth
    login_manager.request_loader(proxy_auth.request_loader)
    app.jinja_env.globals.update(
        auth_supported_features=proxy_auth.supported_features()
    )

    yield app

    otterwiki.auth.auth_manager = original_auth_manager
    login_manager._request_callback = (
        None  # pyright: ignore[reportPrivateUsage]
    )
    app.config["AUTH_METHOD"] = original_auth_method
    app.jinja_env.globals.update(auth_supported_features=original_features)


@pytest.fixture
def proxy_auth(proxy_auth_app):
    import otterwiki.auth

    assert proxy_auth_app.config["AUTH_METHOD"] == "PROXY_HEADER"
    return otterwiki.auth.auth_manager


def proxy_client(app, name=None, email=None, permissions=None):
    """Create a test client that sends the given proxy headers with
    every request (including the csrf token fetch of CSRFTestClient)."""
    client = app.test_client()
    if name is not None:
        client.environ_base["HTTP_X_OTTERWIKI_NAME"] = name
    if email is not None:
        client.environ_base["HTTP_X_OTTERWIKI_EMAIL"] = email
    if permissions is not None:
        client.environ_base["HTTP_X_OTTERWIKI_PERMISSIONS"] = permissions
    return client


#
# unit tests: request_loader
#
def test_request_loader_valid_headers(proxy_auth_app, proxy_auth):
    from flask import request

    with proxy_auth_app.test_request_context(
        "/",
        headers={
            "x-otterwiki-name": PROXY_USER["name"],
            "x-otterwiki-email": PROXY_USER["email"],
            "x-otterwiki-permissions": "READ,WRITE",
        },
    ):
        user = proxy_auth.request_loader(request)
    assert user is not None
    assert user.name == PROXY_USER["name"]
    assert user.email == PROXY_USER["email"]
    assert user.is_approved is True
    assert user.allow_read is True
    assert user.allow_write is True
    assert user.allow_upload is False
    assert not user.is_admin


def test_request_loader_missing_name_header(proxy_auth_app, proxy_auth):
    from flask import request

    with proxy_auth_app.test_request_context(
        "/",
        headers={
            "x-otterwiki-email": PROXY_USER["email"],
            "x-otterwiki-permissions": "READ",
        },
    ):
        assert proxy_auth.request_loader(request) is None


def test_request_loader_missing_email_header(proxy_auth_app, proxy_auth):
    from flask import request

    with proxy_auth_app.test_request_context(
        "/",
        headers={
            "x-otterwiki-name": PROXY_USER["name"],
            "x-otterwiki-permissions": "READ",
        },
    ):
        assert proxy_auth.request_loader(request) is None


def test_request_loader_empty_email(proxy_auth_app, proxy_auth):
    from flask import request

    with proxy_auth_app.test_request_context(
        "/",
        headers={
            "x-otterwiki-name": PROXY_USER["name"],
            "x-otterwiki-email": "",
            "x-otterwiki-permissions": "READ",
        },
    ):
        assert proxy_auth.request_loader(request) is None


def test_request_loader_empty_name_falls_back_to_email(
    proxy_auth_app, proxy_auth
):
    from flask import request

    with proxy_auth_app.test_request_context(
        "/",
        headers={
            "x-otterwiki-name": "",
            "x-otterwiki-email": PROXY_USER["email"],
            "x-otterwiki-permissions": "READ",
        },
    ):
        user = proxy_auth.request_loader(request)
    assert user is not None
    assert user.name == PROXY_USER["email"]


def test_request_loader_missing_permissions_header(proxy_auth_app, proxy_auth):
    from flask import request

    with proxy_auth_app.test_request_context(
        "/",
        headers={
            "x-otterwiki-name": PROXY_USER["name"],
            "x-otterwiki-email": PROXY_USER["email"],
        },
    ):
        user = proxy_auth.request_loader(request)
    assert user is not None
    assert not user.allow_read
    assert not user.allow_write
    assert not user.allow_upload
    assert not user.is_admin


def test_request_loader_permissions_are_case_insensitive(
    proxy_auth_app, proxy_auth
):
    from flask import request

    with proxy_auth_app.test_request_context(
        "/",
        headers={
            "x-otterwiki-name": PROXY_USER["name"],
            "x-otterwiki-email": PROXY_USER["email"],
            "x-otterwiki-permissions": "read,write,upload,admin",
        },
    ):
        user = proxy_auth.request_loader(request)
    assert user is not None
    assert user.allow_read is True
    assert user.allow_write is True
    assert user.allow_upload is True
    assert user.is_admin is True


def test_request_loader_custom_headers(proxy_auth_app):
    from flask import request
    from otterwiki.auth import ProxyHeaderAuth

    custom_auth = ProxyHeaderAuth(
        username_header="x-remote-name",
        email_header="x-remote-email",
        permissions_header="x-remote-permissions",
    )
    with proxy_auth_app.test_request_context(
        "/",
        headers={
            "x-remote-name": PROXY_USER["name"],
            "x-remote-email": PROXY_USER["email"],
            "x-remote-permissions": "READ",
        },
    ):
        user = custom_auth.request_loader(request)
    assert user is not None
    assert user.name == PROXY_USER["name"]
    assert user.email == PROXY_USER["email"]
    assert user.allow_read is True
    # the default headers must not be accepted
    with proxy_auth_app.test_request_context(
        "/",
        headers={
            "x-otterwiki-name": PROXY_USER["name"],
            "x-otterwiki-email": PROXY_USER["email"],
            "x-otterwiki-permissions": "READ",
        },
    ):
        assert custom_auth.request_loader(request) is None


#
# unit tests: has_permission and features
#
def test_has_permission(proxy_auth):
    user = proxy_auth.User(
        name=PROXY_USER["name"],
        email=PROXY_USER["email"],
        permissions=["READ", "WRITE"],
    )
    assert proxy_auth.has_permission("READ", user) is True
    assert proxy_auth.has_permission("read", user) is True
    assert proxy_auth.has_permission("WRITE", user) is True
    assert proxy_auth.has_permission("UPLOAD", user) is False
    assert proxy_auth.has_permission("ADMIN", user) is False


def test_has_permission_anonymous(proxy_auth):
    from otterwiki.auth import OtterWikiAnonymousUser

    anonymous = OtterWikiAnonymousUser()
    assert proxy_auth.has_permission("READ", anonymous) is False
    assert proxy_auth.has_permission("WRITE", anonymous) is False
    assert proxy_auth.has_permission("ADMIN", anonymous) is False


def test_supported_features(proxy_auth):
    features = proxy_auth.supported_features()
    assert features["passwords"] is False
    assert features["editing"] is False
    assert features["logout"] is False


#
# integration tests: routes with proxy headers
#
def test_view_anonymous_is_redirected_to_login(proxy_auth_app):
    client = proxy_auth_app.test_client()
    response = client.get("/")
    assert response.status_code == 302
    assert "/-/login" in response.headers["Location"]
    # the login form aborts with 403 for unauthenticated users
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 403


def test_login_redirects_user_with_read_permission(proxy_auth_app):
    client = proxy_client(proxy_auth_app, permissions="READ", **PROXY_USER)
    response = client.get("/-/login")
    assert response.status_code == 302
    assert response.headers["Location"] in ("/", "http://localhost/")


def test_login_forbidden_without_read_permission(proxy_auth_app):
    client = proxy_client(proxy_auth_app, permissions="", **PROXY_USER)
    response = client.get("/-/login")
    assert response.status_code == 403


def test_page_create_and_view(proxy_auth_app):
    client = proxy_client(
        proxy_auth_app, permissions="READ,WRITE", **PROXY_USER
    )
    response = client.post(
        "/Example/save",
        data={
            "content": "# Example\n\nCreated via proxy header auth.",
            "commit": "created example page",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode()
    assert "Created via proxy header auth." in html
    # the user from the headers is the commit author
    response = client.get("/Example/history")
    assert response.status_code == 200
    html = response.data.decode()
    assert PROXY_USER["name"] in html


def test_save_forbidden_without_write_permission(proxy_auth_app):
    client = proxy_client(proxy_auth_app, permissions="READ", **PROXY_USER)
    response = client.post(
        "/Example/save",
        data={
            "content": "# Example",
            "commit": "",
        },
    )
    assert response.status_code == 403


def test_save_forbidden_anonymous(proxy_auth_app):
    client = proxy_auth_app.test_client()
    # anonymous users can not render any page, so the CSRFTestClient can
    # not fetch a csrf token: the request fails with 400 (missing token)
    # before the missing WRITE permission is checked
    response = client.post(
        "/Example/save",
        data={
            "content": "# Example",
            "commit": "",
        },
    )
    assert response.status_code in (302, 400, 403)


def test_admin_page_with_admin_permission(proxy_auth_app):
    client = proxy_client(
        proxy_auth_app, permissions="READ,WRITE,UPLOAD,ADMIN", **PROXY_USER
    )
    response = client.get("/-/admin")
    assert response.status_code == 200


def test_admin_page_forbidden_without_admin_permission(proxy_auth_app):
    client = proxy_client(
        proxy_auth_app, permissions="READ,WRITE", **PROXY_USER
    )
    response = client.get("/-/admin")
    assert response.status_code == 403
