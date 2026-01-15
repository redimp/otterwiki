#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
otterwiki.helper

functions used multiple times in the otterwiki that are not as
lightweight as utils.

"""

import os
import re
from hashlib import sha256
import json
from collections import namedtuple
from otterwiki.server import app, mail, storage, Preferences, db, app_renderer
from otterwiki.gitstorage import StorageError
from flask import flash, url_for, session
from threading import Thread
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from otterwiki.util import (
    split_path,
    join_path,
    clean_slashes,
    titleSs,
    ttl_lru_cache,
)
from otterwiki.models import Cache


class SerializeError(ValueError):
    pass


# initialize serializer
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


def send_mail(
    subject,
    recipients,
    text_body,
    sender=None,
    html_body=None,
    _async=True,
    raise_on_error=False,
):
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
    if not os.access(storage.path, os.W_OK):
        msg += [f"{storage.path} is not writeable."]
    try:
        storage.log(fail_on_git_error=True, max_count=1)
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


def auto_url(filename, revision=None, _external=False):
    # handle attachments and pages
    arr = split_path(filename)
    if filename.endswith(".md"):
        # page
        return (
            get_pagename(filename, full=True),
            url_for(
                "view",
                path=get_pagename(filename, full=True),
                revision=revision,
                _external=_external,
            ),
        )
    else:
        # attachment
        pagename, attached_filename = (
            get_pagename(join_path(arr[:-1]), full=True),
            arr[-1],
        )
        return (
            filename,
            url_for(
                'get_attachment',
                pagepath=pagename,
                filename=attached_filename,
                revision=revision,
                _external=_external,
            ),
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
    filename = (
        filename if app.config["RETAIN_PAGE_NAME_CASE"] else filename.lower()
    )
    if filename[-3:] != ".md":
        raise ValueError
    return filename[:-3]


def get_pagename(filepath, full=False, header=None):
    '''This will derive the page name (displayed on the web page) from the url requested'''
    # remove trailing slashes from filepath
    filepath = filepath.rstrip("/")

    if filepath.endswith(".md"):
        filepath = filepath[:-3]

    arr = split_path(filepath)
    if app.config["RETAIN_PAGE_NAME_CASE"]:
        # When RETAIN_PAGE_NAME_CASE is set the pagename is deduced by just the filename. No magic.
        pass
    else:
        # When RETAIN_PAGE_NAME_CASE is not set, all files are lowercase, so headers can be used to
        # configure a pagename. else default to titleSs
        for i, part in enumerate(arr):
            hint = part
            # if basename use header as hint
            if i == len(arr) - 1 and header is not None:
                hint = header
            if (hint != part and hint.lower() == part.lower()) or (
                hint == part and hint != part.lower()
            ):
                arr[i] = hint
            else:
                arr[i] = titleSs(part)

    if not full:
        return arr[-1]
    return "/".join(arr)


def get_pagename_for_title(filepath, full=False, header=None):
    '''this will derive the page name for display purposes (titles, breadcrumbs, etc.) with underscore replacement'''
    pagename = get_pagename(filepath, full=full, header=header)

    if app.config.get("TREAT_UNDERSCORE_AS_SPACE_FOR_TITLES", False):
        if full:
            # replace underscores in each path component
            parts = pagename.split("/")
            parts = [part.replace("_", " ") for part in parts]
            return "/".join(parts)
        else:
            # replace underscores in the single component
            return pagename.replace("_", " ")

    return pagename


def get_pagename_prefixes(filter=[]):
    pagename_prefixes = []

    if "pagecrumbs" in session:
        for crumb in session["pagecrumbs"][::-1]:
            if len(crumb) == 0 or crumb.lower() == "home":
                continue
            crumb_parent = join_path(split_path(crumb)[:-1])
            if len(crumb_parent) > 0 and crumb_parent not in pagename_prefixes:
                pagename_prefixes.append(crumb_parent)
            if crumb not in pagename_prefixes and crumb not in filter:
                pagename_prefixes.append(crumb)
            if len(pagename_prefixes) > 3:
                break
    return pagename_prefixes


def get_breadcrumbs(pagepath):
    if not pagepath or len(pagepath) < 1:
        return []
    # strip trailing slashes
    pagepath = pagepath.rstrip("/")
    parents = []
    crumbs = []
    for e in split_path(pagepath):
        parents.append(e)
        crumbs.append(
            (
                get_pagename_for_title(e),
                join_path(parents),
            )
        )
    return crumbs


def upsert_pagecrumbs(pagepath):
    """
    adds the given pagepath to the page specific crumbs "pagecrumbs" stored in the session
    """
    if pagepath is None or pagepath == "/":
        return
    if "pagecrumbs" not in session:
        session["pagecrumbs"] = []
    else:
        session["pagecrumbs"] = list(
            filter(
                lambda x: x.lower() != pagepath.lower(), session["pagecrumbs"]
            )
        )

    # add the pagepath to the tail of the list of pagecrumbs
    session["pagecrumbs"] = session["pagecrumbs"][-7:] + [pagepath]
    # flask.session: modifications on mutable structures are not picked up automatically
    session.modified = True


def patchset2urlmap(patchset, rev_b, rev_a=None):
    url_map = {}
    for file in patchset:
        source_file = re.sub('^(a|b)/', '', file.source_file)
        target_file = re.sub('^(a|b)/', '', file.target_file)
        if rev_a is None:
            # import ipdb; ipdb.set_trace()
            try:
                rev_a = storage.get_parent_revision(
                    filename=source_file, revision=rev_b
                )
            except StorageError:
                rev_a = rev_b
        d = {
            'source_file': source_file,
            'target_file': target_file,
            'source_url': (
                auto_url(source_file, revision=rev_a)[1]
                if source_file != "/dev/null"
                else None
            ),
            'target_url': (
                auto_url(target_file, revision=rev_b)[1]
                if target_file != "/dev/null"
                else None
            ),
        }
        url_map[file.path] = namedtuple('UrlData', d.keys())(*d.values())
    return url_map


def sha256sum(s: str) -> str:
    hash = sha256()
    hash.update(s.encode())
    return hash.hexdigest()


def update_ftoc_cache(filename, ftoc, mtime=None):
    if mtime is None:
        try:
            mtime = storage.mtime(filename)
        except FileNotFoundError as e:
            app.logger.warning(
                f"{e} while running update_ftoc_cache({filename})"
            )
            return
    hash = sha256sum(f"ftoc://{filename}")
    value = json.dumps({"filename": filename, "ftoc": ftoc})
    # check if key exists in Cache
    c = Cache.query.filter(Cache.key == hash).first()
    if c is None:
        c = Cache()
        c.key = hash
    c.value = value
    c.datetime = mtime
    # and update in the database
    db.session.add(c)
    db.session.commit()


def get_ftoc(filename, mtime=None):
    if mtime is None:
        mtime = storage.mtime(filename)
    hash = sha256sum(f"ftoc://{filename}")
    # check if hash is in the Cache
    result = Cache.query.filter(
        db.and_(Cache.key == hash, Cache.datetime >= mtime)
    ).first()
    if result is not None:
        try:
            value = json.loads(result.value)
            try:
                # check
                if filename == value["filename"]:
                    return value["ftoc"]
            except KeyError:
                pass
        except:
            pass
    content = storage.load(filename)
    # parse file contents
    _, ftoc, _ = app_renderer.markdown(content)
    update_ftoc_cache(filename, ftoc, mtime)

    return ftoc


@ttl_lru_cache(ttl=300, maxsize=2)
def load_custom_html(filename: str):
    custom_files = os.path.join(
        # respect the environment variable USE_STATIC_PATH if set, e.g. in a docker environment
        os.getenv(
            "USE_STATIC_PATH",
            os.path.join(
                app.root_path,
                'static',
            ),
        ),
        'custom',
    )
    custom_file_path = os.path.join(custom_files, filename)
    try:
        if os.path.exists(custom_file_path):
            with open(custom_file_path, 'r', encoding='utf-8') as f:
                return f.read()

    except Exception as e:
        app.logger.warning(
            f"Failed to load custom HTML file {filename} from {custom_file_path}: {e}"
        )
    return ""


def get_admin_emails():
    """Get email addresses of all admin users."""
    from otterwiki.auth import get_all_user

    admin_emails = []
    try:
        all_users = get_all_user()
        admin_emails = [
            user.email for user in all_users if user.is_admin and user.email
        ]
    except Exception as e:
        app.logger.error(f"Failed to get admin emails: {e}")

    return admin_emails


def send_repository_error_notification(
    operation_type, error_message, remote_url
):
    """
    Send email notification to all admins about repository operation errors.

    :param operation_type: Type of operation (e.g., "Auto Push", "Auto Pull", "Webhook Pull")
    :param error_message: The error message to include
    :param remote_url: The remote URL that failed
    """
    try:
        admin_emails = get_admin_emails()
        if not admin_emails:
            app.logger.warning(
                "No admin emails found for repository error notification"
            )
            return

        subject = f"OtterWiki Repository Error - {operation_type} Failed"

        # Create email body
        body_lines = [
            f"A repository operation has failed in your OtterWiki instance.",
            f"",
            f"Operation: {operation_type}",
            f"Remote URL: {remote_url}",
            f"Error: {error_message}",
            f"",
            f"Please check your repository configuration and git output.",
        ]

        text_body = "\n".join(body_lines)

        send_mail(
            subject=subject,
            recipients=admin_emails,
            text_body=text_body,
            _async=True,
        )

        app.logger.info(
            f"Repository error notification sent to {len(admin_emails)} admin(s) for {operation_type}"
        )

    except Exception as e:
        app.logger.error(f"Failed to send repository error notification: {e}")
