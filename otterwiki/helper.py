#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
otterwiki.helper

functions used multiple times in the otterwiki that are not as
lightweight as utils.

"""

from otterwiki.server import app, mail, storage, Preferences
from otterwiki.gitstorage import StorageError
from flask import flash, url_for
from threading import Thread
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from otterwiki.util import split_path, join_path, clean_slashes, titleSs


class SerializeError(ValueError):
    pass


# initiliaze serializer
_serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])


def serialize(str, salt=None):
    return _serializer.dumps(str, salt=salt)


def deserialize(str, salt=None, max_age=86400):
    try:
        return _serializer.loads(str, salt=salt, max_age=max_age)
    except (BadSignature, SignatureExpired) as e:
        raise SerializeError


def toast(message, category=""):
    alert_map = {
        "": "alert-primary",
        "success": "alert-success",
        "warning": "alert-secondary",
        "error": "alert-danger",
        "danger": "alert-danger",
    }
    try:
        halfmoon_category = alert_map[category]
    except KeyError:
        halfmoon_category = alert_map[""]
    return flash(message, halfmoon_category)


def send_async_email(app, msg, raise_on_error=False):
    app.logger.debug("send_async_email()")
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error("send_async_email(): Exception {}".format(e))
            if raise_on_error:
                raise e


def send_mail(subject, recipients, text_body, sender=None, html_body=None, _async=True, raise_on_error=False):
    """send_mail

    :param subject:
    :param sender:
    :param recipients:
    :param text_body:
    :param html_body:
    """
    if not type(recipients) is list:
        recipients = list(recipients)
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if not app.config['TESTING'] and _async:
        # send mail asynchronous
        thr = Thread(target=send_async_email, args=[app, msg])
        thr.start()
    else:
        send_async_email(app, msg, raise_on_error)

def health_check():
    # check if storage is readable, the database works and auth is healthy
    msg = []
    # storage check
    try:
        storage.log(fail_on_git_error=True)
    except StorageError as e:
        msg += [f"StorageError in {storage.path}: {e}"]
    # db check
    try:
        Preferences.query.all()
    except:
        msg += [f"DB Error: Unable to query Preferences from DB."]
    if len(msg) == 0:
        return True, ["ok"]
    return False, msg


def auto_url(filename, revision=None):
    # handle attachments and pages
    arr = split_path(filename)
    if filename.endswith(".md"):
        # page
        return (
            get_pagename(filename, full=True),
            url_for(
                "view",
                path=get_pagename(
                    filename, full=True
                ),
                revision=revision,
            ),
        )
    else:
        # attachment
        pagename, attached_filename = (
            get_pagename(
                join_path(arr[:-1]), full=True
            ),
            arr[-1],
        )
        return (filename,
                url_for('get_attachment',
                    pagepath=pagename,
                    filename=attached_filename, revision=revision)
               )


def get_filename(pagepath):
    '''This is the actual filepath on disk (not via URL) relative to the repository root
    This function will attempt to determine if this is a 'folder' or a 'page'.
    '''

    p = pagepath if app.config["RETAIN_PAGE_NAME_CASE"] else pagepath.lower()
    p = clean_slashes(p)

    if not p.endswith(".md"):
        return "{}.md".format(p)

    return p


def get_attachment_directoryname(filename):
    filename = filename if app.config["RETAIN_PAGE_NAME_CASE"] else filename.lower()
    if filename[-3:] != ".md":
        raise ValueError
    return filename[:-3]


def get_pagename(filepath, full=False, header=None):
    '''This will derive the page name (displayed on the web page) from the url requested'''
    # remove trailing slashes from filepath
    filepath=filepath.rstrip("/")

    if filepath.endswith(".md"):
        filepath = filepath[:-3]

    arr = split_path(filepath)
    for i, part in enumerate(arr):
        hint = part
        # if basename use header as hint
        if i == len(arr)-1 and header is not None:
            hint = header
        if (hint != part and hint.lower() == part.lower()) \
                or (hint == part and hint != part.lower()):
            arr[i] = hint
        else:
            arr[i] = part if app.config["RETAIN_PAGE_NAME_CASE"] else titleSs(part)

    if not full:
        return arr[-1]
    return "/".join(arr)


