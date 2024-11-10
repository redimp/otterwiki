#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

from datetime import datetime
from bs4 import BeautifulSoup


def test_admin_form(admin_client):
    rv = admin_client.get("/-/admin")
    assert rv.status_code == 200


def test_preferences_testmail(app_with_user, admin_client):
    # workaround since MAIL_SUPPRESS_SEND doesn't work as expected
    app_with_user.test_mail.state.suppress = True
    # record outbox
    with app_with_user.test_mail.record_messages() as outbox:
        rv = admin_client.post(
            "/-/admin/mail_preferences",
            data={
                "mail_recipient": "",
                "test_mail_preferences": "true",
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200
        assert len(outbox) == 1
        assert "test mail" in outbox[0].subject.lower()
        assert "mail@example.org" in outbox[0].recipients

    with app_with_user.test_mail.record_messages() as outbox:
        rv = admin_client.post(
            "/-/admin/mail_preferences",
            data={
                "mail_recipient": "mail2@example.org",
                "test_mail_preferences": "true",
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200
        assert len(outbox) == 1
        assert "test mail" in outbox[0].subject.lower()
        assert "mail2@example.org" in outbox[0].recipients

    with app_with_user.test_mail.record_messages() as outbox:
        rv = admin_client.post(
            "/-/admin/mail_preferences",
            data={
                "mail_recipient": "example.org",
                "test_mail_preferences": "true",
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()
        assert "invalid email address" in html.lower()


def test_update_preferences(app_with_user, admin_client):
    new_name = "Test Wiki 4711"
    new_description = "another Test Wiki 4711"
    assert app_with_user.config['SITE_NAME'] != new_name
    assert app_with_user.config['SITE_DESCRIPTION'] != new_description
    rv = admin_client.post(
        "/-/admin",
        data={
            "site_name": new_name,
            "site_description": new_description,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert app_with_user.config['SITE_NAME'] == new_name
    assert app_with_user.config['SITE_DESCRIPTION'] == new_description
    assert app_with_user.config['SITE_LOGO'] == ""
    assert app_with_user.config['SITE_ICON'] == ""


def test_update_preferences_logo_and_icon(app_with_user, admin_client):
    new_logo = '/Home/a/logo.png'
    new_icon = '/Random/a/favicon.png'
    assert app_with_user.config['SITE_LOGO'] != new_logo
    assert app_with_user.config['SITE_ICON'] != new_icon
    rv = admin_client.post(
        "/-/admin",
        data={
            "site_logo": new_logo,
            "site_icon": new_icon,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert app_with_user.config['SITE_LOGO'] == new_logo
    assert app_with_user.config['SITE_ICON'] == new_icon
    # check html
    html = rv.data.decode()
    assert f"<link rel=\"icon\" href=\"{new_icon}\">" in html
    assert f"<img src=\"{new_logo}\" alt=\"\" id=\"site_logo\"/>" in html


def test_update_preferences_robotstxt(app_with_user, admin_client):
    # allow
    rv = admin_client.post(
        "/-/admin",
        data={
            "robots_txt": "allow",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert app_with_user.config['ROBOTS_TXT'] == "allow"
    rv = admin_client.get("/robots.txt")
    assert "User-agent: *\nAllow: /" in rv.data.decode()
    # disallow
    rv = admin_client.post(
        "/-/admin",
        data={
            "robots_txt": "disallow",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert app_with_user.config['ROBOTS_TXT'] == "disallow"
    rv = admin_client.get("/robots.txt")
    assert "User-agent: *\nDisallow: /" in rv.data.decode()


def test_update_mail_preferences(app_with_user, admin_client):
    new_sender = "mail@example.com"
    new_server = "mail.example.com"
    new_port = "25"
    data = {
        "mail_sender": new_sender,
        "mail_server": new_server,
        "mail_port": new_port,
    }
    assert app_with_user.config['MAIL_DEFAULT_SENDER'] != new_sender
    assert app_with_user.config['MAIL_SERVER'] != new_server
    rv = admin_client.post(
        "/-/admin/mail_preferences",
        data=data,
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert app_with_user.config['MAIL_DEFAULT_SENDER'] == new_sender
    assert app_with_user.config['MAIL_SERVER'] == new_server
    assert app_with_user.config['MAIL_PORT'] != new_port
    assert app_with_user.config['MAIL_USE_TLS'] == False
    assert app_with_user.config['MAIL_USE_SSL'] == False
    # modify data to test tls/ssl settings
    data["mail_security"] = "tls"
    rv = admin_client.post(
        "/-/admin/mail_preferences",
        data=data,
        follow_redirects=True,
    )
    assert app_with_user.config['MAIL_USE_TLS'] == True
    assert app_with_user.config['MAIL_USE_SSL'] == False
    # modify data to test tls/ssl settings
    data["mail_security"] = "ssl"
    rv = admin_client.post(
        "/-/admin/mail_preferences",
        data=data,
        follow_redirects=True,
    )
    assert app_with_user.config['MAIL_USE_TLS'] == False
    assert app_with_user.config['MAIL_USE_SSL'] == True
    # modify data to test user/password
    assert app_with_user.config['MAIL_USERNAME'] == ""
    assert app_with_user.config['MAIL_PASSWORD'] == ""
    data["mail_username"] = "username"
    data["mail_password"] = "password"
    rv = admin_client.post(
        "/-/admin/mail_preferences",
        data=data,
        follow_redirects=True,
    )
    assert app_with_user.config['MAIL_USERNAME'] == "username"
    assert app_with_user.config['MAIL_PASSWORD'] == "password"


def test_update_mail_preferences_errors(app_with_user, admin_client):
    wrong_sender = "mail.example.com"
    assert app_with_user.config['MAIL_DEFAULT_SENDER'] != wrong_sender
    wrong_port = "twentyfive"
    assert app_with_user.config['MAIL_PORT'] != wrong_port
    # post wrong values to the form
    rv = admin_client.post(
        "/-/admin/mail_preferences",
        data={
            "mail_sender": wrong_sender,
            "mail_port": wrong_port,
        },
        follow_redirects=True,
    )
    # check that the form was submitted
    assert rv.status_code == 200
    html = rv.data.decode()
    # check messages
    assert "is not a valid email address" in html.lower()
    # and that the setting was not applied
    assert app_with_user.config['MAIL_DEFAULT_SENDER'] != wrong_sender
    assert "mail port must be a valid port" in html.lower()
    assert app_with_user.config['MAIL_PORT'] != wrong_port

    # post empty values
    rv = admin_client.post(
        "/-/admin/mail_preferences",
        data={},
        follow_redirects=True,
    )
    # check that the form was submitted
    assert rv.status_code == 200
    html = rv.data.decode()
    # MAIL_PORT can be empty
    assert "mail port must be a valid port" not in html.lower()
    # check required values
    assert "is not a valid email address" in html.lower()
    assert "mail server must not be empty" in html.lower()

    # post wrong port
    rv = admin_client.post(
        "/-/admin/mail_preferences",
        data={
            "mail_port": "1",
        },
        follow_redirects=True,
    )
    # check that the form was submitted
    assert rv.status_code == 200
    html = rv.data.decode()
    # MAIL_PORT can be empty
    assert "mail port must be a valid port" in html.lower()


def test_preferences_403(app_with_user, other_client):
    rv = other_client.get(
        "/-/admin/sidebar_preferences", follow_redirects=True
    )
    assert rv.status_code == 403
    rv = other_client.post(
        "/-/admin/sidebar_preferences", follow_redirects=True
    )
    assert rv.status_code == 403
    rv = other_client.get("/-/admin/user_management", follow_redirects=True)
    assert rv.status_code == 403
    rv = other_client.post("/-/admin/user_management", follow_redirects=True)
    assert rv.status_code == 403
    rv = other_client.get("/-/user/1", follow_redirects=True)
    assert rv.status_code == 403
    rv = other_client.post("/-/user/1", follow_redirects=True)
    assert rv.status_code == 403
    rv = other_client.get(
        "/-/admin/permissions_and_registration", follow_redirects=True
    )
    assert rv.status_code == 403
    rv = other_client.post(
        "/-/admin/permissions_and_registration", follow_redirects=True
    )
    assert rv.status_code == 403
    rv = other_client.get("/-/admin/mail_preferences", follow_redirects=True)
    assert rv.status_code == 403
    rv = other_client.post("/-/admin/mail_preferences", follow_redirects=True)
    assert rv.status_code == 403
    rv = other_client.get(
        "/-/admin/content_and_editing", follow_redirects=True
    )
    assert rv.status_code == 403
    rv = other_client.post(
        "/-/admin/content_and_editing", follow_redirects=True
    )
    assert rv.status_code == 403


def test_sidebar_preferences(app_with_user, admin_client):
    # check the form
    rv = admin_client.get("/-/admin/sidebar_preferences")
    assert rv.status_code == 200
    # disable all shortcuts
    rv = admin_client.post(
        "/-/admin/sidebar_preferences",
        data={
            "sidebar_shortcut_home": "False",
            "sidebar_shortcut_pageindex": "False",
            "sidebar_shortcut_changelog": "False",
            "sidebar_shortcut_createpage": "False",
        },
        follow_redirects=True,
    )
    assert "home" not in app_with_user.config['SIDEBAR_SHORTCUTS']
    assert "pageindex" not in app_with_user.config['SIDEBAR_SHORTCUTS']
    assert "changelog" not in app_with_user.config['SIDEBAR_SHORTCUTS']
    assert "createpage" not in app_with_user.config['SIDEBAR_SHORTCUTS']
    # enable all shortcuts
    rv = admin_client.post(
        "/-/admin/sidebar_preferences",
        data={
            "sidebar_shortcut_home": "True",
            "sidebar_shortcut_pageindex": "True",
            "sidebar_shortcut_changelog": "True",
            "sidebar_shortcut_createpage": "True",
        },
        follow_redirects=True,
    )
    assert "home" in app_with_user.config['SIDEBAR_SHORTCUTS']
    assert "pageindex" in app_with_user.config['SIDEBAR_SHORTCUTS']
    assert "changelog" in app_with_user.config['SIDEBAR_SHORTCUTS']
    assert "createpage" in app_with_user.config['SIDEBAR_SHORTCUTS']
    # configure page index mode
    assert app_with_user.config['SIDEBAR_MENUTREE_MODE'] == ""
    rv = admin_client.post(
        "/-/admin/sidebar_preferences",
        data={
            "sidebar_menutree_mode": "SORTED",
            "sidebar_menutree_maxdepth": "42",
        },
        follow_redirects=True,
    )
    assert app_with_user.config['SIDEBAR_MENUTREE_MODE'] == "SORTED"
    assert app_with_user.config['SIDEBAR_MENUTREE_MAXDEPTH'] == "42"


def test_user_edit(app_with_user, admin_client):
    # check the form
    rv = admin_client.get("/-/user/1")
    assert rv.status_code == 200
    rv = admin_client.get("/-/user/999")
    assert rv.status_code == 404
    rv = admin_client.post(
        "/-/user/1", data={"delete": True}, follow_redirects=True
    )
    assert rv.status_code == 200
    assert "Unable to delete yourself" in rv.data.decode()

    from otterwiki.auth import SimpleAuth, db

    user = SimpleAuth.User(
        name="a",
        email="a@b.de",
        first_seen=datetime.now(),
        last_seen=datetime.now(),
    )  # pyright: ignore

    db.session.add(user)
    db.session.commit()
    assert user.id is not None
    # check that the user can be edited
    rv = admin_client.get(f"/-/user/{user.id}")
    assert rv.status_code == 200
    # test change name, email
    rv = admin_client.post(
        f"/-/user/{user.id}",
        data={"name": "b", "email": "b@b.org"},
        follow_redirects=True,
    )
    assert rv.status_code == 200
    user = SimpleAuth.User.query.filter_by(id=user.id).first()
    assert user
    assert user.name == "b"
    assert user.email == "b@b.org"
    # test invalid name
    rv = admin_client.post(
        f"/-/user/{user.id}",
        data={"name": "", "email": "b@b.org"},
        follow_redirects=True,
    )
    # check error message
    assert "User name must not be empty" in rv.data.decode()
    user = SimpleAuth.User.query.filter_by(id=user.id).first()
    # assert name has not been changed
    assert user and user.name == "b"
    # test invalid email
    rv = admin_client.post(
        f"/-/user/{user.id}",
        data={"name": "b", "email": "@b.org"},
        follow_redirects=True,
    )
    assert "is not a valid email address" in rv.data.decode()
    user = SimpleAuth.User.query.filter_by(id=user.id).first()
    assert user and user.email == "b@b.org"
    # test flags
    for value, label in [
        ("is_admin", "admin"),
        ("is_approved", "approved"),
        ("allow_read", "read"),
        ("allow_write", "write"),
        ("allow_upload", "upload"),
    ]:
        rv = admin_client.post(
            f"/-/user/{user.id}",
            data={"name": "b", "email": "b@b.org", f"{value}": "True"},
            follow_redirects=True,
        )
        assert f"Added {label} flag" in rv.data.decode()
        rv = admin_client.post(
            f"/-/user/{user.id}",
            data={"name": "b", "email": "b@b.org", f"{value}": ""},
            follow_redirects=True,
        )
        assert f"Removed {label} flag" in rv.data.decode()
    # delete user
    rv = admin_client.post(
        f"/-/user/{user.id}", data={"delete": True}, follow_redirects=True
    )
    assert rv.status_code == 200
    # check user has been deleted
    rv = admin_client.get(f"/-/user/{user.id}")
    assert rv.status_code == 404


def test_user_delete(app_with_user, admin_client):
    from otterwiki.auth import SimpleAuth, db

    tmp_user_mail = "delete@me.org"
    # create a user
    user = SimpleAuth.User(
        name="Delete Me",  # pyright: ignore
        email=tmp_user_mail,  # pyright: ignore
        password_hash="",  # pyright: ignore
        first_seen=datetime.now(),  # pyright: ignore
        last_seen=datetime.now(),  # pyright: ignore
        is_admin=False,  # pyright: ignore
    )
    db.session.add(user)
    db.session.commit()
    uid = user.id
    # check user_management if mail address has is listed
    rv = admin_client.get("/-/admin/user_management", follow_redirects=True)
    assert tmp_user_mail in rv.data.decode()
    # check user exists
    rv = admin_client.get(f"/-/user/{uid}")
    assert rv.status_code == 200
    # delete user
    rv = admin_client.post(
        f"/-/user/{uid}", data={"delete": True}, follow_redirects=True
    )
    assert rv.status_code == 200
    # check user has been deleted
    rv = admin_client.get(f"/-/user/{uid}")
    assert rv.status_code == 404


def test_user_management(app_with_user, admin_client):
    from otterwiki.auth import SimpleAuth, generate_password_hash, db

    tmp_user_mail = "tmp@user.org"
    # create a temp user
    user = SimpleAuth.User(
        name="Temp User",  # pyright: ignore
        email=tmp_user_mail,  # pyright: ignore
        password_hash="",  # pyright: ignore
        first_seen=datetime.now(),  # pyright: ignore
        last_seen=datetime.now(),  # pyright: ignore
    )
    db.session.add(user)
    db.session.commit()

    # check user_management if mail address has is listed
    rv = admin_client.get("/-/admin/user_management", follow_redirects=True)
    table = BeautifulSoup(rv.data.decode(), "html.parser").find("table")
    assert tmp_user_mail in str(table)

    # test prevention of removing all admins
    rv = admin_client.post(
        "/-/admin/user_management",
        data={
            "is_admin": [],
            "is_approved": [1],
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "You can't remove all admins" in rv.data.decode()

    # test prevention of removing all approved users
    rv = admin_client.post(
        "/-/admin/user_management",
        data={
            "is_admin": [1],
            "is_approved": [],
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "You can't disable all users" in rv.data.decode()

    # test approved flag
    rv = admin_client.post(
        "/-/admin/user_management",
        data={
            "is_approved": [1, user.id],
            "is_admin": [1],
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    # check database
    user = SimpleAuth.User.query.filter_by(id=user.id).first()
    assert user and user.is_approved == True

    # test admin flag
    rv = admin_client.post(
        "/-/admin/user_management",
        data={
            "is_approved": [1, user.id],
            "is_admin": [1, user.id],
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    # check database
    user = SimpleAuth.User.query.filter_by(id=user.id).first()
    assert user and user.is_approved == True and user.is_admin == True

    # test all other flags
    for flag in ["allow_read", "allow_write", "allow_upload"]:
        rv = admin_client.post(
            "/-/admin/user_management",
            data={
                "is_approved": [1, user.id],
                "is_admin": [1],
                flag: [user.id],
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200
        # check database
        admin = SimpleAuth.User.query.filter_by(id=1).first()
        assert admin and admin.is_approved == True and admin.is_admin == True
        user = SimpleAuth.User.query.filter_by(id=user.id).first()
        assert user and getattr(user, flag) == True
        # remove flag
        rv = admin_client.post(
            "/-/admin/user_management",
            data={
                "is_approved": [1, user.id],
                "is_admin": [1],
                flag: [],
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200
        # check database
        admin = SimpleAuth.User.query.filter_by(id=1).first()
        assert admin and admin.is_approved == True and admin.is_admin == True
        user = SimpleAuth.User.query.filter_by(id=user.id).first()
        assert user and getattr(user, flag) == False


def test_user_add(app_with_user, admin_client):
    from otterwiki.auth import SimpleAuth

    new_user = ("New User", "new@user.org")
    # check user_management if mail address has is listed
    rv = admin_client.get("/-/admin/user_management", follow_redirects=True)
    table = BeautifulSoup(rv.data.decode(), "html.parser").find("table")
    # make user doesn't exist
    assert new_user[0] not in str(table)
    assert new_user[1] not in str(table)
    # create user
    rv = admin_client.post(
        f"/-/user/",
        data={
            "name": new_user[0],
            "email": new_user[1],
            "is_approved": "1",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    # check that the user has been created
    rv = admin_client.get("/-/admin/user_management", follow_redirects=True)
    table = BeautifulSoup(rv.data.decode(), "html.parser").find("table")
    # make user exists
    assert new_user[0] in str(table)
    assert new_user[1] in str(table)
    user = SimpleAuth.User.query.filter_by(email=new_user[1]).first()
    assert user is not None
    assert user.name == new_user[0]
    assert user.email == new_user[1]
    assert user.is_approved == True
    assert user.is_admin == False

    # try to add user again
    rv = admin_client.post(
        f"/-/user/",
        data={
            "name": "",
            "email": new_user[1],
            "is_approved": "1",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    # check for toast
    assert "User with this email exists" in rv.data.decode()
    assert "Name must not be empty" in rv.data.decode()
