#!/usr/bin/env python

from otterwiki.util import is_valid_email
from flask import (
    redirect,
    abort,
    url_for,
    render_template,
)
from flask_login import (
    current_user,
)
from otterwiki.server import app, db, update_app_config, Preferences
from otterwiki.helper import toast, send_mail
from otterwiki.util import empty, is_valid_email
from flask_login import current_user
from otterwiki.auth import has_permission, get_all_user, get_user, update_user, delete_user

def _update_preference(name, value, commit=False):
    entry = Preferences.query.filter_by(name=name).first()
    if entry is None:
        # create entry
        entry = Preferences(name=name, value=value) # pyright: ignore
    entry.value = value
    db.session.add(entry)
    if commit:
        db.session.commit()

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
    if len(form.get("mail_password", ""))>0:
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
    for name in ["site_name", "site_logo", "site_description", "site_icon",
                 "sidebar_menutree_maxdepth","sidebar_menutree_mode", "commit_message",
                 "git_web_server"]:
        _update_preference(name.upper(),form.get(name, ""))
    for name in ["READ_access", "WRITE_access", "ATTACHMENT_access"]:
        _update_preference(name.upper(),form.get(name, "ANONYMOUS"))
    for checkbox in [
        "auto_approval",
        "email_needs_confirmation",
        "notify_admins_on_register",
        "notify_user_on_approval",
        "retain_page_name_case",
    ]:
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


def send_approvement_mail(user):
    text_body = render_template(
            "approvement_notification.txt",
            sitename=app.config["SITE_NAME"],
            name=user.name,
            url=url_for("login", _external=True),
            )
    subject = "Your account has been approved - {} - An Otter Wiki".format(app.config["SITE_NAME"])
    send_mail(subject=subject, recipients=[user.email], text_body=text_body)


def handle_user_management(form):
    if not has_permission("ADMIN"):
        return abort(403)
    is_approved = [int(x) for x in form.getlist("is_approved")]
    is_admin = [int(x) for x in form.getlist("is_admin")]
    allow_read = [int(x) for x in form.getlist("allow_read")]
    allow_write = [int(x) for x in form.getlist("allow_write")]
    allow_upload = [int(x) for x in form.getlist("allow_upload")]
    # track users that have been approved to send a notification
    # Make sure that nobody accidentally locks themselves out.
    if len(is_admin) < 1:
        toast("You can't remove all admins", "error")
    elif len(is_approved) < 1:
        toast("You can't disable all users", "error")
    else:
        # update users
        for user in get_all_user():
            user_was_just_approved = False
            msgs = []
            # approval
            if user.is_approved and not user.id in is_approved:
                user.is_approved = False
                msgs.append("disapproved")
            elif not user.is_approved and user.id in is_approved:
                user.is_approved = True
                user_was_just_approved = True
                msgs.append("approved")
            # read
            if user.allow_read and not user.id in allow_read:
                user.allow_read = False
                msgs.append("disallowed read")
            elif not user.allow_read and user.id in allow_read:
                user.allow_read = True
                msgs.append("allowed read")
            # write
            if user.allow_write and not user.id in allow_write:
                user.allow_write = False
                msgs.append("disallowed write")
            elif not user.allow_write and user.id in allow_write:
                user.allow_write = True
                msgs.append("allowed write")
            # upload
            if user.allow_upload and not user.id in allow_upload:
                user.allow_upload = False
                msgs.append("disallowed upload")
            elif not user.allow_upload and user.id in allow_upload:
                user.allow_upload = True
                msgs.append("allowed upload")
            # admin
            if user.is_admin and not user.id in is_admin:
                user.is_admin = False
                msgs.append("disabled admin")
            elif not user.is_admin and user.id in is_admin:
                user.is_admin = True
                msgs.append("enabled admin")
            if len(msgs):
                toast("{} {} flag".format(user.email, " and ".join(msgs)))
                app.logger.report( # pyright: ignore
                    "{} updated {} <{}>: {}".format(
                        current_user, user.name, user.email, " and ".join(msgs)
                    )
                )
                # update database
                update_user(user)
                # send notification mail
                if user_was_just_approved:
                    send_approvement_mail(user)

    return redirect(url_for("admin", _anchor="user_management"))

def admin_form():
    if not has_permission("ADMIN"):
        abort(403)
    # query user
    user_list = get_all_user()
    # render form
    return render_template(
        "admin.html",
        title="Admin",
        user_list=user_list,
    )

def user_edit_form(uid):
    if not has_permission("ADMIN"):
        abort(403)
    user = get_user(uid)
    if user is None:
        abort(404)
    # render form
    return render_template(
        "user.html",
        title="User",
        user=user,
    )

def handle_user_edit(uid, form):
    if not has_permission("ADMIN"):
        abort(403)
    user = get_user(uid)
    if user is None:
        abort(404)
    msgs, flags = [], []
    # delete
    if (form.get("delete", False)):
        if (user == current_user):
            toast(f"Unable to delete yourself.","error")
            return redirect(url_for("user", uid=user.id))
        toast(f"User '{user.name} &lt;{user.email}&gt;' deleted.")
        app.logger.report(f"deleted user '{user.name} &lt;{user.email}&gt;'") # pyright: ignore
        delete_user(user)
        return redirect(url_for("admin", _anchor="user_management"))
    if form.get("name") is None:
        return redirect(url_for("user", uid=user.id))
    # name
    if user.name != form.get("name").strip():
        msgs.append(f"renamed '{user.name}' to '{form.get('name').strip()}'")
        user.name = form.get("name").strip()
    # email
    if user.email != form.get("email").strip():
        if is_valid_email(form.get("email").strip()):
            msgs.append(f"updated {user.email} to {form.get('email').strip()}")
            user.email = form.get("email").strip()
        else:
            toast(f"'{form.get('email').strip()}' is not a valid email address","danger")
    user_was_already_approved = user.is_approved
    # handle all the flags
    for value, label in [
            ("is_admin", "admin"),
            ("is_approved", "approved"),
            ("allow_read", "read"),
            ("allow_write", "write"),
            ("allow_upload", "upload"),
            ]:
        if getattr(user, value) and not form.get(value):
            setattr(user, value, False)
            flags.append(f"removed {label}")
        elif not getattr(user, value) and form.get(value):
            setattr(user, value, True)
            flags.append(f"added {label}")
    # all flags checked updated msgs
    if len(flags):
        msgs.append("{} flag".format(" and ".join(flags)))
    if len(msgs):
        msgs[0] = msgs[0].capitalize()
        msgs[-1] += "."
        toast(" and ".join(msgs))
        app.logger.report( # pyright: ignore
            "{} updated {} <{}>: {}".format(
                current_user, user.name, user.email, " and ".join(msgs)
            ))
    try:
        update_user(user)
        if user.is_approved and not user_was_already_approved:
            send_approvement_mail(user)
    except Exception as e:
        app.logger.error(f"Unable to update user: {e}")
    return redirect(url_for("user", uid=user.id))


