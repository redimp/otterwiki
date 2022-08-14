#!/usr/bin/env python

import os
import sys
from flask import Flask
from flask_htmlmin import HTMLMIN
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from otterwiki import fatal_error, __version__
import otterwiki.gitstorage

app = Flask(__name__)
# default configuration settings
app.config.update(
    DEBUG=False,  # make sure DEBUG is off unless enabled explicitly otherwise
    TESTING=False,
    REPOSITORY=None,
    SECRET_KEY="CHANGE ME",
    SITE_NAME="An Otter Wiki",
    SITE_LOGO=None,
    AUTH_METHOD="",
    READ_ACCESS="ANONYMOUS",
    WRITE_ACCESS="ANONYMOUS",
    ATTACHMENT_ACCESS="ANONYMOUS",
    AUTO_APPROVAL=True,
    EMAIL_NEEDS_CONFIRMATION=True,
    NOTIFY_ADMINS_ON_REGISTER=False,
    SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    MAIL_DEFAULT_SENDER="otterwiki@YOUR.ORGANIZATION.TLD",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MINIFY_HTML=True,
)
app.config.from_envvar("OTTERWIKI_SETTINGS", silent=True)

# setup flask_mail
mail = Mail(app)

# setup database
db = SQLAlchemy(app)

# auto html minify
if not app.config["TESTING"] and not app.config["DEBUG"]:
    htmlmin = HTMLMIN(app)

# setup storage
if app.config["REPOSITORY"] is None:
    fatal_error("Please configure a REPOSITORY path.")
elif not os.path.exists(app.config["REPOSITORY"]):
    fatal_error(
        "Repository path '{}' not found. Please configure otterwiki.".format(
            app.config["REPOSITORY"]
        )
    )
else:
    try:
        storage = otterwiki.gitstorage.GitStorage(app.config["REPOSITORY"])
    except otterwiki.gitstorage.StorageError as e:
        fatal_error(e)

#
# template extensions
#
@app.template_filter("debug_unixtime")
def template_debug_unixtime(s):
    if app.debug:
        from datetime import datetime

        return "{}?{}".format(s, datetime.now().strftime("%s"))
    else:
        return "{}?{}".format(s, __version__)


@app.template_filter("format_datetime")
def format_datetime(value, format="medium"):
    if format == "medium":
        format = "%Y-%m-%d %H:%M"
    else:  # format == 'full':
        format = "%Y-%m-%d %H:%M:%S"
    return value.strftime(format)


import otterwiki.views

# vim: set et ts=8 sts=4 sw=4 ai:
