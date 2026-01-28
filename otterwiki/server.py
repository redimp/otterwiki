#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import datetime
import os
import sys
import logging

from flask import Flask
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

import otterwiki.gitstorage
import otterwiki.util
from otterwiki import __version__, fatal_error
from otterwiki.plugins import plugin_manager
from otterwiki.renderer import OtterwikiRenderer

app = Flask(__name__)
# default configuration settings
app.config.update(
    DEBUG=False,  # make sure DEBUG is off unless enabled explicitly otherwise
    TESTING=False,
    LOG_LEVEL="INFO",
    REPOSITORY=None,
    SECRET_KEY="CHANGE ME",
    SITE_NAME="An Otter Wiki",
    SITE_DESCRIPTION=None,
    SITE_LOGO=None,
    SITE_ICON=None,
    SITE_LANG="en",
    HIDE_LOGO=False,
    AUTH_METHOD="",
    AUTH_HEADERS_USERNAME="x-otterwiki-name",
    AUTH_HEADERS_EMAIL="x-otterwiki-email",
    AUTH_HEADERS_PERMISSIONS="x-otterwiki-permissions",
    READ_ACCESS="ANONYMOUS",
    WRITE_ACCESS="ANONYMOUS",
    ATTACHMENT_ACCESS="ANONYMOUS",
    AUTO_APPROVAL=True,
    DISABLE_REGISTRATION=False,
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
    SIDEBAR_MENUTREE_IGNORE_CASE=False,
    SIDEBAR_MENUTREE_MAXDEPTH="",
    SIDEBAR_MENUTREE_FOCUS="SUBTREE",  # OFF
    SIDEBAR_CUSTOM_MENU="",
    COMMIT_MESSAGE="REQUIRED",  # OPTIONAL DISABLED
    GIT_WEB_SERVER=False,
    SIDEBAR_SHORTCUTS="home pageindex createpage",
    ROBOTS_TXT="allow",
    WIKILINK_STYLE="",
    MAX_FORM_MEMORY_SIZE=1_000_000,
    HTML_EXTRA_HEAD="",
    HTML_EXTRA_BODY="",
    LOG_LEVEL_WERKZEUG="INFO",
    TREAT_UNDERSCORE_AS_SPACE_FOR_TITLES=False,
    HOME_PAGE="",
)
app.config.from_envvar("OTTERWIKI_SETTINGS", silent=True)

# print current version
print(
    f"*** Starting An Otter Wiki {__version__} {os.getenv('GIT_TAG', '')}",
    file=sys.stderr,
)

# check if any config option exists as environment variable
for key in app.config:
    if key in os.environ:
        if type(app.config[key]) == bool:
            app.config[key] = os.environ[key].lower() in [
                "true",
                "yes",
                "on",
                "1",
            ]
        else:
            app.config[key] = os.environ[key]

# configure logging
app.logger.setLevel(app.config["LOG_LEVEL"])
logging.getLogger('werkzeug').setLevel(app.config["LOG_LEVEL_WERKZEUG"])

# setup database
db = SQLAlchemy(app)

# ensure SECRET_KEY is set
if (
    len(app.config["SECRET_KEY"]) < 16
    or app.config["SECRET_KEY"] == "CHANGE ME"
):
    fatal_error(
        "Please configure a random SECRET_KEY with a length of at least 16 characters."
    )

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
if (len(storage.list()[0]) < 1) and (  # pyright: ignore never unbound
    len(storage.log()) < 1  # pyright: ignore
):
    home_page_config = app.config.get("HOME_PAGE", "")

    # only create initial page if HOME_PAGE is empty or doesn't start with /-/
    if not home_page_config or not home_page_config.startswith("/-/"):
        with open(os.path.join(app.root_path, "initial_home.md")) as f:
            content = f.read()

            if not home_page_config:
                # use the default Home page
                filename = (
                    "Home.md"
                    if app.config["RETAIN_PAGE_NAME_CASE"]
                    else "home.md"
                )
            else:
                # use the custom page path from HOME_PAGE
                custom_path = home_page_config.strip("/")
                if app.config["RETAIN_PAGE_NAME_CASE"]:
                    filename = f"{custom_path}.md"
                else:
                    filename = f"{custom_path.lower()}.md"

            storage.store(  # pyright: ignore
                filename=filename,
                content=content,
                author=("Otterwiki Robot", "noreply@otterwiki"),
                message="Initial commit",
            )
            app.logger.info(f"server: Created initial page /{filename[:-3]}.")


#
# app.config from db preferences
#
from otterwiki.models import *

mail = None


