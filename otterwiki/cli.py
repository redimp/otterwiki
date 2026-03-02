#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
otterwiki.cli

And Otter Wiki CLI.

User management:
  For usage info call `flask user --help`.
  The same is available for individual commands, e.g. `flask user create --help`.
"""

import json
import sys
import click
from datetime import datetime
from flask import current_app, render_template
from flask.cli import AppGroup

from otterwiki.server import app, db
from otterwiki.util import is_valid_email, is_valid_name
from otterwiki.helper import send_mail, serialize

user_cli = AppGroup("user", help="User management commands.")


def _get_user(email):
    from otterwiki.auth import SimpleAuth

    user = SimpleAuth.User.query.filter_by(email=email.lower()).first()
    if user is None:
        click.echo(f"Error: User '{email}' not found.", err=True)
        sys.exit(1)
    return user


def _parse_flags(flags_str):
    valid_flags = {"email_confirmed", "approved"}
    result = {}
    if not flags_str:
        return result
    for flag in flags_str.split(","):
        flag = flag.strip()
        if not flag:
            continue
        if flag not in valid_flags:
            click.echo(
                f"Error: Unknown flag '{flag}'. Valid flags: {', '.join(sorted(valid_flags))}",
                err=True,
            )
            sys.exit(1)
        result[flag] = True
    return result


def _parse_permissions(permissions_str):
    valid_permissions = {"read", "write", "upload", "admin"}
    result = {}
    if not permissions_str:
        return result
    for perm in permissions_str.split(","):
        perm = perm.strip()
        if not perm:
            continue
        if perm not in valid_permissions:
            click.echo(
                f"Error: Unknown permission '{perm}'. Valid permissions: {', '.join(sorted(valid_permissions))}",
                err=True,
            )
            sys.exit(1)
        result[perm] = True
    return result


def _apply_flags_and_permissions(user, flags, permissions):
    if flags:
        user.email_confirmed = "email_confirmed" in flags
        user.is_approved = "approved" in flags

    if permissions:
        if "admin" in permissions:
            user.is_admin = True
            user.is_approved = True
            user.allow_read = True
            user.allow_write = True
            user.allow_upload = True
        else:
            user.is_admin = False
            user.allow_read = "read" in permissions
            user.allow_write = "write" in permissions
            user.allow_upload = "upload" in permissions

    return user


def _print_user_summary(user):
    perms = []
    if user.allow_read:
        perms.append("read")
    if user.allow_write:
        perms.append("write")
    if user.allow_upload:
        perms.append("upload")
    if user.is_admin:
        perms = ["admin"]

    click.echo(f"  Admin:          {'yes' if user.is_admin else 'no'}")
    click.echo(f"  Approved:       {'yes' if user.is_approved else 'no'}")
    click.echo(f"  Email confirmed:{'yes' if user.email_confirmed else 'no'}")
    click.echo(f"  Permissions:    {', '.join(perms) if perms else 'none'}")
    click.echo(f"  Password:       {'set' if user.password_hash else 'none'}")


@user_cli.command("create")
@click.argument("email")
@click.argument("name")
@click.option(
    "-f",
    "--flags",
    default=None,
    help="Comma-separated flags to set: email_confirmed, approved",
)
@click.option(
    "-p",
    "--permissions",
    default=None,
    help="Comma-separated permissions to grant: read, write, upload, admin",
)
def user_create(email, name, flags, permissions):
    """Create a new user account.

    EMAIL is the user's email address (required).
    NAME is the user's display name (required).

    The user will have no password set and cannot log in until a password
    is assigned via 'flask user password'.

    Examples:

        flask user create user@example.com "John Doe"

        flask user create user@example.com "John Doe" --flags=email_confirmed,approved --permissions=read,write

        flask user create admin@example.com "Admin User" -p admin
    """
    from otterwiki.auth import SimpleAuth

    if not is_valid_email(email):
        click.echo(f"Error: '{email}' is not a valid email address.", err=True)
        sys.exit(1)

    name_valid, name_reason = is_valid_name(name)
    if not name_valid:
        click.echo(f"Error: Invalid name - {name_reason}.", err=True)
        sys.exit(1)

    existing = SimpleAuth.User.query.filter_by(email=email.lower()).first()
    if existing is not None:
        click.echo(
            f"Error: A user with email '{email}' already exists.", err=True
        )
        sys.exit(1)

    parsed_flags = _parse_flags(flags)
    parsed_permissions = _parse_permissions(permissions)

    # create user without password (password_hash=None means cannot log in)
    user = SimpleAuth.User(  # pyright: ignore
        name=name,
        email=email.lower(),
        password_hash=None,
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        is_admin=False,
        is_approved=False,
        email_confirmed=False,
        allow_read=False,
        allow_write=False,
        allow_upload=False,
    )

    user = _apply_flags_and_permissions(user, parsed_flags, parsed_permissions)

    db.session.add(user)
    db.session.commit()

    click.echo(f"User '{name}' <{email.lower()}> created successfully.")
    _print_user_summary(user)


@user_cli.command("edit")
@click.argument("email")
@click.option(
    "--new-email", default=None, help="New email address for the user."
)
@click.option(
    "--new-name", default=None, help="New display name for the user."
)
@click.option(
    "-f",
    "--flags",
    default=None,
    help="Comma-separated flags to set: email_confirmed, approved",
)
@click.option(
    "-p",
    "--permissions",
    default=None,
    help="Comma-separated permissions to grant: read, write, upload, admin",
)
def user_edit(email, new_email, new_name, flags, permissions):
    """Edit an existing user account.

    EMAIL is the current email address of the user to edit (required).
    At least one of --new-email, --new-name, --flags, or --permissions must be provided.

    Note: --flags and --permissions OVERWRITE current values.

    Examples:

        flask user edit user@example.com --new-name="Jane Doe"

        flask user edit user@example.com --new-email=new@example.com

        flask user edit user@example.com --flags=email_confirmed,approved --permissions=read,write

        flask user edit user@example.com -p admin
    """
    from otterwiki.auth import SimpleAuth

    if (
        new_email is None
        and new_name is None
        and flags is None
        and permissions is None
    ):
        click.echo(
            "Error: At least one of --new-email, --new-name, --flags, or --permissions must be provided.",
            err=True,
        )
        sys.exit(1)

    user = _get_user(email)

    if new_email is not None:
        if not is_valid_email(new_email):
            click.echo(
                f"Error: '{new_email}' is not a valid email address.", err=True
            )
            sys.exit(1)
        existing = SimpleAuth.User.query.filter_by(
            email=new_email.lower()
        ).first()
        if existing is not None and existing.id != user.id:
            click.echo(
                f"Error: A user with email '{new_email}' already exists.",
                err=True,
            )
            sys.exit(1)
        user.email = new_email.lower()

    if new_name is not None:
        name_valid, name_reason = is_valid_name(new_name)
        if not name_valid:
            click.echo(f"Error: Invalid name - {name_reason}.", err=True)
            sys.exit(1)
        user.name = new_name

    parsed_flags = _parse_flags(flags)
    parsed_permissions = _parse_permissions(permissions)
    user = _apply_flags_and_permissions(user, parsed_flags, parsed_permissions)

    db.session.add(user)
    db.session.commit()

    click.echo(f"User '{user.name}' <{user.email}> updated successfully.")
    _print_user_summary(user)


@user_cli.command("password")
@click.argument("email")
@click.option(
    "--password-interactive",
    "-i",
    is_flag=True,
    default=False,
    help="Prompt for a new password.",
)
@click.option(
    "--send-password-reset",
    "-r",
    is_flag=True,
    default=False,
    help="Send a password reset email (requires mail server).",
)
@click.option(
    "--delete-password",
    "-d",
    is_flag=True,
    default=False,
    help="Unset the user's password so they cannot log in until a reset is requested.",
)
@click.option(
    "--generate-password",
    "-g",
    is_flag=True,
    default=False,
    help="Generate a secure 12-character password and print it.",
)
def user_password(
    email,
    password_interactive,
    send_password_reset,
    delete_password,
    generate_password,
):
    """Set or reset a user's password.

    EMAIL is the email address of the user (required).

    Exactly one of --password-interactive, --send-password-reset,
    --delete-password, or --generate-password must be provided.

    Examples:

        flask user password user@example.com --password-interactive

        flask user password user@example.com --send-password-reset

        flask user password user@example.com --delete-password

        flask user password user@example.com --generate-password

        flask user password user@example.com -i

        flask user password user@example.com -r

        flask user password user@example.com -d

        flask user password user@example.com -g
    """
    from werkzeug.security import generate_password_hash

    options_count = sum(
        [
            password_interactive,
            send_password_reset,
            delete_password,
            generate_password,
        ]
    )

    if options_count == 0:
        click.echo(
            "Error: Provide --password-interactive (-i), --send-password-reset (-r), --delete-password (-d), or --generate-password (-g).",
            err=True,
        )
        sys.exit(1)

    if options_count > 1:
        click.echo(
            "Error: --password-interactive, --send-password-reset, --delete-password, and --generate-password are mutually exclusive.",
            err=True,
        )
        sys.exit(1)

    user = _get_user(email)

    if delete_password:
        user.password_hash = None
        db.session.add(user)
        db.session.commit()
        click.echo(f"Password for '{user.email}' deleted successfully.")

    elif generate_password:
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = "".join(secrets.choice(alphabet) for _ in range(12))
        user.password_hash = generate_password_hash(password, method="scrypt")
        db.session.add(user)
        db.session.commit()
        click.echo(f"Password for '{user.email}' set to: {password}")

    elif password_interactive:
        while True:
            password1 = click.prompt("New password", hide_input=True, err=True)
            password2 = click.prompt(
                "Confirm password", hide_input=True, err=True
            )
            if password1 != password2:
                click.echo(
                    "Error: Passwords do not match. Try again.", err=True
                )
                continue
            if len(password1) < 8:
                click.echo(
                    "Error: Password must be at least 8 characters long. Try again.",
                    err=True,
                )
                continue
            break

        user.password_hash = generate_password_hash(password1, method="scrypt")
        db.session.add(user)
        db.session.commit()
        click.echo(f"Password for '{user.email}' updated successfully.")

    elif send_password_reset:
        mail_server = current_app.config.get("MAIL_SERVER", "")
        if not mail_server:
            click.echo(
                "Error: Mail server is not configured (MAIL_SERVER is empty). Cannot send password reset email.",
                err=True,
            )
            sys.exit(1)

        token = serialize(user.email, salt="lost-password-email")
        subject = "Password Recovery - {} - An Otter Wiki".format(
            current_app.config["SITE_NAME"]
        )
        text_body = render_template(
            "recover_password.txt",
            sitename=current_app.config["SITE_NAME"],
            name=user.name,
            url="{}/-/recover_password/{}".format(
                current_app.config.get("SERVER_NAME", "http://localhost"),
                token,
            ),
        )
        send_mail(
            subject=subject,
            recipients=[user.email],
            text_body=text_body,
            _async=False,
            raise_on_error=True,
        )
        click.echo(f"Password reset email sent to '{user.email}'.")


@user_cli.command("delete")
@click.argument("email")
@click.option(
    "--confirm",
    "-y",
    is_flag=True,
    default=False,
    help="Skip confirmation and delete immediately.",
)
def user_delete(email, confirm):
    """Delete a user account.

    EMAIL is the email address of the user to delete (required).

    Without --confirm, you will be asked to confirm the deletion.

    Examples:

        flask user delete user@example.com

        flask user delete user@example.com --confirm

        flask user delete user@example.com -y
    """
    user = _get_user(email)

    if not confirm:
        click.echo(f"About to delete user '{user.name}' <{user.email}>.")
        confirmed = click.confirm("Are you sure?", default=False)
        if not confirmed:
            click.echo("Deletion cancelled.")
            return

    db.session.delete(user)
    db.session.commit()
    click.echo(f"User '{user.name}' <{user.email}> deleted successfully.")


@user_cli.command("list")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output the user list in JSON format.",
)
def user_list(output_json):
    """List all user accounts.

    Displays a human-readable table of all users and their attributes,
    or JSON output if --json is specified.

    Examples:

        flask user list

        flask user list --json
    """
    from otterwiki.auth import SimpleAuth

    users = SimpleAuth.User.query.order_by(SimpleAuth.User.email).all()

    if not users:
        if output_json:
            click.echo("[]")
        else:
            click.echo("No users found.")
        return

    if output_json:
        user_data = []
        for u in users:
            user_data.append(
                {
                    "id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "is_admin": u.is_admin,
                    "is_approved": u.is_approved,
                    "email_confirmed": u.email_confirmed,
                    "allow_read": u.allow_read,
                    "allow_write": u.allow_write,
                    "allow_upload": u.allow_upload,
                    "has_password": u.password_hash is not None,
                    "first_seen": (
                        u.first_seen.isoformat() if u.first_seen else None
                    ),
                    "last_seen": (
                        u.last_seen.isoformat() if u.last_seen else None
                    ),
                }
            )
        click.echo(json.dumps(user_data, indent=2))
    else:
        # human-readable table
        col_widths = {
            "email": max(len("Email"), max(len(u.email or "") for u in users)),
            "name": max(len("Name"), max(len(u.name or "") for u in users)),
        }

        header = (
            f"{'Email':<{col_widths['email']}}  "
            f"{'Name':<{col_widths['name']}}  "
            f"{'Admin':<5}  "
            f"{'Approved':<8}  "
            f"{'Confirmed':<9}  "
            f"{'Permissions':<12}  "
            f"{'Password':<8}"
        )
        separator = "-" * len(header)

        click.echo(separator)
        click.echo(header)
        click.echo(separator)

        for u in users:
            perms = []
            if u.allow_read:
                perms.append("read")
            if u.allow_write:
                perms.append("write")
            if u.allow_upload:
                perms.append("upload")
            if u.is_admin:
                perms = ["admin"]
            perms_str = ",".join(perms) if perms else "-"

            row = (
                f"{u.email or '':<{col_widths['email']}}  "
                f"{u.name or '':<{col_widths['name']}}  "
                f"{'yes' if u.is_admin else 'no':<5}  "
                f"{'yes' if u.is_approved else 'no':<8}  "
                f"{'yes' if u.email_confirmed else 'no':<9}  "
                f"{perms_str:<12}  "
                f"{'set' if u.password_hash else 'not set':<8}"
            )
            click.echo(row)

        click.echo(separator)
        click.echo(f"Total: {len(users)} user(s)")


app.cli.add_command(user_cli)
