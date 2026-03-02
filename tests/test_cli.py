#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
Tests for otterwiki.cli.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cli_app(create_app, req_ctx):
    """App fixture with a clean user table."""
    from otterwiki.auth import SimpleAuth, db

    db.session.query(SimpleAuth.User).delete()
    db.session.commit()
    yield create_app


@pytest.fixture
def cli_app_with_user(cli_app, req_ctx):
    """App fixture with one pre-existing user."""
    from otterwiki.auth import SimpleAuth, db
    from werkzeug.security import generate_password_hash

    user = SimpleAuth.User(  # pyright: ignore
        name="Existing User",
        email="existing@example.com",
        password_hash=generate_password_hash("password1234", method="scrypt"),
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        is_admin=False,
        is_approved=True,
        email_confirmed=True,
    )
    db.session.add(user)
    db.session.commit()
    yield cli_app


@pytest.fixture
def runner(cli_app):
    return cli_app.test_cli_runner()


@pytest.fixture
def runner_with_user(cli_app_with_user):
    return cli_app_with_user.test_cli_runner()


# ---------------------------------------------------------------------------
# flask user create
# ---------------------------------------------------------------------------


def test_create_basic(runner, cli_app):
    """Create a user with just email and name."""
    result = runner.invoke(
        args=["user", "create", "new@example.com", "New User"]
    )
    assert result.exit_code == 0, result.output
    assert "created successfully" in result.output

    from otterwiki.auth import SimpleAuth

    user = SimpleAuth.User.query.filter_by(email="new@example.com").first()
    assert user is not None
    assert user.name == "New User"
    assert user.password_hash is None
    assert user.is_admin is False
    assert user.is_approved is False
    assert user.email_confirmed is False


def test_create_with_flags_and_permissions(runner, cli_app):
    """Create a user with flags and permissions."""
    result = runner.invoke(
        args=[
            "user",
            "create",
            "full@example.com",
            "Full User",
            "--flags=email_confirmed,approved",
            "--permissions=read,write,upload",
        ]
    )
    assert result.exit_code == 0, result.output

    from otterwiki.auth import SimpleAuth

    user = SimpleAuth.User.query.filter_by(email="full@example.com").first()
    assert user.email_confirmed is True
    assert user.is_approved is True
    assert user.allow_read is True
    assert user.allow_write is True
    assert user.allow_upload is True
    assert user.is_admin is False


def test_create_admin_permission(runner, cli_app):
    """Creating with admin permission sets is_admin and all permissions."""
    result = runner.invoke(
        args=[
            "user",
            "create",
            "admin@example.com",
            "Admin User",
            "-p",
            "admin",
        ]
    )
    assert result.exit_code == 0, result.output

    from otterwiki.auth import SimpleAuth

    user = SimpleAuth.User.query.filter_by(email="admin@example.com").first()
    assert user.is_admin is True
    assert user.is_approved is True
    assert user.allow_read is True
    assert user.allow_write is True
    assert user.allow_upload is True


def test_create_no_password_cannot_login(cli_app_with_user):
    """A user with no password cannot log in."""
    from otterwiki.auth import SimpleAuth, db

    user = SimpleAuth.User(  # pyright: ignore
        name="No Pass",
        email="nopass@example.com",
        password_hash=None,
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        is_approved=True,
        email_confirmed=True,
    )
    db.session.add(user)
    db.session.commit()

    client = cli_app_with_user.test_client()
    rv = client.post(
        "/-/login",
        data={"email": "nopass@example.com", "password": ""},
        follow_redirects=True,
    )
    assert "Invalid email address or password." in rv.data.decode()


def test_create_duplicate_email_fails(runner_with_user):
    """Creating a user with an existing email fails."""
    result = runner_with_user.invoke(
        args=["user", "create", "existing@example.com", "Duplicate"]
    )
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_create_invalid_email_fails(runner):
    """Creating a user with an invalid email fails."""
    result = runner.invoke(
        args=["user", "create", "not-an-email", "Some User"]
    )
    assert result.exit_code != 0
    assert "not a valid email" in result.output


def test_create_invalid_flag_fails(runner):
    """Creating a user with an unknown flag fails."""
    result = runner.invoke(
        args=["user", "create", "x@example.com", "X User", "--flags=bad_flag"]
    )
    assert result.exit_code != 0
    assert "Unknown flag" in result.output


def test_create_invalid_permission_fails(runner):
    """Creating a user with an unknown permission fails."""
    result = runner.invoke(
        args=[
            "user",
            "create",
            "x@example.com",
            "X User",
            "--permissions=superpower",
        ]
    )
    assert result.exit_code != 0
    assert "Unknown permission" in result.output


# ---------------------------------------------------------------------------
# flask user edit
# ---------------------------------------------------------------------------