def update_app_config():
    global mail
    with app.app_context():
        for item in Preferences.query:
            if item.name.upper() in [
                "MAIL_USE_TLS",
                "MAIL_USE_SSL",
                "DISABLE_REGISTRATION",
                "AUTO_APPROVAL",
                "EMAIL_NEEDS_CONFIRMATION",
                "NOTIFY_ADMINS_ON_REGISTER",
                "NOTIFY_USER_ON_APPROVAL",
                "RETAIN_PAGE_NAME_CASE",
                "SIDEBAR_MENUTREE_IGNORE_CASE",
                "GIT_WEB_SERVER",
                "GIT_REMOTE_PUSH_ENABLED",
                "GIT_REMOTE_PULL_ENABLED",
                "HIDE_LOGO",
                "TREAT_UNDERSCORE_AS_SPACE_FOR_TITLES",
            ] or item.name.upper().startswith("SIDEBAR_SHORTCUT_"):
                item.value = item.value.lower() in ["true", "yes"]
            if item.name.upper() in ["MAIL_PORT"]:
                try:
                    item.value = int(item.value)
                except ValueError:
                    app.logger.warning(
                        "server: Ignored invalid value app.config[\"{}\"]={}".format(
                            item.name, item.value
                        )
                    )
            # update app settings
            app.config[item.name] = item.value
        # setup flask_mail
        mail = Mail(app)


with app.app_context():
    db.create_all()
update_app_config()


#
# a renderer configured with the app.config
#
# initialize renderer
app_renderer = OtterwikiRenderer(config=app.config)


#
# plugins
#
plugininfo = plugin_manager.list_plugin_distinfo()
for plugin, dist in plugininfo:
    app.logger.info(
        f"server: Loaded plugin: {dist.project_name}-{dist.version}"
    )
# setup plugins
plugin_manager.hook.setup(
    app=app, storage=storage, db=db
)  # pyright: ignore never unbound


#
# template extensions
#
@app.template_filter("debug_unixtime")
def template_debug_unixtime(s: int) -> str:
    if app.debug:

        return "{}?{}".format(s, datetime.datetime.now().strftime("%s"))
    else:
        return "{}?{}".format(s, os.getenv("GIT_TAG", None) or __version__)


@app.template_filter('pluralize')
def pluralize(count, plural='s', singular=''):
    """
    Example usage:

    - Found {{pages|length}} page{{pages|length|pluralize("s")}} matching the pattern.
    - We visited {{num_countries}} countr{{ num_countries|pluralize:("ies","y") }}.
    """
    if count == 1:
        return singular
    else:
        return plural


@app.template_filter('urlquote')
def urlquote(s):
    """
    Example usage:

    {{ url_for('inline_attachment', pagepath=pagepath) | urlquote }}.
    """
    squote = s.replace("'", "%27").replace("\"", "%22")
    return squote


@app.template_filter("format_datetime")
def format_datetime(value: datetime.datetime, format="medium") -> str:
    if type(value) is not datetime.datetime:
        app.logger.warning(f"format_datetime: {value=} is not datetime.datime")
        return str(value)
    if format == "medium":
        format = "%Y-%m-%d %H:%M"
    if format == "deltanow":
        if value.tzinfo is None:
            now = datetime.datetime.now()
        else:
            now = datetime.datetime.now(datetime.UTC)
        td = now - value

        return otterwiki.util.strfdelta_round(td, "second")
    else:  # format == 'full':
        format = "%Y-%m-%d %H:%M:%S"

    return value.strftime(format)


@app.template_filter('slugify')
def slugify(s, keep_slashes=True):
    """
    Example usage:

    {{ pagepath | slugify(keep_slashes=True) }}.
    """

    return otterwiki.util.slugify(s, keep_slashes=keep_slashes)


app.jinja_env.globals.update(os_getenv=os.getenv)

from otterwiki.helper import load_custom_html


def plugin_html_head_inject(page=None):
    """Template function to inject HTML into the head section via plugins."""
    results = plugin_manager.hook.template_html_head_inject(page=page)
    return ''.join(result for result in results if result)


def plugin_html_body_inject(page=None):
    """Template function to inject HTML into the body section via plugins."""
    results = plugin_manager.hook.template_html_body_inject(page=page)
    return ''.join(result for result in results if result)


app.jinja_env.globals.update(
    load_custom_html=load_custom_html,
    plugin_html_head_inject=plugin_html_head_inject,
    plugin_html_body_inject=plugin_html_body_inject,
)

# initialize git via http
import otterwiki.remote

githttpserver = otterwiki.remote.GitHttpServer(path=app.config["REPOSITORY"])

# initialize repository management stuff
import otterwiki.repomgmt

otterwiki.repomgmt.initialize_repo_management(storage)

# contains application routes,
# using side-effect of import executing the file to get
import otterwiki.views  # pyright: ignore
