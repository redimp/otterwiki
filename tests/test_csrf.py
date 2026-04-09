# vim: set et ts=8 sts=4 sw=4 ai:

"""Tests verifying that CSRF protection is active and enforced.

Uses the raw FlaskClient (not CSRFTestClient) so that CSRF tokens
are NOT injected automatically.  Every POST without a valid token
must be rejected with 400.
"""

import re
import pytest
from flask.testing import FlaskClient


# ---------------------------------------------------------------------------
# Fixtures -- raw client (no automatic CSRF token injection)
# ---------------------------------------------------------------------------


@pytest.fixture
def csrf_app(create_app):
    """Wrap create_app with WTF_CSRF_ENABLED=True."""
    create_app.config['WTF_CSRF_ENABLED'] = True
    return create_app


@pytest.fixture
def csrf_app_with_user(app_with_user):
    """Wrap app_with_user with WTF_CSRF_ENABLED=True."""
    app_with_user.config['WTF_CSRF_ENABLED'] = True
    return app_with_user


@pytest.fixture
def raw_client(csrf_app):
    """A plain FlaskClient that does NOT inject CSRF tokens."""
    old_cls = csrf_app.test_client_class
    csrf_app.test_client_class = FlaskClient
    client = csrf_app.test_client()
    csrf_app.test_client_class = old_cls
    return client


@pytest.fixture
def raw_admin_client(csrf_app_with_user):
    """A plain FlaskClient logged in as admin, without CSRF injection."""
    old_cls = csrf_app_with_user.test_client_class
    csrf_app_with_user.test_client_class = FlaskClient
    client = csrf_app_with_user.test_client()
    csrf_app_with_user.test_client_class = old_cls
    # Login requires a CSRF token -- fetch one manually.
    token = _get_csrf_token(client)
    result = client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "password1234",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    assert "You logged in successfully." in result.data.decode()
    return client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_csrf_token(client):
    """Fetch the CSRF token from the home page meta tag."""
    response = client.get('/', follow_redirects=True)
    match = re.search(
        r'name="csrf-token" content="([^"]+)"',
        response.data.decode(),
    )
    assert match, "CSRF meta tag not found in response"
    return match.group(1)


# ---------------------------------------------------------------------------
# Tests -- requests WITHOUT token must be rejected (400)
# ---------------------------------------------------------------------------