def test_edit_name(runner_with_user, cli_app_with_user):
    """Edit a user's name."""
    result = runner_with_user.invoke(
        args=[
            "user",
            "edit",
            "existing@example.com",
            "--new-name=Updated Name",
        ]
    )
    assert result.exit_code == 0, result.output
    assert "updated successfully" in result.output

    from otterwiki.auth import SimpleAuth

    user = SimpleAuth.User.query.filter_by(
        email="existing@example.com"
    ).first()
    assert user.name == "Updated Name"


def test_edit_email(runner_with_user, cli_app_with_user):
    """Edit a user's email."""
    result = runner_with_user.invoke(
        args=[
            "user",
            "edit",
            "existing@example.com",
            "--new-email=updated@example.com",
        ]
    )
    assert result.exit_code == 0, result.output

    from otterwiki.auth import SimpleAuth

    assert (
        SimpleAuth.User.query.filter_by(email="updated@example.com").first()
        is not None
    )
    assert (
        SimpleAuth.User.query.filter_by(email="existing@example.com").first()
        is None
    )


def test_edit_permissions(runner_with_user, cli_app_with_user):
    """Edit a user's permissions using short flag."""
    result = runner_with_user.invoke(
        args=["user", "edit", "existing@example.com", "-p", "admin"]
    )
    assert result.exit_code == 0, result.output

    from otterwiki.auth import SimpleAuth

    user = SimpleAuth.User.query.filter_by(
        email="existing@example.com"
    ).first()
    assert user.is_admin is True


def test_edit_no_options_fails(runner_with_user):
    """Editing without any options fails."""
    result = runner_with_user.invoke(
        args=["user", "edit", "existing@example.com"]
    )
    assert result.exit_code != 0
    assert "At least one" in result.output


def test_edit_nonexistent_user_fails(runner):
    """Editing a non-existent user fails."""
    result = runner.invoke(
        args=["user", "edit", "ghost@example.com", "--new-name=Ghost"]
    )
    assert result.exit_code != 0
    assert "not found" in result.output


def test_edit_duplicate_email_fails(runner_with_user, cli_app_with_user):
    """Editing to an already-used email fails."""
    from otterwiki.auth import SimpleAuth, db

    other = SimpleAuth.User(  # pyright: ignore
        name="Other",
        email="other@example.com",
        password_hash=None,
        first_seen=datetime.now(),
        last_seen=datetime.now(),
    )
    db.session.add(other)
    db.session.commit()

    result = runner_with_user.invoke(
        args=[
            "user",
            "edit",
            "existing@example.com",
            "--new-email=other@example.com",
        ]
    )
    assert result.exit_code != 0
    assert "already exists" in result.output


# ---------------------------------------------------------------------------
# flask user password
# ---------------------------------------------------------------------------


def test_password_interactive(runner_with_user, cli_app_with_user):
    """Set password interactively."""
    result = runner_with_user.invoke(
        args=["user", "password", "existing@example.com", "-i"],
        input="newpassword123\nnewpassword123\n",
    )
    assert result.exit_code == 0, result.output
    assert "updated successfully" in result.output

    from otterwiki.auth import SimpleAuth
    from werkzeug.security import check_password_hash

    user = SimpleAuth.User.query.filter_by(
        email="existing@example.com"
    ).first()
    assert user.password_hash is not None
    assert check_password_hash(user.password_hash, "newpassword123")


def test_password_interactive_mismatch_retries(runner_with_user):
    """Mismatched passwords prompt again."""
    result = runner_with_user.invoke(
        args=["user", "password", "existing@example.com", "-i"],
        input="password123\nwrongpassword\npassword123\npassword123\n",
    )
    assert result.exit_code == 0, result.output
    assert "do not match" in result.output
    assert "updated successfully" in result.output


def test_password_no_option_fails(runner_with_user):
    """Calling password without any option fails."""
    result = runner_with_user.invoke(
        args=["user", "password", "existing@example.com"]
    )
    assert result.exit_code != 0
    assert "Provide" in result.output


