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
        roles_header=app.config["AUTH_HEADERS_PERMISSIONS"],
        read_roles=app.config.get("AUTH_ROLES_READ"),
        write_roles=app.config.get("AUTH_ROLES_WRITE"),
        upload_roles=app.config.get("AUTH_ROLES_UPLOAD"),
        admin_roles=app.config.get("AUTH_ROLES_ADMIN"),
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
        roles_header="x-remote-permissions",
        read_roles="READ",
        write_roles="WRITE",
        upload_roles="UPLOAD",
        admin_roles="ADMIN",
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
# unit tests: role mapping
#

# role configuration as in the example from PR #525: the proxy sends
# roles like "member" or "moderator, admin" which are mapped to the
# internal permissions
ROLES_CONFIG = {
    "read_roles": "member, moderator, admin",
    "write_roles": "moderator, admin",
    "upload_roles": "moderator, admin",
    "admin_roles": "admin",
}


def role_auth(**kwargs):
    from otterwiki.auth import ProxyHeaderAuth

    config = {
        "username_header": "x-otterwiki-name",
        "email_header": "x-otterwiki-email",
        "roles_header": "x-otterwiki-permissions",
        **ROLES_CONFIG,
        **kwargs,
    }
    return ProxyHeaderAuth(**config)


def load_user(app, auth, roles):
    from flask import request

    with app.test_request_context(
        "/",
        headers={
            "x-otterwiki-name": PROXY_USER["name"],
            "x-otterwiki-email": PROXY_USER["email"],
            "x-otterwiki-permissions": roles,
        },
    ):
        return auth.request_loader(request)


def test_parse_roles(create_app):
    # create_app configures the app, without it otterwiki.auth can not
    # be imported
    from otterwiki.auth import ProxyHeaderAuth

    parse_roles = (
        ProxyHeaderAuth._parse_roles  # pyright: ignore[reportPrivateUsage]
    )
    assert parse_roles("moderator, admin") == {"MODERATOR", "ADMIN"}
    assert parse_roles("moderator ,admin") == {"MODERATOR", "ADMIN"}
    assert parse_roles("moderator admin") == {"MODERATOR", "ADMIN"}
    assert parse_roles("moderator  admin") == {"MODERATOR", "ADMIN"}
    assert parse_roles(" admin ") == {"ADMIN"}
    assert parse_roles("a,,b, ,c") == {"A", "B", "C"}
    assert parse_roles("") == set()


def test_request_loader_role_mapping_member(create_app):
    user = load_user(create_app, role_auth(), "member")
    assert user is not None
    assert user.allow_read is True
    assert user.allow_write is False
    assert user.allow_upload is False
    assert not user.is_admin


def test_request_loader_role_mapping_moderator(create_app):
    user = load_user(create_app, role_auth(), "moderator")
    assert user is not None
    assert user.allow_read is True
    assert user.allow_write is True
    assert user.allow_upload is True
    assert not user.is_admin


def test_request_loader_role_mapping_admin(create_app):
    user = load_user(create_app, role_auth(), "admin")
    assert user is not None
    assert user.allow_read is True
    assert user.allow_write is True
    assert user.allow_upload is True
    assert user.is_admin


def test_request_loader_role_mapping_multiple_roles(create_app):
    # whitespace after the comma in the header value must not prevent
    # the match with the configured roles
    user = load_user(create_app, role_auth(), "moderator, admin")
    assert user is not None
    assert user.allow_read is True
    assert user.allow_write is True
    assert user.allow_upload is True
    assert user.is_admin


def test_request_loader_role_mapping_is_case_insensitive(create_app):
    user = load_user(create_app, role_auth(), "Moderator")
    assert user is not None
    assert user.allow_read is True
    assert user.allow_write is True
    # and vice versa: mixed case in the configuration
    auth = role_auth(admin_roles="Admin")
    user = load_user(create_app, auth, "ADMIN")
    assert user is not None
    assert user.is_admin


def test_request_loader_unknown_role_grants_nothing(create_app):
    user = load_user(create_app, role_auth(), "guest")
    assert user is not None
    assert not user.allow_read
    assert not user.allow_write
    assert not user.allow_upload
    assert not user.is_admin


def test_request_loader_permissions_are_not_roles(create_app):
    # with a role configuration the internal permission names must not
    # grant any permissions (ADMIN is left out, since "admin" is a
    # configured role in ROLES_CONFIG)
    user = load_user(create_app, role_auth(), "READ,WRITE,UPLOAD")
    assert user is not None
    assert not user.allow_read
    assert not user.allow_write
    assert not user.allow_upload
    assert not user.is_admin


def test_request_loader_empty_role_config(create_app):
    # an empty role configuration disables the permission entirely
    auth = role_auth(admin_roles="")
    user = load_user(create_app, auth, "admin")
    assert user is not None
    assert user.allow_read is True
    assert user.allow_write is True
    assert not user.is_admin


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


#
# integration tests: routes with a role mapping configured
#
@pytest.fixture
def role_auth_app(proxy_auth_app):
    """proxy_auth_app with the ROLES_CONFIG mapping installed. The
    teardown of proxy_auth_app restores the original auth_manager."""
    import otterwiki.auth
    from otterwiki.auth import login_manager

    proxy_auth = role_auth()
    otterwiki.auth.auth_manager = proxy_auth
    login_manager.request_loader(proxy_auth.request_loader)
    return proxy_auth_app


def test_moderator_can_edit_but_not_admin(role_auth_app):
    client = proxy_client(role_auth_app, permissions="moderator", **PROXY_USER)
    response = client.post(
        "/Example/save",
        data={
            "content": "# Example\n\nCreated by a moderator.",
            "commit": "created example page",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Created by a moderator." in response.data.decode()
    response = client.get("/-/admin")
    assert response.status_code == 403


def test_member_can_read_but_not_edit(role_auth_app):
    client = proxy_client(role_auth_app, permissions="member", **PROXY_USER)
    response = client.get("/-/login")
    assert response.status_code == 302
    response = client.post(
        "/Example/save",
        data={
            "content": "# Example",
            "commit": "",
        },
    )
    assert response.status_code == 403


def test_admin_role_can_access_admin_page(role_auth_app):
    client = proxy_client(role_auth_app, permissions="admin", **PROXY_USER)
    response = client.get("/-/admin")
    assert response.status_code == 200
