#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

from otterwiki.util import is_valid_email
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlsplit
from flask import (
    redirect,
    request,
    url_for,
    render_template,
    abort,
)
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    current_user,
)
from otterwiki.server import app, db
from otterwiki.helper import (
    toast,
    send_mail,
    serialize,
    deserialize,
    SerializeError,
)
from otterwiki.util import random_password, empty
from otterwiki.models import User as UserModel
from datetime import datetime
import hmac


def check_password_hash_backport(pwhash, password):
    # split pwhash to check the method
    method, salt, hashval = pwhash.split("$", 2)
    # sha256 is no longer supported by werkzeug>=3.x
    if method in ["sha256", "sha512"]:
        # encode salt and passwd
        salt = salt.encode("utf-8")
        password = password.encode("utf-8")
        return hmac.compare_digest(
            hmac.new(salt, password, method).hexdigest(), hashval
        )
    return check_password_hash(pwhash, password)


class SimpleAuth:
    class User(UserMixin, UserModel):
        pass

    def user_loader(self, id):
        return self.User.query.filter_by(id=int(id)).first()

    def get_all_user(self):
        return self.User.query.all()

    def get_user(self, uid=None, email=None):
        if uid is not None:
            return self.User.query.filter_by(id=uid).first()
        if email is not None:
            return self.User.query.filter_by(email=email).first()
        return self.User()

    def update_user(self, user):
        # validation check
        if not user.is_admin:
            # check if any user is admin
            if not True in [u.is_admin for u in self.get_all_user()]:
                # no admin left
                user.is_admin = True
        db.session.add(user)
        db.session.commit()
        return user

    def delete_user(self, user):
        db.session.delete(user)
        db.session.commit()

    def get_author(self):
        if not current_user.is_authenticated:
            return ("Anonymous", "")
        return (current_user.name, current_user.email)

    def login_form(self, email, remember=None, next=None):
        if next is None:
            next = request.args.get("next")
        # render template
        return render_template(
            "login.html",
            title="Login",
            email=email,
            remember=remember,
            next=next,
        )

    def handle_logout(self):
        logout_user()
        toast("You logged out successfully.")
        return redirect(url_for("login"))

    def check_credentials(self, email, password):
        user = self.User.query.filter_by(email=email).first()
        if not user or not check_password_hash_backport(
            user.password_hash, password
        ):
            return None
        return user

    def handle_login(self, email=None, password=None, remember=None):
        if email is not None:
            email = email.lower()
        # query user
        user = self.User.query.filter_by(email=email).first()
        next_page = request.form.get("next")
        user = self.check_credentials(email, password)
        if user is not None:
            if (
                app.config["EMAIL_NEEDS_CONFIRMATION"]
                and not user.is_admin
                and not user.email_confirmed
            ):
                toast(
                    "Please confirm your email address. "
                    + "<a href='{}'>Resend confirmation link.</a>".format(
                        url_for("request_confirmation_link", email=email)
                    ),
                    "warning",
                )
                return redirect(url_for("login"))
            if not user.is_admin and (
                self._user_needs_approvement() and not user.is_approved
            ):
                toast("You are not approved yet.", "warning")
                return redirect(url_for("login"))
            # login
            login_user(user, remember=remember is not None)
            # set next_page
            if not next_page or urlsplit(next_page).netloc != "":
                next_page = url_for("index")
            # check if the users password_hash is going to be deprecated
            if user.password_hash.startswith("sha256$"):
                app.logger.warning(
                    f"User has deprecated password hash: {user.email}"
                )
                toast(
                    f"Please <a href='{url_for('settings')}'>update your password</a>. The hashing method used is deprecated. Check <a href='{url_for('settings')}'>settings</a> for additional information.",
                    "warning",
                )
            else:
                toast("You logged in successfully.", "success")
            # update last_seen
            user.last_seen = datetime.now()
            db.session.add(user)
            db.session.commit()
            # redirect
            return redirect(next_page)
        else:
            toast("Invalid email address or password.", "error")

        return self.login_form(email, remember, next=next_page)

    def register_form(self, email=None, name=None):
        if email is not None:
            email = email.lower()
        # render template
        return render_template(
            "register.html",
            title="Register",
            email=email,
            name=name,
        )

    def request_confirmation(self, email):
        if email is not None:
            email = email.lower()
        # check if email exists
        user = self.User.query.filter_by(email=email).first()
        if not user:
            app.logger.warning(
                f"request of confirmation for non existing email: {email}"
            )
            abort(404)
        token = serialize(email, salt="confirm-email")
        # generate mail
        subject = "Request confirmation - {} - An Otter Wiki".format(
            app.config["SITE_NAME"]
        )
        text_body = render_template(
            "confirm_email.txt",
            sitename=app.config["SITE_NAME"],
            name=user.name,
            email=email,
            url=url_for("confirm_email", token=token, _external=True),
        )
        # send mail
        send_mail(subject=subject, recipients=[email], text_body=text_body)
        # notify user
        toast(
            "A request for confirmation has been sent to {}. Please check your mailbox.".format(
                email
            )
        )

    def handle_request_confirmation(self, email):
        self.request_confirmation(email)
        return redirect(url_for("login"))

    def create_user(self, email, name, password=None):
        if email is not None:
            email = email.lower()
        if password is None:
            # generate random password
            password = random_password()
        # hash password
        hashed_password = generate_password_hash(password, method="scrypt")
        # handle flags
        # first user is admin
        if len(self.User.query.all()) < 1:
            is_admin = True
            is_approved = True
        else:
            is_admin = False
            # handle auto approval
            is_approved = app.config["AUTO_APPROVAL"] is True
        # create user object
        user = self.User(  # pyright: ignore
            name=name,
            email=email,
            password_hash=hashed_password,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            is_admin=is_admin,
            is_approved=is_approved,
        )
        # add to database
        db.session.add(user)
        db.session.commit()
        # log user creation
        app.logger.info(
            "auth: New user registered: {} <{}>".format(name, email)
        )
        if app.config["EMAIL_NEEDS_CONFIRMATION"] and not is_admin:
            self.request_confirmation(email)
        else:
            # notify user
            if user.is_approved:
                toast("Your account has been created. You can log in now.")
            else:
                toast("Your account is waiting for approval.", "warning")
            # notify admins
            if app.config['NOTIFY_ADMINS_ON_REGISTER']:
                self.activated_user_notify_admins(name, email)

    def activated_user_notify_admins(self, name, email):
        # fetch all admin email adresses
        admin_list = self.User.query.filter_by(is_admin=True).all()
        admin_emails = [str(u.email) for u in admin_list]
        text_body = render_template(
            "admin_notification.txt",
            sitename=app.config["SITE_NAME"],
            name=name,
            email=email,
            url=url_for("settings", _external=True),
        )
        subject = "New Account Registration - {} - An Otter Wiki".format(
            app.config["SITE_NAME"]
        )
        send_mail(
            subject=subject, recipients=admin_emails, text_body=text_body
        )

    def _user_needs_approvement(self):
        # check if the user needs to be approved by checking
        # if beeing REGISTERED is a lower requirement anywhere
        return "REGISTERED" not in [
            app.config[permission].upper()
            for permission in [
                "READ_ACCESS",
                "WRITE_ACCESS",
                "ATTACHMENT_ACCESS",
            ]
        ]

    def user_confirmed_email(self, email):
        user = self.User.query.filter_by(email=email).first()
        if user is None or user.email_confirmed:
            return
        # mark email as confirmed
        user.email_confirmed = True
        db.session.add(user)
        db.session.commit()

        if user.is_approved:
            toast("Your email address has been confirmed. You can log in now.")
        elif self._user_needs_approvement():
            toast("Your account is waiting for approval.", "warning")
        # notify admins
        if app.config['NOTIFY_ADMINS_ON_REGISTER']:
            self.activated_user_notify_admins(user.name, user.email)

    def handle_register(self, email, name, password1, password2):
        # check if email exists
        user = self.User.query.filter_by(email=email).first()
        # check if email is valid
        if not is_valid_email(email):
            toast("This email address is invalid.", "error")
        elif user is not None:
            toast("This email address is already registered.", "error")
        elif name is None or len(name) < 1:
            toast("Please enter your name.", "error")
        elif password1 != password2:
            toast("The passwords do not match.", "error")
        elif password1 is None or len(password1) < 8:
            toast("The password must be at least 8 characters long.", "error")
        else:
            # register account
            self.create_user(email, name, password=password1)
            # send user back to login
            return redirect(url_for("login"))
        return self.register_form(email=email, name=name)

    def handle_confirmation(self, token):
        try:
            email = deserialize(token, salt="confirm-email", max_age=86400)
        except SerializeError:
            app.logger.warning(
                "auth.handle_confirmation() Invalid token: {}".format(token)
            )
            toast("Invalid token.", "error")
            # redirect
            return redirect(url_for("login"))
        # check if email exists
        user = self.User.query.filter_by(email=email).first()
        if user is None:
            toast("Invalid user or token.", "error")
            return redirect(url_for("login"))
        # mark user as confirmed
        self.user_confirmed_email(email)
        # notify admins
        if app.config['NOTIFY_ADMINS_ON_REGISTER']:
            self.activated_user_notify_admins(user.name, email)
        # log activation
        app.logger.info(
            "auth: New user activated: {} <{}>".format(user.name, user.email)
        )
        # redirect user back to login
        return redirect(url_for("login"))

    def settings_form(self):
        if has_permission("ADMIN"):
            user_list = self.User.query.all()
        else:
            user_list = None
        return render_template(
            "settings.html",
            title="Settings",
            user_list=user_list,
        )

    def handle_settings(self, form):
        if form.get("name") is not None:
            new_name = form.get("name")
            if len(new_name) < 1:
                toast("Your name must be at least one character.")
            else:
                # update name
                current_user.name = new_name
                db.session.add(current_user)
                db.session.commit()
                toast("Your name was updated successfully.", "success")
        if not empty(form.get("password1")) or not empty(
            form.get("password2")
        ):
            if form.get("password1") != form.get("password2"):
                toast("The passwords do not match.", "error")
            elif len(form.get("password1")) < 8:
                toast(
                    "The password must be at least 8 characters long.", "error"
                )
            else:
                # update password
                current_user.password_hash = generate_password_hash(
                    form.get("password1"), method="scrypt"
                )
                db.session.add(current_user)
                db.session.commit()
                toast("Your password was updated successfully.", "success")

        return redirect(url_for("settings"))

    def lost_password_form(self):
        return render_template(
            "lost_password.html",
            title="Lost password",
        )

    def handle_recover_password(self, email):
        # check if email exists
        user = self.User.query.filter_by(email=email).first()
        # check if email is valid
        if not is_valid_email(email):
            toast("This email address is invalid.", "error")
        elif user is None:
            toast("This email address is unknown.", "error")
        else:
            # recovery process
            token = serialize(email, salt="lost-password-email")
            # generate mail
            subject = "Password Recovery - {} - An Otter Wiki".format(
                app.config["SITE_NAME"]
            )
            text_body = render_template(
                "recover_password.txt",
                sitename=app.config["SITE_NAME"],
                name=user.name,
                url=url_for("recover_password", token=token, _external=True),
            )
            # send mail
            send_mail(subject=subject, recipients=[email], text_body=text_body)
            # log recovery attempt
            app.logger.info("auth: Password recovery for: {}".format(email))
            # notify user
            toast(
                "A recovery link been sent to {}. Please check your mailbox.".format(
                    email
                )
            )
        return self.lost_password_form()

    def handle_recover_password_token(self, token):
        try:
            email = deserialize(
                token, salt="lost-password-email", max_age=86400
            )
        except SerializeError:
            app.logger.warning(
                "auth.recover_password_token() Invalid token: {}".format(token)
            )
            toast("Invalid token.", "error")
            # redirect
            return redirect(url_for("login"))
        user = self.User.query.filter_by(email=email).first()
        if user is not None:
            login_user(user, remember=True)
            app.logger.info(
                "auth: Password recovery successful: {}".format(email)
            )
            toast("Welcome {}, please update your password.".format(user.name))
            return redirect(url_for("settings"))
        else:
            toast("Invalid email address.")
        return lost_password_form()

    def has_permission(self, permission, user):
        if user.is_authenticated and user.is_admin:
            return True
        # check page read permission
        if permission.upper() == "READ":
            if app.config["READ_ACCESS"].upper() == "ANONYMOUS":
                return True
            if (
                app.config["READ_ACCESS"].upper() == "REGISTERED"
                and user.is_authenticated
            ):
                return True
            if (
                app.config["READ_ACCESS"].upper() == "APPROVED"
                and user.is_authenticated
                and user.is_approved
            ):
                return True
            if user.is_authenticated and user.is_approved and user.allow_read:
                return True
            # admins have permissions for everything
            if user.is_authenticated and user.is_admin:
                return True
        # check page edit permission
        if permission.upper() == "WRITE":
            # if you are not allowed to read, you are not allowed to write
            if not self.has_permission("READ", user):
                return False
            if app.config["WRITE_ACCESS"].upper() == "ANONYMOUS":
                return True
            if (
                app.config["WRITE_ACCESS"].upper() == "REGISTERED"
                and user.is_authenticated
            ):
                return True
            if (
                app.config["WRITE_ACCESS"].upper() == "APPROVED"
                and user.is_authenticated
                and user.is_approved
            ):
                return True
            if user.is_authenticated and user.is_approved and user.allow_write:
                return True
            # admins have permissions for everything
            if user.is_authenticated and user.is_admin:
                return True
        # check upload permission
        if permission.upper() == "UPLOAD":
            if not self.has_permission("WRITE", user):
                return False
            if app.config["ATTACHMENT_ACCESS"] == "ANONYMOUS":
                return True
            if (
                app.config["ATTACHMENT_ACCESS"] == "REGISTERED"
                and user.is_authenticated
            ):
                return True
            if (
                app.config["ATTACHMENT_ACCESS"] == "APPROVED"
                and user.is_authenticated
                and user.is_approved
            ):
                return True
            if (
                user.is_authenticated
                and user.is_approved
                and user.allow_upload
            ):
                return True
            # admins have permissions for everything
            if user.is_authenticated and user.is_admin:
                return True
        if permission.upper() == "ADMIN":
            if user.is_anonymous:
                return False
            return True == user.is_admin

        return False

    def supported_features(self):
        return {'passwords': True, 'editing': True, 'logout': True}


class ProxyHeaderAuth:
    # if logout_link is not provided, hide the logout button
    def __init__(self, logout_link=None):
        self.logout_link = logout_link

    class User(UserMixin):
        def __init__(self, name, email, permissions):
            self.name = name
            self.email = email
            self.is_approved = True
            self.allow_read = 'READ' in permissions
            self.allow_write = 'WRITE' in permissions
            self.allow_upload = 'UPLOAD' in permissions
            self.is_admin = 'ADMIN' in permissions
            self.permissions = permissions

        def __repr__(self):
            return f"<User '{self.name} <{self.email}>' a:{self.is_admin}>"

    def supported_features(self):
        return {'passwords': False, 'editing': False, 'logout': False}

    # called on every page load
    def request_loader(self, req):
        if 'x-otterwiki-name' not in req.headers:
            return None

        if 'x-otterwiki-email' not in req.headers:
            return None

        if 'x-otterwiki-permissions' in req.headers:
            permissions = (
                req.headers.get('x-otterwiki-permissions').upper().split(',')
            )
        else:
            permissions = []

        return self.User(
            name=req.headers.get('x-otterwiki-name'),
            email=req.headers.get('x-otterwiki-email'),
            permissions=permissions,
        )

    # we can use the same implementation as above
    def get_author(self):
        if not current_user.is_authenticated:
            return ("Anonymous", "")
        return (current_user.name, current_user.email)

    # user will be directed to login form first, we should redirect them to handle_login automatically (just a POST to /-/login)
    def login_form(self, *args, **kwargs):
        if current_user.is_authenticated and self.has_permission(
            'READ', current_user
        ):
            return redirect(url_for("index"))
        else:
            return abort(403)

    def settings_form(self):
        return render_template(
            "settings.html",
            title="Settings",
            user_list=None,  # no users are stored in the database anyways
        )

    def get_all_user(self):
        return [current_user]

    def has_permission(self, permission, user):
        if not user.is_authenticated:
            return False
        return permission.upper() in user.permissions


# create login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # pyright: ignore

# create auth_manager
if app.config.get("AUTH_METHOD") in ["", "SIMPLE"]:
    auth_manager = SimpleAuth()
elif app.config.get("AUTH_METHOD") == "PROXY_HEADER":
    auth_manager = ProxyHeaderAuth()
else:
    raise RuntimeError(
        "Unknown AUTH_METHOD '{}'".format(app.config.get("AUTH_METHOD"))
    )

#
# proxies
#
if hasattr(auth_manager, "user_loader"):

    @login_manager.user_loader
    def user_load_proxy(id):
        return auth_manager.user_loader(id)

elif hasattr(auth_manager, "request_loader"):

    @login_manager.request_loader
    def request_load_proxy(req):
        return auth_manager.request_loader(req)


def login_form(*args, **kwargs):
    return auth_manager.login_form(*args, **kwargs)


def handle_login(*args, **kwargs):
    return auth_manager.handle_login(*args, **kwargs)


def handle_confirmation(*args, **kwargs):
    return auth_manager.handle_confirmation(*args, **kwargs)


def register_form(*args, **kwargs):
    if app.config['DISABLE_REGISTRATION']:
        toast("Registration is disabled.", "error")
        return redirect(url_for("index"))

    return auth_manager.register_form(*args, **kwargs)


