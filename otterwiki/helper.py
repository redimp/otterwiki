#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
otterwiki.helper

functions used multiple times in the otterwiki that are not as
lightweight as utils.

"""

from otterwiki.server import app, mail
from flask import flash
from threading import Thread
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, BadData, SignatureExpired


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
