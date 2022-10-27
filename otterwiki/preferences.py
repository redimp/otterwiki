#!/usr/bin/env python

from otterwiki import fatal_error
from otterwiki.util import is_valid_email
from werkzeug.urls import url_parse
from flask import (
    redirect,
    request,
    abort,
    url_for,
    render_template,
)
from flask_login import (
    login_required,
    current_user,
)
from otterwiki.server import app, db, update_app_config, Preferences
from otterwiki.helper import toast, send_mail, serialize, deserialize, SerializeError
from otterwiki.util import random_password, empty, is_valid_email
from otterwiki.auth import has_permission, current_user, get_all_User
from pprint import pprint

def _update_preference(name, value, delay_commit=False):
    entry = Preferences.query.filter_by(name=name).first()
    try:
        entry.value = value
    except AttributeError:
        entry = Preferences(name=name, value=value)
    db.session.add(entry)

def handle_mail_preferences(form):
    error = 0
    if not is_valid_email(form.get("mail_sender") or ""):
        toast("'{}' is not a valid email address.".format(form.get("mail_sender")), "error")
        error += 1
    else:
        _update_preference("MAIL_DEFAULT_SENDER", form.get("mail_sender").strip())
    if empty(form.get("mail_server")):
        toast("Mail Server must not be empty.", "error")
        error += 1
    else:
        _update_preference("MAIL_SERVER", form.get("mail_server").strip())
    try:
        if not empty(form.get("mail_port")):
            mail_port = int(form.get("mail_port").strip())
            if mail_port < 24 or mail_port > 65535:
                raise ValueError
        else:
            mail_port = ""
    except (ValueError, TypeError) as e:
        toast("Mail port must be a valid port.", "error")
        error += 1
    else:
        _update_preference("MAIL_PORT", mail_port)
    # MAIL_USERNAME and MAIL_PASSWORD
    _update_preference("MAIL_USERNAME", form.get("mail_user", ""))
    _update_preference("MAIL_PASSWORD", form.get("mail_password", ""))
    # Encryption
    if empty(form.get("mail_security")):
        _update_preference("MAIL_USE_TLS", "False")
        _update_preference("MAIL_USE_SSL", "False")
    elif form.get("mail_security") == "tls":
        _update_preference("MAIL_USE_TLS", "True")
        _update_preference("MAIL_USE_SSL", "False")
    else:
        _update_preference("MAIL_USE_TLS", "False")
        _update_preference("MAIL_USE_SSL", "True")
    if error < 1:
        toast("Mail Preferences upated.")

    db.session.commit()
    update_app_config()
    return redirect(url_for("admin", _anchor="mail_preferences"))

def handle_app_preferences(form):
    for name in ["site_name", "site_logo"]:
        _update_preference(name.upper(),form.get(name, ""))
    for name in ["READ_access", "WRITE_access", "ATTACHMENT_access"]:
        _update_preference(name.upper(),form.get(name, "ANONYMOUS"))
    for checkbox in ["auto_approval", "email_needs_confirmation",
                     "notify_admins_on_register"]:
        _update_preference(checkbox.upper(),form.get(checkbox, "False"))
    # commit changes to the database
    db.session.commit()
    update_app_config()
    toast("Application Preferences upated.")
    return redirect(url_for("admin", _anchor="application_preferences"))

def handle_test_mail_preferences(form):
    recipient = form.get("mail_recipient")
    if empty(recipient):
        # default current user
        recipient = current_user.email
    # check if mail is valid
    if is_valid_email(recipient):
        body = """OtterWiki Test Mail"""
        subject = "OtterWiki Test Mail"
        try:
            send_mail(subject, [recipient], body, _async=False, raise_on_error=True)
        except Exception as e:
            toast("Error: {}".format(e),"error")
        else:
            toast("Testmail sent to {}.".format(recipient))
    else:
        toast("Invalid email address: {}".format(recipient),"error")
    return redirect(url_for("admin", _anchor="mail_preferences"))

def handle_preferences(form):
    if not empty(form.get('update_preferences')):
        return handle_app_preferences(form)
    if not empty(form.get('update_mail_preferences')):
        return handle_mail_preferences(form)
    if not empty(form.get('test_mail_preferences')):
        return handle_test_mail_preferences(form)
    if not empty(form.get("update_permissions")):
        return handle_user_management(form)

def handle_user_management(form):
    if not has_permission("ADMIN"):
        return abort(403)
    is_approved = [int(x) for x in form.getlist("is_approved")]
    is_admin = [int(x) for x in form.getlist("is_admin")]
    if len(is_admin) < 1:
        toast("You can't remove all admins", "error")
    elif len(is_approved) < 1:
        toast("You can't disable all users", "error")
    else:
        # update users
        for user in get_all_User():
            msgs = []
            # approval
            if user.is_approved and not user.id in is_approved:
                user.is_approved = False
                msgs.append("removed approved")
            elif not user.is_approved and user.id in is_approved:
                user.is_approved = True
                msgs.append("added approved")
            # admin
            if user.is_admin and not user.id in is_admin:
                user.is_admin = False
                msgs.append("removed admin")
            elif not user.is_admin and user.id in is_admin:
                user.is_admin = True
                msgs.append("added admin")
            if len(msgs):
                toast("{} {} flag".format(user.email, " and ".join(msgs)))
                app.logger.report(
                    "{} updated {} <{}>: {}".format(
                        current_user, user.name, user.email, " and ".join(msgs)
                    )
                )
                db.session.add(user)
        db.session.commit()
    return redirect(url_for("admin", _anchor="user_management"))

def admin_form():
    if not has_permission("ADMIN"):
        abort(403)
    # query user
    user_list = get_all_User()
    # render form
    return render_template(
        "admin.html",
        title="Admin",
        user_list=user_list,
    )

