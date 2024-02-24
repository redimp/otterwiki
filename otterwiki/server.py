#!/usr/bin/env python

import os
import logging
from flask import Flask
from flask_htmlmin import HTMLMIN
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from otterwiki import fatal_error, __version__
import otterwiki.gitstorage
import otterwiki.util

app = Flask(__name__)
# default configuration settings
app.config.update(
    DEBUG=False,  # make sure DEBUG is off unless enabled explicitly otherwise
    TESTING=False,
    REPOSITORY=None,
    SECRET_KEY="CHANGE ME",
    SITE_NAME="An Otter Wiki",
    SITE_DESCRIPTION=None,
    SITE_LOGO=None,
    SITE_ICON=None,
    AUTH_METHOD="",
    READ_ACCESS="ANONYMOUS",
    WRITE_ACCESS="ANONYMOUS",
    ATTACHMENT_ACCESS="ANONYMOUS",
    AUTO_APPROVAL=True,
    EMAIL_NEEDS_CONFIRMATION=True,
    NOTIFY_ADMINS_ON_REGISTER=False,
    NOTIFY_USER_ON_APPROVAL=False,
    RETAIN_PAGE_NAME_CASE=False,
    SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    MAIL_DEFAULT_SENDER="otterwiki@YOUR.ORGANIZATION.TLD",
    MAIL_SERVER="",
    MAIL_PORT="",
    MAIL_USERNAME="",
    MAIL_PASSWORD="",
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=False,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MINIFY_HTML=True,
    SIDEBAR_MENUTREE_MODE="SORTED",
    SIDEBAR_MENUTREE_MAXDEPTH="",
    COMMIT_MESSAGE="REQUIRED", # OPTIONAL
    GIT_WEB_SERVER=False,
)
app.config.from_envvar("OTTERWIKI_SETTINGS", silent=True)

# add log level
otterwiki.util.addLoggingLevel('REPORT',logging.ERROR + 5)

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


# check if the git repository is empty
if (len(storage.list()[0]) < 1) and (len(storage.log()) < 1):  # pyright: ignore
    # we have a brand new repository here
    with open(os.path.join(app.root_path, "initial_home.md")) as f:
        content = f.read()
        filename = "Home.md" if app.config["RETAIN_PAGE_NAME_CASE"] else "home.md"
        storage.store(  # pyright: ignore
            filename=filename, content=content,
            author=("Otterwiki Robot", "noreply@otterwiki"),
            message="Initial commit",
        )
        app.logger.report("Initial /Home created.")     # pyright: ignore


#
# app.config from db preferences
#
class Preferences(db.Model):
    name = db.Column(db.String(256), primary_key=True)
    value = db.Column(db.String(256))

    def __str__(self):
        return '{}: {}'.format(self.name, self.value)

mail = None

def update_app_config():
    global mail
    with app.app_context():
        for item in Preferences.query:
            if item.name.upper() in [
                "MAIL_USE_TLS",
                "MAIL_USE_SSL",
                "AUTO_APPROVAL",
                "EMAIL_NEEDS_CONFIRMATION",
                "NOTIFY_ADMINS_ON_REGISTER",
                "NOTIFY_USER_ON_APPROVAL",
                "RETAIN_PAGE_NAME_CASE",
            ]:
                item.value = item.value.lower() in ["true","yes"]
            if item.name.upper() in ["MAIL_PORT"]:
                try:
                    item.value = int(item.value)
                except ValueError:
                    app.logger.warning("ignored invalid value app.config[\"{}\"]={}".format(
                        item.name, item.value))
            # update app settings
            app.config[item.name] = item.value
        # setup flask_mail
        mail = Mail(app)

with app.app_context():
    db.create_all()
update_app_config()

#
# template extensions
#
@app.template_filter("debug_unixtime")
def template_debug_unixtime(s):
    if app.debug:
        from datetime import datetime

        return "{}?{}".format(s, datetime.now().strftime("%s"))
    else:
        return "{}?{}".format(s, os.getenv("GIT_TAG", None) or __version__)


@app.template_filter("format_datetime")
def format_datetime(value, format="medium"):
    if format == "medium":
        format = "%Y-%m-%d %H:%M"
    else:  # format == 'full':
        format = "%Y-%m-%d %H:%M:%S"
    return value.strftime(format)

app.jinja_env.globals.update(os_getenv=os.getenv)

# initialize git via http
import otterwiki.remote
githttpserver = otterwiki.remote.GitHttpServer(path=app.config["REPOSITORY"])

import otterwiki.views

# vim: set et ts=8 sts=4 sw=4 ai:
