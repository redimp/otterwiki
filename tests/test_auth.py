# /usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import re
from flask import url_for


def test_create_app_with_user(app_with_user):
    test_client = app_with_user.test_client()
    result = test_client.get("/")
    assert "<!DOCTYPE html>" in result.data.decode()
    assert "<title>" in result.data.decode()
    assert "</html>" in result.data.decode()


def test_db(app_with_user):
    from otterwiki.auth import SimpleAuth, check_password_hash, db

    # check that table 'user' exists
    from sqlalchemy import inspect

    inspector = inspect(db.engine)
    assert "user" in [str(x) for x in inspector.get_table_names()]

    # query all user
    all_user = SimpleAuth.User.query.all()
    assert len(all_user) == 2

    # query created user
    user = SimpleAuth.User.query.filter_by(email="mail@example.org").first()
    assert user is not None
    assert user.email == "mail@example.org"
    assert user.name == "Test User"
    # check hash
    assert True is check_password_hash(user.password_hash, "password1234")


def test_generate_and_check_hash(create_app):
    from otterwiki.auth import generate_password_hash, check_password_hash

    for password in ["abc123.!äüöß", "aedaiPaesh8ie5Iu", "┳━┳ ヽ(ಠل͜ಠ)ﾉ"]:
        for method in ["scrypt"]:
            hash = generate_password_hash(password, method=method)
            assert True is check_password_hash(hash, password)


def test_check_password_hash_backport(create_app):
    from otterwiki.auth import (
        generate_password_hash,
        check_password_hash_backport,
    )

    # make sure check_password_hash still works sice sha256/sha512 password methods
    # are deprecated and will be removed in Werkzeug 3.0 to not break existing
    # installations
    for passwd, pwhash in [
        (
            "abc123.!äüöß",
            "sha256$AuvUmsdieyFfazrT$c5f6f1efe98ed5590dee4971345e57f54da33f277e1e00e558fdc3749dc1aa4d",
        ),
        (
            "aedaiPaesh8ie5Iu",
            "sha256$sF2obN32d4OkvmLs$cfb90dab3c2250791eaae6f9ece94a8f1eb79d2dc04d535801e15c53ac66305b",
        ),
        (
            "┳━┳ ヽ(ಠل͜ಠ)ﾉ",
            "sha256$OEPGu0fDDZSvlEhZ$6af38560ea7a07d93e66105a02babca6a179f7c96dd1a3c42a7fca77bc2d09be",
        ),
        (
            "abc123.!äüöß",
            "sha512$8hycondShwRbmPT7$8fe00313e3ae05eb788dcd24a7fb577442c3eb31c60bf4a66acb92868187425db0f3e3af07b0e76726930e4012b5b8488d23f28ac16f18a7790c066c94727954",
        ),
        (
            "aedaiPaesh8ie5Iu",
            "sha512$JbDiZmPuzsOuHQLZ$57a18fa3eb3c9f93d0d8e6d5c460e9e14cbcefdb8c36fb7bbb4a24b0f61a8e9674e09172a4ee8dce40de79d64f7fddd8addc46b881f2fbb837be46402198ae14",
        ),
        (
            "┳━┳ ヽ(ಠل͜ಠ)ﾉ",
            "sha512$5aG970kGxIx1lKp0$2f54f96e4e68020c0ba5780b0b882979dd3ce79eabd34b40b4fce8da215ea018dba5c2f71015a0051ad798106f4e5fdbd40c6589ea4e4b260555daf205f9accc",
        ),
        (
            "abc123.!äüöß",
            "scrypt:32768:8:1$jTNi3RiP3DuKPgrX$7d6c11df590d60ac9b96837a43bbd57dbc2bf5958e4ef316dc7214fa87e60849883fc090265bbd2910659c527d51c17815e4f79bff8b3458f6925f1f07905ce7",
        ),
        (
            "aedaiPaesh8ie5Iu",
            "scrypt:32768:8:1$m1S6sWOQ7GK1zDpM$14368587b86036a44835ac6f1775b36e6ad217a7a895c4e41ff3b087bab5222da982a79bae540868b7d01bdf6e952545196bbba8866b3f6d69153abd0cdb46a1",
        ),
        (
            "┳━┳ ヽ(ಠل͜ಠ)ﾉ",
            "scrypt:32768:8:1$R4Tk2yLvwsIXIJqa$f298715f1ae4242014779d45a4fb509f59f49f347708039698023f8a9c7513e3ed68471b6282c2ca5f3d9f56213b404117e0fb5c8f395853ed5acd9ec17f10df",
        ),
    ]:
        assert True is check_password_hash_backport(pwhash, passwd)


def test_minimal_auth(app_with_user):
    # check auth defaults
    assert app_with_user.config.get("AUTH_METHOD") == ""


def login(client):
    return client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "password1234",
        },
        follow_redirects=True,
    )


def test_login(app_with_user, test_client):
    result = login(test_client)
    html = result.data.decode()
    assert "You logged in successfully." in html


def test_login_fail_without_app(test_client):
    html = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "",
        },
        follow_redirects=True,
    ).data.decode()
    assert "Invalid email address or password." in html


def test_login_fail_wrong_username(app_with_user, test_client):
    html = test_client.post(
        "/-/login",
        data={
            "email": "x@x.x",
            "password": "",
        },
        follow_redirects=True,
    ).data.decode()
    assert "Invalid email address or password." in html


def test_login_fail_wrong_password(app_with_user, test_client):
    html = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "xxx",
        },
        follow_redirects=True,
    ).data.decode()
    assert "Invalid email address or password." in html


def test_logout(test_client):
    result = login(test_client)
    html = test_client.get(
        "/-/logout",
        follow_redirects=True,
    ).data.decode()
    assert "You logged out successfully." in html


def test_login_required(test_client):
    html = test_client.get(
        "/-/settings",
        follow_redirects=True,
    ).data.decode()
    assert "Change Password" not in html
    assert "Please log in to access this page." in html


def test_settins_minimal(app_with_user, test_client):
    result = login(test_client)
    html = test_client.get(
        "/-/settings",
        follow_redirects=True,
    ).data.decode()
    assert "Change Password" in html


#
# test permissions
#
@pytest.fixture
def app_with_permissions(app_with_user, test_client):
    app_with_user.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_user.config["WRITE_ACCESS"] = "ANONYMOUS"
    # create a Home
    html = test_client.post(
        "/Home/save",
        data={
            "content": "There is no place like Home.",
            "commit": "Home: initial test commit.",
        },
        follow_redirects=True,
    ).data.decode()
    html = test_client.get("/Home").data.decode()
    assert "There is no place like Home." in html
    # update permissions
    app_with_user.config["READ_ACCESS"] = "REGISTERED"
    # and fetch again
    html = test_client.get("/Home").data.decode()
    assert "There is no place like Home." not in html

    with app_with_user.test_request_context() as ctx:
        yield app_with_user


def test_page_view_permissions(app_with_permissions, test_client):
    fun = "view"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun, path="Home"))
    assert "There is no place like Home." in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun, path="Home"), follow_redirects=True)
    assert "There is no place like Home." not in rv.data.decode()
    # check for the toast
    assert "lack the permissions to access" in rv.data.decode()
    # check for the login form
    assert url_for("login") in rv.data.decode()
    assert 'name="password"' in rv.data.decode()
    assert rv.status_code == 200
    login(test_client)
    rv = test_client.get(url_for(fun, path="Home"))
    assert "There is no place like Home." in rv.data.decode()
    assert rv.status_code == 200


def test_page_blame_permissions(app_with_permissions, test_client):
    fun = "blame"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "There is no place like Home." in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 302
    assert "/-/login" in rv.location
    login(test_client)
    rv = test_client.get(url_for(fun, path="Home"))
    assert "There is no place like Home." in rv.data.decode()


def test_page_history_permissions(app_with_permissions, test_client):
    fun = "history"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "initial test commit" in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 302
    assert "/-/login" in rv.location
    login(test_client)
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "initial test commit" in rv.data.decode()


def test_page_index_permissions(app_with_permissions, test_client):
    fun = "pageindex"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun))
    assert rv.status_code == 200
    assert "Page Index" in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun))
    assert rv.status_code == 302
    assert "/-/login" in rv.location
    login(test_client)
    rv = test_client.get(url_for(fun))
    assert rv.status_code == 200
    assert "Page Index" in rv.data.decode()