class TestCSRFRejection:
    """POST requests without a valid CSRF token must return 400."""

    def test_login_rejected(self, raw_client):
        rv = raw_client.post(
            "/-/login",
            data={
                "email": "user@example.org",
                "password": "secret",
            },
        )
        assert rv.status_code == 400

    def test_register_rejected(self, raw_client):
        rv = raw_client.post(
            "/-/register",
            data={
                "name": "Foo",
                "email": "foo@example.org",
                "password": "secret1234",
                "password_repeat": "secret1234",
            },
        )
        assert rv.status_code == 400

    def test_lost_password_rejected(self, raw_client):
        rv = raw_client.post(
            "/-/lost_password",
            data={"email": "user@example.org"},
        )
        assert rv.status_code == 400

    def test_create_page_rejected(self, raw_client):
        rv = raw_client.post(
            "/-/create",
            data={"pagename": "NewPage"},
        )
        assert rv.status_code == 400

    def test_search_rejected(self, raw_client):
        rv = raw_client.post(
            "/-/search",
            data={"query": "hello"},
        )
        assert rv.status_code == 400

    def test_settings_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/-/settings",
            data={"name": "Updated Name"},
        )
        assert rv.status_code == 400

    def test_admin_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/-/admin",
            data={"SITE_NAME": "Hacked Wiki"},
        )
        assert rv.status_code == 400

    def test_page_save_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/Home/save",
            data={
                "content": "# pwned",
                "commit": "evil commit",
            },
        )
        assert rv.status_code == 400

    def test_page_preview_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/Home/preview",
            data={"content": "# hello"},
        )
        assert rv.status_code == 400

    def test_page_delete_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/Home/delete",
            data={},
        )
        assert rv.status_code == 400

    def test_page_rename_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/Home/rename",
            data={"newname": "Hijacked"},
        )
        assert rv.status_code == 400

    def test_draft_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/Home/draft",
            data={"content": "draft text"},
        )
        assert rv.status_code == 400

    def test_housekeeping_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/-/housekeeping",
            data={},
        )
        assert rv.status_code == 400

    def test_user_management_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/-/admin/user_management",
            data={},
        )
        assert rv.status_code == 400

    def test_attachment_upload_rejected(self, raw_admin_client):
        import io

        data = {
            'file': (io.BytesIO(b"fake image data"), 'test.png'),
        }
        rv = raw_admin_client.post(
            "/Home/attachments",
            data=data,
            content_type='multipart/form-data',
        )
        assert rv.status_code == 400

    def test_inline_attachment_rejected(self, raw_admin_client):
        import io

        data = {
            'file': (io.BytesIO(b"fake image data"), 'inline.png'),
        }
        rv = raw_admin_client.post(
            "/Home/inline_attachment",
            data=data,
            content_type='multipart/form-data',
        )
        assert rv.status_code == 400

    def test_admin_sidebar_preferences_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/-/admin/sidebar_preferences",
            data={},
        )
        assert rv.status_code == 400

    def test_admin_permissions_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/-/admin/permissions_and_registration",
            data={},
        )
        assert rv.status_code == 400

    def test_admin_content_and_editing_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/-/admin/content_and_editing",
            data={},
        )
        assert rv.status_code == 400

    def test_admin_repository_management_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/-/admin/repository_management",
            data={},
        )
        assert rv.status_code == 400

    def test_admin_mail_preferences_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/-/admin/mail_preferences",
            data={},
        )
        assert rv.status_code == 400

    def test_user_edit_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/-/user/",
            data={"name": "Hacked Name"},
        )
        assert rv.status_code == 400

    def test_page_edit_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/Home/edit",
            data={"draft": "edit"},
        )
        assert rv.status_code == 400

    def test_page_history_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/Home/history",
            data={"rev_a": "aaa", "rev_b": "bbb"},
        )
        assert rv.status_code == 400

    def test_edit_attachment_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/Home/attachment/test.png",
            data={"new_filename": "evil.png"},
        )
        assert rv.status_code == 400

    def test_revert_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/-/revert/abc123",
            data={"message": "revert"},
        )
        assert rv.status_code == 400

    def test_plugin_url_rejected(self, raw_client):
        rv = raw_client.post(
            "/-/plugin/fakeplugin/action",
            data={},
        )
        assert rv.status_code == 400

    def test_admin_plugin_url_rejected(self, raw_admin_client):
        rv = raw_admin_client.post(
            "/-/admin/plugin/fakeplugin/action",
            data={},
        )
        assert rv.status_code == 400


# ---------------------------------------------------------------------------
# Tests -- invalid / tampered tokens must be rejected
# ---------------------------------------------------------------------------


class TestCSRFInvalidToken:
    """POST requests with an invalid or tampered CSRF token must fail."""

    def test_invalid_token_rejected(self, raw_client):
        rv = raw_client.post(
            "/-/login",
            data={
                "email": "user@example.org",
                "password": "secret",
                "csrf_token": "this-is-not-a-valid-token",
            },
        )
        assert rv.status_code == 400

    def test_empty_token_rejected(self, raw_client):
        rv = raw_client.post(
            "/-/login",
            data={
                "email": "user@example.org",
                "password": "secret",
                "csrf_token": "",
            },
        )
        assert rv.status_code == 400


# ---------------------------------------------------------------------------
# Tests -- requests WITH a valid token must succeed (not 400)
# ---------------------------------------------------------------------------


