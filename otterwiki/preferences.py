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
    if not is_valid_email(form.get("mail_sender")):
        toast("'{}' is not a valid email address.".format(form.get("mail_sender")), "error")
        error += 1
    else:
        _update_preference("MAIL_DEFAULT_SENDER", form.get("mail_sender"))
    if empty(form.get("mail_server")):
        toast("Mail Server can not be empty.", "error")
        error += 1
    else:
        _update_preference("MAIL_SERVER", form.get("mail_server"))
    try:
        mail_port = int(form.get("mail_port"))
        if mail_port < 24 or mail_port > 65535:
            raise ValueError
    except ValueError:
        toast("Mail Port must a valid port.", "error")
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
    return redirect(url_for("settings", _anchor="mail_preferences"))

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
    return redirect(url_for("settings", _anchor="application_preferences"))

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
    return redirect(url_for("settings", _anchor="mail_preferences"))

def handle_preferences(form):
    if not empty(form.get('update_preferences')):
        return handle_app_preferences(form)
    if not empty(form.get('update_mail_preferences')):
        return handle_mail_preferences(form)
    if not empty(form.get('test_mail_preferences')):
        return handle_test_mail_preferences(form)