def test_password_both_options_fails(runner_with_user):
    """Calling password with both options fails."""
    result = runner_with_user.invoke(
        args=[
            "user",
            "password",
            "existing@example.com",
            "--password-interactive",
            "--send-password-reset",
        ],
        input="password123\npassword123\n",
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output


def test_password_nonexistent_user_fails(runner):
    """Setting password for non-existent user fails."""
    result = runner.invoke(
        args=["user", "password", "ghost@example.com", "-i"],
        input="password123\npassword123\n",
    )
    assert result.exit_code != 0
    assert "not found" in result.output


def test_password_delete_password(runner_with_user, cli_app_with_user):
    """--delete-password unsets the password_hash."""
    from otterwiki.auth import SimpleAuth

    result = runner_with_user.invoke(
        args=["user", "password", "existing@example.com", "-d"]
    )
    assert result.exit_code == 0, result.output
    assert "deleted successfully" in result.output

    user = SimpleAuth.User.query.filter_by(
        email="existing@example.com"
    ).first()
    assert user.password_hash is None


def test_password_generate_password(runner_with_user, cli_app_with_user):
    """--generate-password sets a new password and prints it."""
    from otterwiki.auth import SimpleAuth
    from werkzeug.security import check_password_hash

    result = runner_with_user.invoke(
        args=["user", "password", "existing@example.com", "-g"]
    )
    assert result.exit_code == 0, result.output
    assert "set to:" in result.output

    generated = result.output.strip().split("set to:")[-1].strip()
    assert len(generated) == 12

    user = SimpleAuth.User.query.filter_by(
        email="existing@example.com"
    ).first()
    assert check_password_hash(user.password_hash, generated)


def test_password_send_reset_no_mail_server_fails(
    runner_with_user, cli_app_with_user
):
    """Sending password reset without mail server configured fails."""
    cli_app_with_user.config["MAIL_SERVER"] = ""
    result = runner_with_user.invoke(
        args=["user", "password", "existing@example.com", "-r"]
    )
    assert result.exit_code != 0
    assert "Mail server is not configured" in result.output


def test_password_send_reset_sends_email(runner_with_user, cli_app_with_user):
    """Sending password reset sends a reset email without clearing the password."""
    cli_app_with_user.config["MAIL_SERVER"] = "smtp.example.com"
    cli_app_with_user.config["MAIL_DEFAULT_SENDER"] = "noreply@example.com"

    with patch("otterwiki.cli.send_mail") as mock_send_mail:
        result = runner_with_user.invoke(
            args=["user", "password", "existing@example.com", "-r"]
        )
    assert result.exit_code == 0, result.output
    mock_send_mail.assert_called_once()


# ---------------------------------------------------------------------------
# flask user delete
# ---------------------------------------------------------------------------


def test_delete_with_confirm_flag(runner_with_user, cli_app_with_user):
    """Delete a user with --confirm skips interactive prompt."""
    result = runner_with_user.invoke(
        args=["user", "delete", "existing@example.com", "--confirm"]
    )
    assert result.exit_code == 0, result.output
    assert "deleted successfully" in result.output

    from otterwiki.auth import SimpleAuth

    assert (
        SimpleAuth.User.query.filter_by(email="existing@example.com").first()
        is None
    )


def test_delete_interactive_confirm(runner_with_user, cli_app_with_user):
    """Delete a user with interactive 'y' confirmation."""
    result = runner_with_user.invoke(
        args=["user", "delete", "existing@example.com"],
        input="y\n",
    )
    assert result.exit_code == 0, result.output
    assert "deleted successfully" in result.output


def test_delete_interactive_cancel(runner_with_user, cli_app_with_user):
    """Cancel deletion with interactive 'n'."""
    result = runner_with_user.invoke(
        args=["user", "delete", "existing@example.com"],
        input="n\n",
    )
    assert result.exit_code == 0, result.output
    assert "cancelled" in result.output

    from otterwiki.auth import SimpleAuth

    assert (
        SimpleAuth.User.query.filter_by(email="existing@example.com").first()
        is not None
    )


def test_delete_nonexistent_user_fails(runner):
    """Deleting a non-existent user fails."""
    result = runner.invoke(
        args=["user", "delete", "ghost@example.com", "--confirm"]
    )
    assert result.exit_code != 0
    assert "not found" in result.output


# ---------------------------------------------------------------------------
# flask user list
# ---------------------------------------------------------------------------


def test_list_empty(runner, cli_app):
    """Listing users when there are none."""
    result = runner.invoke(args=["user", "list"])
    assert result.exit_code == 0, result.output
    assert "No users found" in result.output


def test_list_empty_json(runner, cli_app):
    """Listing users in JSON when there are none returns empty array."""
    result = runner.invoke(args=["user", "list", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == []


def test_list_human_readable(runner_with_user):
    """Listing users in human-readable format shows user info."""
    result = runner_with_user.invoke(args=["user", "list"])
    assert result.exit_code == 0, result.output
    assert "existing@example.com" in result.output
    assert "Existing User" in result.output
    assert "Total: 1 user(s)" in result.output


def test_list_json(runner_with_user):
    """Listing users in JSON format returns correct data."""
    result = runner_with_user.invoke(args=["user", "list", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert len(data) == 1
    u = data[0]
    assert u["email"] == "existing@example.com"
    assert u["name"] == "Existing User"
    assert u["is_admin"] is False
    assert u["is_approved"] is True
    assert u["email_confirmed"] is True
    assert u["has_password"] is True
    # check all expected fields are present
    for field in [
        "id",
        "allow_read",
        "allow_write",
        "allow_upload",
        "first_seen",
        "last_seen",
    ]:
        assert field in u, f"Missing field: {field}"