def handle_register(*args, **kwargs):
    if app.config['DISABLE_REGISTRATION']:
        # Bad Request
        return abort(400, "Registration is disabled.")

    return auth_manager.handle_register(*args, **kwargs)


def handle_logout(*args, **kwargs):
    return auth_manager.handle_logout(*args, **kwargs)


def get_author():
    return auth_manager.get_author()


def settings_form():
    return auth_manager.settings_form()


def handle_settings(*args, **kwargs):
    return auth_manager.handle_settings(*args, **kwargs)


def lost_password_form():
    return auth_manager.lost_password_form()


def handle_recover_password(*args, **kwargs):
    return auth_manager.handle_recover_password(*args, **kwargs)


def handle_recover_password_token(*args, **kwargs):
    return auth_manager.handle_recover_password_token(*args, **kwargs)


def handle_request_confirmation(*args, **kwargs):
    return auth_manager.handle_request_confirmation(*args, **kwargs)


def get_all_user(*args, **kwargs):
    return auth_manager.get_all_user(*args, **kwargs)


def get_user(*args, **kwargs):
    return auth_manager.get_user(*args, **kwargs)


def update_user(*args, **kwargs):
    return auth_manager.update_user(*args, **kwargs)


def delete_user(user):
    return auth_manager.delete_user(user)


def check_credentials(email, password):
    return auth_manager.check_credentials(email, password)


#
# utils
#
def has_permission(permission, user=current_user):
    return auth_manager.has_permission(permission, user)


app.jinja_env.globals.update(has_permission=has_permission)

# these features help enable / disable the relevant parts of the UI
app.jinja_env.globals.update(
    auth_supported_features=auth_manager.supported_features()
)