def test_page_changelog_permissions(app_with_permissions, test_client):
    fun = "changelog"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "initial test commit" in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 302
    assert "/-/login" in rv.location
    login(test_client)
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "initial test commit" in rv.data.decode()


def test_page_edit_permissions(app_with_permissions, test_client):
    # update permissions
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_permissions.config["WRITE_ACCESS"] = "ANONYMOUS"
    # helper
    pagename = "RandomEdit"
    # try to edit anonymous
    rv = test_client.get(url_for("edit", path=pagename))
    assert rv.status_code == 200
    html = rv.data.decode()
    # check that there is an editor in the html
    assert "<textarea" in html
    # update permissions
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    app_with_permissions.config["WRITE_ACCESS"] = "REGISTERED"
    # try edit
    rv = test_client.get(url_for("edit", path=pagename))
    html = rv.data.decode()
    # check that there is an editor in the html
    assert rv.status_code == 403
    assert "<textarea" not in html
    # login
    login(test_client)
    # try edit
    rv = test_client.get(url_for("edit", path=pagename))
    html = rv.data.decode()
    assert rv.status_code == 200
    assert "<textarea" in html


def test_page_save_permissions(app_with_permissions, test_client):
    # update permissions
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_permissions.config["WRITE_ACCESS"] = "ANONYMOUS"
    # helper
    pagename = "RandomSaveTest"
    content = "Random Content"
    # try to edit anonymous
    rv = test_client.post(
        url_for("save", path=pagename),
        data={
            "content": content,
            "commit": "Home: initial test commit.",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert content in rv.data.decode()
    # change permissions
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    app_with_permissions.config["WRITE_ACCESS"] = "REGISTERED"
    # try to edit anonymous (and fail)
    rv = test_client.post(
        url_for("save", path=pagename),
        data={
            "content": content,
            "commit": "Home: initial test commit.",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 403
    # try to create (and fail)
    rv = test_client.post("/-/create", data={"pagename": "example"})
    assert rv.status_code == 403


def test_page_revert_permissions(app_with_permissions, test_client):
    # update permissions
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_permissions.config["WRITE_ACCESS"] = "ANONYMOUS"
    # helper
    pagename = "Random Revert Test 0"
    old_content = "Random Content 0"
    # try to edit anonymous
    rv = test_client.post(
        url_for("save", path=pagename),
        data={
            "content": old_content,
            "commit": "initial test commit.",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert old_content in rv.data.decode()
    # test view
    html = test_client.get("/{}/view".format(pagename)).data.decode()
    assert old_content in html
    # update content
    content = "Random Content 1"
    rv = test_client.post(
        url_for("save", path=pagename),
        data={
            "content": content,
            "commit": "updated content.",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert content in rv.data.decode()

    # find revision
    rv = test_client.get("/{}/history".format(pagename))
    html = rv.data.decode()
    revisions = re.findall(
        r"class=\"btn revision-small\">([A-z0-9]+)</a>", html
    )
    assert len(revisions) == 2
    latest_revision = revisions[0]

    # change permissions
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    app_with_permissions.config["WRITE_ACCESS"] = "REGISTERED"

    # try to revert non existing commit
    rv = test_client.get("/-/revert/{}".format(0000000))
    assert rv.status_code == 403

    # try revert form
    rv = test_client.get("/-/revert/{}".format(latest_revision))
    assert rv.status_code == 403
    # try to revert latest commit
    rv = test_client.post("/-/revert/{}".format(latest_revision))
    assert rv.status_code == 403

    # change permissions again
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_permissions.config["WRITE_ACCESS"] = "ANONYMOUS"

    # check revert form
    rv = test_client.get("/-/revert/{}".format(latest_revision))
    html = rv.data.decode()
    assert rv.status_code == 200
    assert "Revert commit [{}]".format(latest_revision) in html

    # try to revert latest commit
    rv = test_client.post(
        "/-/revert/{}".format(latest_revision), follow_redirects=True
    )
    assert rv.status_code == 200

    # check if content changed
    html = test_client.get("/{}/view".format(pagename)).data.decode()
    assert old_content in html


def test_permissions_per_user(app_with_permissions, test_client):
    fun = "view"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun, path="Home"))
    assert "There is no place like Home." in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "ADMIN"
    app_with_permissions.config["WRITE_ACCESS"] = "ADMIN"
    app_with_permissions.config["ATTACHMENT_ACCESS"] = "ADMIN"
    rv = test_client.get(url_for(fun, path="Home"), follow_redirects=True)
    assert "There is no place like Home." not in rv.data.decode()
    # check for the toast
    assert "lack the permissions to access" in rv.data.decode()

    rv = test_client.post(
        "/-/login",
        data={
            "email": "another@user.org",
            "password": "password4567",
        },
        follow_redirects=True,
    )

    assert "You logged in successfully" in rv.data.decode()
    assert "You are logged in but lack READ permissions." in rv.data.decode()
    assert "There is no place like Home." not in rv.data.decode()
    # grant the user read_access
    from otterwiki.auth import SimpleAuth, db

    user = SimpleAuth.User.query.filter_by(email="another@user.org").first()
    assert user is not None
    user.allow_read = True
    db.session.add(user)
    db.session.commit()
    # check if the read_access works
    rv = test_client.get(url_for(fun, path="Home"), follow_redirects=True)
    assert "There is no place like Home." in rv.data.decode()
    # try to save
    rv = test_client.post(
        url_for("save", path="SaveTest"),
        data={
            "content": "Another save test",
            "commit": "test commit.",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 403
    user = SimpleAuth.User.query.filter_by(email="another@user.org").first()
    assert user is not None
    user.allow_write = True
    db.session.add(user)
    db.session.commit()
    # try to save
    rv = test_client.post(
        url_for("save", path="SaveTest"),
        data={
            "content": "Another save test",
            "commit": "test commit.",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    # restore permissions
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_permissions.config["WRITE_ACCESS"] = "ANONYMOUS"
    app_with_permissions.config["ATTACHMENT_ACCESS"] = "ANONYMOUS"


#
# lost_password
#
def test_lost_password_form(test_client):
    rv = test_client.get("/-/lost_password")
    assert rv.status_code == 200


def test_lost_password_mail(app_with_user, test_client, req_ctx):
    # workaround since MAIL_SUPPRESS_SEND doesn't work as expected
    app_with_user.test_mail.state.suppress = True
    # record outbox
    with app_with_user.test_mail.record_messages() as outbox:
        assert len(outbox) == 0
        rv = test_client.post(
            "/-/lost_password",
            data={
                "email": "mail@example.org",
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200
        assert len(outbox) == 1
        assert "Password Recovery" in outbox[0].subject
        assert "/-/recover_password/" in outbox[0].body
        assert "mail@example.org" in outbox[0].recipients
        # find token
        m = re.search(
            r"\/-\/recover_password\/(\S+)", outbox[0].body, flags=re.MULTILINE
        )
        assert m is not None
        token = m.group(1)
        assert len(token) > 0
        # test token
        rv = test_client.get(
            f"/-/recover_password/{token}",
            follow_redirects=True,
        )
        assert "please update your password." in rv.data.decode()


def test_lost_password_form_address(app_with_user, test_client):
    rv = test_client.post(
        "/-/lost_password",
        data={
            "email": "invalidmail@",
        },
        follow_redirects=True,
    )
    assert "This email address is invalid." in rv.data.decode()
    rv = test_client.post(
        "/-/lost_password",
        data={
            "email": "nonexistent@email.address",
        },
        follow_redirects=True,
    )
    assert (
        "If this email is registered, you will receive a password reset link."
        in rv.data.decode()
    )


def test_lost_password_invalid_token(app_with_user, test_client):
    rv = test_client.get(
        "/-/recover_password/invalidtoken",
        follow_redirects=True,
    )
    assert "Invalid token." in rv.data.decode()

    from otterwiki.helper import serialize

    # generate token
    token = serialize("nonexistent@email.address", salt="lost-password-email")
    rv = test_client.get(
        f"/-/recover_password/{token}",
        follow_redirects=True,
    )
    assert "Invalid email address." in rv.data.decode()


def test_lost_password_token_reuse(app_with_user, test_client, req_ctx):
    """Password reset token must be single-use — second use is rejected."""
    app_with_user.test_mail.state.suppress = True
    with app_with_user.test_mail.record_messages() as outbox:
        # Step 1: Request password reset
        rv = test_client.post(
            "/-/lost_password",
            data={"email": "mail@example.org"},
            follow_redirects=True,
        )
        assert len(outbox) == 1
        # Extract token from email
        m = re.search(
            r"\/-\/recover_password\/(\S+)", outbox[0].body, flags=re.MULTILINE
        )
        assert m is not None
        token = m.group(1)

        # Step 2: First use — should succeed (logs in, redirects to settings)
        rv = test_client.get(
            f"/-/recover_password/{token}",
            follow_redirects=True,
        )
        assert "please update your password." in rv.data.decode()

        # Log out so we can test the token again
        test_client.get("/-/logout")

        # Step 3: Second use of same token — should be rejected
        rv = test_client.get(
            f"/-/recover_password/{token}",
            follow_redirects=True,
        )
        result = rv.data.decode()
        # Token must be rejected — should NOT see the success message
        assert "please update your password." not in result
        # Should see an error/rejection message
        assert (
            "Invalid" in result
            or "expired" in result
            or "already used" in result
        )


#
# register
#
def test_register_and_login(app_with_user, test_client, req_ctx):
    app_with_user.config["EMAIL_NEEDS_CONFIRMATION"] = False
    app_with_user.config["AUTO_APPROVAL"] = True
    # workaround since MAIL_SUPPRESS_SEND doesn't work as expected
    app_with_user.test_mail.state.suppress = True
    email = "mail2@example.org"
    password = "1234567890"

    rv = test_client.post(
        "/-/register",
        data={
            "email": email,
            "name": "Example User",
            "password1": password,
            "password2": password,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # test login with new account
    rv = test_client.post(
        "/-/login",
        data={
            "email": email,
            "password": password,
        },
        follow_redirects=True,
    )
    html = rv.data.decode()
    assert "You logged in successfully." in html


def test_register_and_confirm(app_with_user, test_client, req_ctx):
    app_with_user.config["EMAIL_NEEDS_CONFIRMATION"] = True
    # workaround since MAIL_SUPPRESS_SEND doesn't work as expected
    app_with_user.test_mail.state.suppress = True
    # record outbox
    with app_with_user.test_mail.record_messages() as outbox:
        email = "mail3@example.org"
        password = "1234567890"
        assert len(outbox) == 0
        rv = test_client.post(
            "/-/register",
            data={
                "email": email,
                "name": "Example User",
                "password1": password,
                "password2": password,
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200

        # check if account is unconfirmed
        rv = test_client.post(
            "/-/login",
            data={
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )
        html = rv.data.decode()
        assert "You logged in successfully." not in html

        # check mail
        assert len(outbox) == 1
        assert "confirm" in outbox[0].subject.lower()
        assert "/-/confirm_email/" in outbox[0].body
        assert email in outbox[0].recipients
        # find token
        token = re.findall("confirm_email/(.*)", outbox[0].body)[0]
        # check if confirm token works
        rv = test_client.get(
            "/-/confirm_email/{}".format(token),
            follow_redirects=True,
        )
        assert rv.status_code == 200
        assert (
            "Your email address has been confirmed. You can log in now."
            in rv.data.decode()
        )
        # check if account is confirmed now
        rv = test_client.post(
            "/-/login",
            data={
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )
        html = rv.data.decode()
        assert "You logged in successfully." in html


def test_register_errors(app_with_user, test_client, req_ctx):
    # test invalid mail
    rv = test_client.post(
        "/-/register",
        data={
            "email": "john",
            "name": "",
            "password1": "",
            "password2": "",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "email address is invalid" in rv.data.decode()
    assert "account has been created" not in rv.data.decode()
    assert "account is waiting for approval" not in rv.data.decode()
    # test existing email
    rv = test_client.post(
        "/-/register",
        data={
            "email": "mail@example.org",
            "name": "",
            "password1": "",
            "password2": "",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "already registered" in rv.data.decode()
    assert "account has been created" not in rv.data.decode()
    assert "account is waiting for approval" not in rv.data.decode()
    # invalid name
    rv = test_client.post(
        "/-/register",
        data={
            "email": "mail@example.com",
            "name": "Click for discount drugs: http://example.com/uri",
            "password1": "",
            "password2": "",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert (
        "name can only contain letters, spaces, hyphens, apostrophes, and periods"
        in rv.data.decode()
    )
    assert "account has been created" not in rv.data.decode()
    assert "account is waiting for approval" not in rv.data.decode()
    # empty name
    rv = test_client.post(
        "/-/register",
        data={
            "email": "mail@example.com",
            "name": "",
            "password1": "",
            "password2": "",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "enter your name" in rv.data.decode()
    assert "account has been created" not in rv.data.decode()
    assert "account is waiting for approval" not in rv.data.decode()
    # passwords not match
    rv = test_client.post(
        "/-/register",
        data={
            "email": "mail@example.com",
            "name": "John Doe",
            "password1": "123456789",
            "password2": "12345678",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "passwords do not match" in rv.data.decode()
    assert "account has been created" not in rv.data.decode()
    assert "account is waiting for approval" not in rv.data.decode()
    # passwords not match
    rv = test_client.post(
        "/-/register",
        data={
            "email": "mail@example.com",
            "name": "John Doe",
            "password1": "1234567",
            "password2": "1234567",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "password must be at least" in rv.data.decode()
    assert "account has been created" not in rv.data.decode()
    assert "account is waiting for approval" not in rv.data.decode()


def test_user_with_empty_password_issues_204_205(app_with_user, test_client):
    from otterwiki.auth import SimpleAuth, db
    from datetime import datetime

    email = "empty@example.org"

    # create a user with empty password field
    user = SimpleAuth.User(  # pyright: ignore
        name="Test User E",  # pyright: ignore
        email=email,  # pyright: ignore
        password_hash=None,  # pyright: ignore
        first_seen=datetime.now(),  # pyright: ignore
        last_seen=datetime.now(),  # pyright: ignore
        is_admin=False,  # pyright: ignore
    )
    db.session.add(user)
    db.session.commit()

    rv = test_client.post(
        "/-/login",
        data={
            "email": email,
            "password": "",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # workaround since MAIL_SUPPRESS_SEND doesn't work as expected
    app_with_user.test_mail.state.suppress = True
    # record outbox
    with app_with_user.test_mail.record_messages() as outbox:
        assert len(outbox) == 0
        rv = test_client.post(
            "/-/lost_password",
            data={
                "email": email,
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200
        assert len(outbox) == 1
        assert "Password Recovery" in outbox[0].subject
        assert "/-/recover_password/" in outbox[0].body
        assert email in outbox[0].recipients
        # find token
        m = re.search(
            r"\/-\/recover_password\/(\S+)", outbox[0].body, flags=re.MULTILINE
        )
        assert m is not None
        token = m.group(1)
        assert len(token) > 0
        # test token
        rv = test_client.get(
            f"/-/recover_password/{token}",
            follow_redirects=True,
        )
        assert "please update your password." in rv.data.decode()


def test_register_first_user(create_app, test_client, req_ctx):
    """
    This test verifies that the first user that is registered becomes admin.
    """
    from otterwiki.auth import SimpleAuth, db

    first_email = "admin@example.com"
    second_email = "random@example.com"
    password = "password1234"

    db.session.query(SimpleAuth.User).delete()
    # check users to make sure we start from scratch
    assert len(SimpleAuth.User.query.all()) == 0
    create_app.config["ADMIN_USER_EMAIL"] = ""

    # Register random_email
    rv = test_client.post(
        "/-/register",
        data={
            "email": first_email,
            "name": "Admin User",
            "password1": password,
            "password2": password,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    # Register admin email
    rv = test_client.post(
        "/-/register",
        data={
            "email": second_email,
            "name": "Random User",
            "password1": password,
            "password2": password,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    admin_user = SimpleAuth.User.query.filter_by(email=first_email).first()
    assert admin_user
    assert admin_user.is_admin is True
    random_user = SimpleAuth.User.query.filter_by(email=second_email).first()
    assert random_user
    assert random_user.is_admin is False
    # clean up
    db.session.query(SimpleAuth.User).delete()
    create_app.config["ADMIN_USER_EMAIL"] = ""


def test_register_first_admin_user_email(create_app, test_client, req_ctx):
    """
    This test verifies that with ADMIN_USER_EMAIL configured only user with
    this email gets admin permissions
    """
    from otterwiki.auth import SimpleAuth, db

    admin_email = "admin@example.com"
    random_email = "random@example.com"
    password = "password1234"

    db.session.query(SimpleAuth.User).delete()
    # check users to make sure we start from scratch
    assert len(SimpleAuth.User.query.all()) == 0
    create_app.config["ADMIN_USER_EMAIL"] = admin_email

    # Register random_email
    rv = test_client.post(
        "/-/register",
        data={
            "email": random_email,
            "name": "Random User",
            "password1": password,
            "password2": password,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    # Register admin email
    rv = test_client.post(
        "/-/register",
        data={
            "email": admin_email,
            "name": "Admin User",
            "password1": password,
            "password2": password,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    admin_user = SimpleAuth.User.query.filter_by(email=admin_email).first()
    assert admin_user
    assert admin_user.is_admin is True
    random_user = SimpleAuth.User.query.filter_by(email=random_email).first()
    assert random_user
    assert random_user.is_admin is False
    # clean up
    db.session.query(SimpleAuth.User).delete()
    create_app.config["ADMIN_USER_EMAIL"] = ""


def test_register_first_admin_user_email_disabled(
    create_app, test_client, req_ctx
):
    """
    This test verifies that even with ADMIN_USER_EMAIL configured
    a user with this email does not get admin acccess if another admin is already registered.
    This prevents edge cases where old admin users have been deleted and the config is forgotten.
    """
    from otterwiki.auth import SimpleAuth, db

    admin_email = "admin@example.com"
    random_email = "random@example.com"
    password = "password1234"

    db.session.query(SimpleAuth.User).delete()
    # check users to make sure we start from scratch
    assert len(SimpleAuth.User.query.all()) == 0

    create_app.config["ADMIN_USER_EMAIL"] = ""
    # Register random_email
    rv = test_client.post(
        "/-/register",
        data={
            "email": random_email,
            "name": "Random User",
            "password1": password,
            "password2": password,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # enable ADMIN_USER_EMAIL, must have no effect since random_email already is admin
    create_app.config["ADMIN_USER_EMAIL"] = admin_email
    # Register admin email
    rv = test_client.post(
        "/-/register",
        data={
            "email": admin_email,
            "name": "Admin User",
            "password1": password,
            "password2": password,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    admin_user = SimpleAuth.User.query.filter_by(email=admin_email).first()
    assert admin_user
    assert admin_user.is_admin is False
    random_user = SimpleAuth.User.query.filter_by(email=random_email).first()
    assert random_user
    assert random_user.is_admin is True
    # clean up
    db.session.query(SimpleAuth.User).delete()
    create_app.config["ADMIN_USER_EMAIL"] = ""


def test_login_redirect_next_parameter(app_with_user):
    """Test that unauthenticated users are redirected to login with ?next="""
    test_client = app_with_user.test_client()
    # access a @login_required page without being logged in
    rv = test_client.get("/-/settings", follow_redirects=False)
    assert rv.status_code == 302
    location = rv.headers["Location"]
    assert "/-/login" in location
    assert "next=" in location
    assert "%2F-%2Fsettings" in location or "/-/settings" in location


def test_login_next_shown_in_form(app_with_user):
    """Test that the login form includes the next parameter."""
    test_client = app_with_user.test_client()
    rv = test_client.get("/-/login?next=%2F-%2Fsettings")
    assert rv.status_code == 200
    html = rv.data.decode()
    # the next value should be present in a hidden form field
    assert "/-/settings" in html


def test_login_redirects_to_next_after_login(app_with_user):
    """Test that after login the user is redirected to the next page."""
    test_client = app_with_user.test_client()
    rv = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "password1234",
            "next": "/-/settings",
        },
        follow_redirects=False,
    )
    assert rv.status_code == 302
    location = rv.headers["Location"]
    assert "/-/settings" in location


def test_login_next_ignores_external_url(app_with_user):
    """Test that external URLs in next are ignored (open redirect protection)."""
    test_client = app_with_user.test_client()
    rv = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "password1234",
            "next": "http://evil.example.com/steal",
        },
        follow_redirects=False,
    )
    assert rv.status_code == 302
    location = rv.headers["Location"]
    # must not redirect to the external URL
    assert "evil.example.com" not in location


def test_login_next_empty_redirects_to_index(app_with_user):
    """Test that an empty next value redirects to the index."""
    test_client = app_with_user.test_client()
    rv = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "password1234",
            "next": "",
        },
        follow_redirects=False,
    )
    assert rv.status_code == 302
    location = rv.headers["Location"]
    assert location.endswith("/")


def test_login_next_preserved_on_failed_login(app_with_user):
    """Test that the next parameter is preserved when login fails."""
    test_client = app_with_user.test_client()
    rv = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "wrongpassword",
            "next": "/-/settings",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "/-/settings" in html
    assert "Invalid email address or password." in html


def test_login_next_full_flow(app_with_user):
    """Test the full flow: access protected page -> login -> redirected back."""
    test_client = app_with_user.test_client()
    # step 1: access protected page, get redirected to login
    rv = test_client.get("/-/settings", follow_redirects=False)
    assert rv.status_code == 302
    login_url = rv.headers["Location"]
    assert "/-/login" in login_url

    # step 2: follow redirect to login page
    rv = test_client.get(login_url)
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "/-/settings" in html

    # step 3: submit login with next parameter
    rv = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "password1234",
            "next": "/-/settings",
        },
        follow_redirects=False,
    )
    assert rv.status_code == 302
    assert "/-/settings" in rv.headers["Location"]

    # step 4: follow redirect to the original page
    rv = test_client.get(rv.headers["Location"])
    assert rv.status_code == 200


#
# rate limiting tests
#
@pytest.fixture
def ratelimit_client(app_with_user):
    """Test client with rate limiting enabled for testing rate limit behavior."""
    from otterwiki.server import limiter

    app_with_user.config["RATELIMIT_ENABLED"] = True
    old_got_first_request = app_with_user._got_first_request
    app_with_user._got_first_request = False
    limiter.init_app(app_with_user)
    app_with_user._got_first_request = old_got_first_request
    limiter.reset()
    client = app_with_user.test_client()
    yield client
    limiter.reset()
    limiter.enabled = False
    app_with_user.config["RATELIMIT_ENABLED"] = False
    app_with_user.config["RATELIMIT_ENABLED"] = False


def test_login_ratelimit(ratelimit_client):
    """POST /-/login is rate limited to 10/minute; 11th request returns 429 with error message."""
    for i in range(10):
        result = ratelimit_client.post(
            "/-/login",
            data={"email": "mail@example.org", "password": "wrongpassword"},
            follow_redirects=False,
        )
        assert result.status_code != 429, f"Request {i + 1} was rate limited"
    result = ratelimit_client.post(
        "/-/login",
        data={"email": "mail@example.org", "password": "wrongpassword"},
        follow_redirects=False,
    )
    assert result.status_code == 429
    assert b"Too many attempts" in result.data


def test_lost_password_ratelimit(ratelimit_client):
    """POST /-/lost_password is rate limited to 5/minute; 6th request returns 429 with error message."""
    for i in range(5):
        result = ratelimit_client.post(
            "/-/lost_password",
            data={"email": "mail@example.org"},
            follow_redirects=False,
        )
        assert result.status_code != 429, f"Request {i + 1} was rate limited"
    result = ratelimit_client.post(
        "/-/lost_password",
        data={"email": "mail@example.org"},
        follow_redirects=False,
    )
    assert result.status_code == 429
    assert b"Too many attempts" in result.data


def test_login_get_not_ratelimited(ratelimit_client):
    """GET /-/login is never rate limited (only POST is)."""
    for i in range(50):
        result = ratelimit_client.get("/-/login")
        assert result.status_code in (
            200,
            302,
        ), f"GET request {i + 1} returned unexpected status {result.status_code}"


def test_ratelimit_disabled_in_tests(app_with_user):
    """With RATELIMIT_ENABLED=False (test default), rate limits are not enforced."""
    client = app_with_user.test_client()
    for i in range(20):
        result = client.post(
            "/-/login",
            data={"email": "mail@example.org", "password": "wrongpassword"},
            follow_redirects=False,
        )
        assert (
            result.status_code != 429
        ), f"Request {i + 1} was rate limited despite RATELIMIT_ENABLED=False"