class TestCSRFAccepted:
    """POST requests with a valid CSRF token must not be rejected."""

    def test_login_with_token(self, raw_client):
        token = _get_csrf_token(raw_client)
        rv = raw_client.post(
            "/-/login",
            data={
                "email": "user@example.org",
                "password": "wrong",
                "csrf_token": token,
            },
            follow_redirects=True,
        )
        # Should not be 400 -- may be 200 with login-failed message
        assert rv.status_code != 400

    def test_search_with_token(self, raw_client):
        token = _get_csrf_token(raw_client)
        rv = raw_client.post(
            "/-/search",
            data={
                "query": "hello",
                "csrf_token": token,
            },
            follow_redirects=True,
        )
        assert rv.status_code != 400

    def test_create_page_with_token(self, raw_client):
        token = _get_csrf_token(raw_client)
        rv = raw_client.post(
            "/-/create",
            data={
                "pagename": "TestPage",
                "csrf_token": token,
            },
            follow_redirects=True,
        )
        assert rv.status_code != 400

    def test_settings_with_token(self, raw_admin_client):
        token = _get_csrf_token(raw_admin_client)
        rv = raw_admin_client.post(
            "/-/settings",
            data={
                "name": "Updated Name",
                "csrf_token": token,
            },
            follow_redirects=True,
        )
        assert rv.status_code != 400

    def test_admin_with_token(self, raw_admin_client):
        token = _get_csrf_token(raw_admin_client)
        rv = raw_admin_client.post(
            "/-/admin/permissions_and_registration",
            data={
                "csrf_token": token,
            },
            follow_redirects=True,
        )
        assert rv.status_code != 400


# ---------------------------------------------------------------------------
# Tests -- CSRF token via X-CSRFToken header (AJAX / HTMX requests)
# ---------------------------------------------------------------------------


class TestCSRFHeader:
    """CSRF validation must accept tokens via the X-CSRFToken header."""

    def test_header_token_accepted(self, raw_client):
        token = _get_csrf_token(raw_client)
        rv = raw_client.post(
            "/-/search",
            data={"query": "hello"},
            headers={"X-CSRFToken": token},
            follow_redirects=True,
        )
        assert rv.status_code != 400

    def test_header_invalid_token_rejected(self, raw_client):
        rv = raw_client.post(
            "/-/search",
            data={"query": "hello"},
            headers={"X-CSRFToken": "bad-token"},
        )
        assert rv.status_code == 400

    def test_header_without_form_field(self, raw_admin_client):
        """Token in header alone (no csrf_token form field) must work."""
        token = _get_csrf_token(raw_admin_client)
        rv = raw_admin_client.post(
            "/-/settings",
            data={"name": "Updated"},
            headers={"X-CSRFToken": token},
            follow_redirects=True,
        )
        assert rv.status_code != 400


# ---------------------------------------------------------------------------
# Tests -- csrf-exempt routes must work without token
# ---------------------------------------------------------------------------


class TestCSRFExempt:
    """Routes decorated with @csrf.exempt must accept requests
    without a CSRF token."""

    def test_webhook_exempt(self, raw_client):
        # The webhook route is CSRF-exempt but validates via hash.
        # A made-up hash will return a non-400 error (likely 403/404),
        # proving CSRF is not the gatekeeper.
        rv = raw_client.post("/-/api/v1/pull/somefakehash")
        assert rv.status_code != 400

    def test_git_info_refs_exempt(self, raw_client):
        rv = raw_client.post("/.git/info/refs")
        # 400 from missing service param is fine -- not a CSRF 400
        assert rv.status_code == 400
        assert b"CSRF" not in rv.data

    def test_git_upload_pack_exempt(self, raw_client):
        rv = raw_client.post(
            "/.git/git-upload-pack",
            data=b"",
            content_type="application/x-git-upload-pack-request",
        )
        assert rv.status_code != 400 or b"CSRF" not in rv.data

    def test_git_receive_pack_exempt(self, raw_client):
        rv = raw_client.post(
            "/.git/git-receive-pack",
            data=b"",
            content_type="application/x-git-receive-pack-request",
        )
        assert rv.status_code != 400 or b"CSRF" not in rv.data


# ---------------------------------------------------------------------------
# Tests -- CSRFTestClient auto-injection works
# ---------------------------------------------------------------------------


class TestCSRFTestClient:
    """Verify the CSRFTestClient fixture injects tokens correctly."""

    def test_auto_injected_post(self, csrf_app):
        """The standard test_client (CSRFTestClient) must inject tokens
        automatically, so POSTs succeed without manual token handling."""
        client = csrf_app.test_client()
        rv = client.post(
            "/-/search",
            data={"query": "hello"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
