#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Thread
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, BadData, SignatureExpired
from otterwiki import app, mail

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

def get_filename(pagename):
    return "{}.md".format(pagename.lower())

def get_pagename(filename):
    name = filename
    if name.endswith(".md"):
        name = name[:-3]
        name = name.title()
    return name

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, sender=None, html_body=None):
    """send_email

    :param subject:
    :param sender:
    :param recipients:
    :param text_body:
    :param html_body:
    """
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    # send mail asynchronous
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
