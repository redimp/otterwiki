#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os

from flask import (
    request,
    send_from_directory,
    abort,
    render_template,
    make_response,
    redirect,
    url_for,
)
from otterwiki.server import app, storage, githttpserver
from otterwiki.wiki import (
    Page,
    PageIndex,
    Changelog,
    Search,
    AutoRoute,
)
import otterwiki.auth
import otterwiki.preferences
from otterwiki.renderer import render
from otterwiki.helper import toast, health_check, get_pagename_prefixes
from otterwiki.version import __version__
from otterwiki.util import sanitize_pagename, split_path, join_path

from flask_login import login_required


#
# technical views/routes/redirects
#
@app.route("/")
def index():
    return view()


@app.route("/robots.txt")
def robotstxt():
    if app.config["ROBOTS_TXT"] == "allow":
        txt = "User-agent: *\nAllow: /"
    elif app.config["ROBOTS_TXT"] == "disallow":
        txt = "User-agent: *\nDisallow: /"
    else:  # this a fallback, in case of a typo: disallow
        txt = "User-agent: *\nDisallow: /"
    response = make_response(
        txt,
        200,
    )
    response.mimetype = "text/plain"
    return response


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static/img"),
        "otter-favicon2.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/-/healthz")
def healthz():
    healthy, msgs = health_check()
    return (
        "\n".join(msgs),
        200 if healthy else 503,
        {'Content-Type': 'text/plain; charset=utf-8'},
    )


#
# wiki views
#
@app.route("/-/about")
def about():
    with open(os.path.join(app.root_path, "about.md")) as f:
        content = f.read()
    htmlcontent, _ = render.markdown(content)
    return render_template(
        "about.html",
        htmlcontent=htmlcontent,
        __version__=__version__,
    )


@app.route("/-/syntax")
def syntax():
    return render_template(
        "syntax.html",
        in_help=True,
    )


@app.route("/-/help")
@app.route("/-/help/<string:topic>")
def help(topic=None):
    toc = None
    content = "TODO"
    if topic == "admin":
        with open(os.path.join(app.root_path, "help_admin.md")) as f:
            md = f.read()
            content, toc = render.markdown(md)
    elif topic == "syntax":
        toc = [
            (None, '', 2, s, s.lower())
            for s in [
                'Emphasis',
                'Headings',
                'Lists',
                'Links',
                'Quotes',
                'Images',
                'Tables',
                'Code',
                'Mathjax',
                'Footnotes',
                'Blocks',
                'Diagrams',
            ]
        ]
        return render_template("help_syntax.html", toc=toc, in_help=True)
    else:
        with open(os.path.join(app.root_path, "help.md")) as f:
            md = f.read()
            content, toc = render.markdown(md)
    # default help
    return render_template("help.html", content=content, toc=toc)


@app.route("/-/settings", methods=["POST", "GET"])
@login_required
def settings():
    if request.method == "GET":
        return otterwiki.auth.settings_form()
    else:
        return otterwiki.auth.handle_settings(request.form)


@app.route(
    "/-/admin/user_management", methods=["POST", "GET"]
)  # pyright: ignore -- false positive
@login_required
def admin_user_management():
    if request.method == "GET":
        return otterwiki.preferences.user_management_form()
    else:
        return otterwiki.preferences.handle_user_management(request.form)


@app.route(
    "/-/admin/sidebar_preferences", methods=["POST", "GET"]
)  # pyright: ignore -- false positive
@login_required
def admin_sidebar_preferences():
    if request.method == "GET":
        return otterwiki.preferences.sidebar_preferences_form()
    else:
        return otterwiki.preferences.handle_sidebar_preferences(request.form)


@app.route(
    "/-/admin/permissions_and_registration", methods=["POST", "GET"]
)  # pyright: ignore -- false positive
@login_required
def admin_permissions_and_registration():
    if request.method == "GET":
        return otterwiki.preferences.permissions_and_registration_form()
    else:
        return otterwiki.preferences.handle_permissions_and_registration(
            request.form
        )


@app.route(
    "/-/admin/content_and_editing", methods=["POST", "GET"]
)  # pyright: ignore -- false positive
@login_required
def admin_content_and_editing():
    if request.method == "GET":
        return otterwiki.preferences.content_and_editing_form()
    else:
        return otterwiki.preferences.handle_content_and_editing(request.form)


@app.route(
    "/-/admin/mail_preferences", methods=["POST", "GET"]
)  # pyright: ignore -- false positive
@login_required
def admin_mail_preferences():
    if request.method == "GET":
        return otterwiki.preferences.mail_preferences_form()
    else:
        return otterwiki.preferences.handle_mail_preferences(request.form)


@app.route(
    "/-/admin", methods=["POST", "GET"]
)  # pyright: ignore -- false positive
@login_required
def admin():
    if request.method == "GET":
        return otterwiki.preferences.admin_form()
    else:
        return otterwiki.preferences.handle_preferences(request.form)


@app.route("/-/user/", methods=["POST", "GET"])
@app.route("/-/user/<string:uid>", methods=["POST", "GET"])
@login_required
def user(uid=None):
    if request.method == "GET":
        return otterwiki.preferences.user_edit_form(uid)
    else:
        return otterwiki.preferences.handle_user_edit(uid, request.form)


#
# index, changelog
#
@app.route("/-/log")
@app.route("/-/log/<string:revision>")
@app.route("/-/changelog")
@app.route("/-/changelog/<string:revision>")
def changelog(revision=None):
    chlg = Changelog(revision)
    return chlg.render()


@app.route("/-/index")
def pageindex():
    idx = PageIndex()
    return idx.render()


@app.route("/-/create", methods=["POST", "GET"])
def create():
    pagename = request.form.get("pagename")
    pagename_sanitized = sanitize_pagename(pagename)
    if pagename is None:
        # This is the default create page view
        return render_template(
            "create.html",
            title="Create Page",
            pagename_prefixes=get_pagename_prefixes(),
        )
    elif pagename != pagename_sanitized:
        if pagename is not None and pagename != pagename_sanitized:
            toast("Please check the pagename ...", "warning")
        return render_template(
            "create.html",
            title="Create Page",
            pagename=pagename_sanitized,
            pagename_prefixes=get_pagename_prefixes(),
        )
    else:
        # this is the creation of a new page
        p = Page(pagename=pagename)
        return p.create()


#
# user login/logout/settings
#
@app.route("/-/login", methods=["POST", "GET"])
def login():
    email = request.cookies.get("email")
    if request.method == "GET":
        return otterwiki.auth.login_form(email)
    else:
        return otterwiki.auth.handle_login(
            email=request.form.get("email"),
            password=request.form.get("password"),
            remember=request.form.get("remember"),
        )


@app.route("/-/register", methods=["POST", "GET"])
def register():
    if request.method == "GET":
        return otterwiki.auth.register_form()
    else:
        return otterwiki.auth.handle_register(
            email=request.form.get("email"),
            name=request.form.get("name"),
            password1=request.form.get("password1"),
            password2=request.form.get("password2"),
        )


@app.route("/-/logout")
@login_required
def logout():
    return otterwiki.auth.handle_logout()


@app.route("/-/lost_password", methods=["POST", "GET"])
def lost_password():
    if request.method == "GET":
        return otterwiki.auth.lost_password_form()
    else:
        return otterwiki.auth.handle_recover_password(
            email=request.form.get("email"),
        )


@app.route("/-/confirm_email/<string:token>", methods=["POST", "GET"])
def confirm_email(token):
    return otterwiki.auth.handle_confirmation(token)


@app.route("/-/recover_password/<string:token>", methods=["GET"])
def recover_password(token):
    return otterwiki.auth.handle_recover_password_token(token=token)


@app.route("/-/request_confirmation_link/<string:email>", methods=["GET"])
def request_confirmation_link(email):
    return otterwiki.auth.handle_request_confirmation(email=email)


#
# page views
#
@app.route("/<path:path>/view/<string:revision>")
@app.route("/<path:path>/view")
def pageview(path="Home", revision=None):
    p = Page(path, revision=revision)
    return p.view()


# last matching endpoint seems to be the default for url_for
@app.route("/<path:path>")
def view(path="Home"):
    p = AutoRoute(path, values=request.values)
    return p.view()


@app.route("/<path:path>/history", methods=["POST", "GET"])
def history(path):
    # return "path={}".format(path)
    p = Page(path)
    return p.history(
        rev_a=request.form.get("rev_a"),
        rev_b=request.form.get("rev_b"),
    )


@app.route(
    "/<path:path>/diff/<string:rev_a>/<string:rev_b>", methods=["POST", "GET"]
)
def diff(path, rev_a, rev_b):
    # return "path={}".format(path)
    p = Page(path)
    return p.diff(
        rev_a=rev_a,
        rev_b=rev_b,
    )


@app.route("/<path:path>/rename/", methods=["POST", "GET"])
@app.route("/<path:path>/rename", methods=["POST", "GET"])
def rename(path):
    p = Page(path)
    if request.method == "POST":
        return p.handle_rename(
            new_pagename=request.form.get("new_pagename"),
            message=request.form.get("message"),
            author=otterwiki.auth.get_author(),
        )
    return p.rename_form()


@app.route("/<path:path>/delete/", methods=["POST", "GET"])
@app.route("/<path:path>/delete", methods=["POST", "GET"])
def delete(path):
    p = Page(path)
    if request.method == "POST":
        return p.delete(
            message=request.form.get("message"),
            author=otterwiki.auth.get_author(),
            recursive=request.form.get("recursive", False) == "recursive",
        )
    return p.delete_form()


@app.route("/<path:path>/blame/", methods=["GET"])
@app.route("/<path:path>/blame", methods=["GET"])
@app.route("/<path:path>/blame/<string:revision>", methods=["GET"])
def blame(path, revision=None):
    p = Page(path, revision=revision)
    return p.blame()


@app.route("/<path:path>/edit", methods=["POST", "GET"])
@app.route("/<path:path>/edit/<string:revision>", methods=["GET"])
def edit(path, revision=None):

    p = Page(path, revision=revision)
    return p.editor(
        author=otterwiki.auth.get_author(),
        handle_draft=request.form.get("draft", None),
    )


@app.route("/<path:path>/save", methods=["POST"])
def save(path):
    # fetch form
    content = request.form.get("content", "")
    # commit message
    commit = request.form.get("commit", "").strip()
    # Note: cursor_line cursor_ch are in the form
    # clean form data (make sure last character is a newline
    content = content.replace("\r\n", "\n").strip() + "\n"
    commit = commit.strip()
    # create page object
    p = Page(path)
    # and save
    return p.save(
        content=content, commit=commit, author=otterwiki.auth.get_author()
    )


@app.route("/<path:path>/preview", methods=["POST", "GET"])
def preview(path):
    p = Page(path)
    return p.preview(
        content=request.form.get("content"),
        cursor_line=request.form.get("cursor_line"),
    )


@app.route("/<path:path>/draft", methods=["POST", "GET"])
def draft(path):
    p = Page(path)
    return p.save_draft(
        content=request.form.get("content", ""),
        cursor_line=request.form.get("cursor_line", 0),
        cursor_ch=request.form.get("cursor_ch", 0),
        revision=request.form.get("revision", ""),
        author=otterwiki.auth.get_author(),
    )


@app.route("/<path:pagepath>/source/<string:revision>")
@app.route("/<path:pagepath>/source", methods=["GET"])
def source(pagepath, revision=None):
    raw = 'raw' in request.args
    p = Page(pagepath, revision=revision)
    return p.source(raw=raw)


@app.route("/-/commit/<string:revision>", methods=["GET"])
def show_commit(revision):
    chlg = Changelog()
    return chlg.show_commit(revision)


@app.route("/-/revert/<string:revision>", methods=["POST", "GET"])
def revert(revision):
    message = request.form.get("message")
    chlg = Changelog()
    if request.method == "POST":
        return chlg.revert(
            revision=revision,
            message=message,
            author=otterwiki.auth.get_author(),
        )
    return chlg.revert_form(revision=revision, message=message)


#
# page attachments
#


@app.route("/<path:pagepath>/a/<string:filename>")
@app.route("/<path:pagepath>/a/<string:filename>/<string:revision>")
def get_attachment(pagepath, filename, revision=None):
    p = Page(pagepath)
    if revision is None:
        revision = request.args.get("revision", None)
    return p.get_attachment(filename, revision)


@app.route("/<path:pagepath>/t/<string:filename>")
@app.route("/<path:pagepath>/t/<string:filename>/<int:size>")
def get_attachment_thumbnail(pagepath, filename, size=80):
    p = Page(pagepath)
    return p.get_attachment_thumbnail(
        filename=filename, size=size, revision=None
    )


@app.route(
    "/<path:pagepath>/attachment/<string:filename>", methods=["POST", "GET"]
)
def edit_attachment(pagepath, filename):
    p = Page(pagepath)
    return p.edit_attachment(
        filename=filename,
        new_filename=request.form.get("new_filename"),
        message=request.form.get("message"),
        delete=request.form.get("delete"),
        author=otterwiki.auth.get_author(),
    )


@app.route("/<path:pagepath>/attachments", methods=["POST", "GET"])
def attachments(pagepath):
    p = Page(pagepath)
    if request.method == "POST":
        return p.upload_attachments(
            files=request.files.getlist("file"),
            message=request.form.get("message"),
            filename=request.form.get("filename"),
            author=otterwiki.auth.get_author(),
        )
    return p.render_attachments()


@app.route("/<path:pagepath>/inline_attachment", methods=["POST"])
def inline_attachment(pagepath):
    p = Page(pagepath)
    return p.upload_attachments(
        files=request.files.getlist("file"),
        message="Uploaded via inline attachment",
        filename=None,
        author=otterwiki.auth.get_author(),
        inline=True,
    )


#
# search
#


@app.route("/-/search", methods=["POST", "GET"])
@app.route("/-/search/<string:query>", methods=["POST", "GET"])
def search(query=None):
    if query is None:
        query = request.form.get("query")
    s = Search(
        query=query,
        is_casesensitive=request.form.get("is_casesensitive") == "y",
        is_regexp=request.form.get("is_regexp") == "y",
        in_history=request.form.get("in_history") == "y",
    )
    return s.render()


#
# git remote http server
#
@app.route("/.git", methods=["GET"])
def dotgit():
    return redirect(url_for("index"))


@app.route("/.git/info/refs", methods=["POST", "GET"])
def git_info_refs():
    service = request.args.get("service")
    if service in ["git-upload-pack", "git-receive-pack"]:
        return githttpserver.advertise_refs(service)
    else:
        abort(400)


@app.route("/.git/git-upload-pack", methods=["POST"])
def git_upload_pack():
    return githttpserver.git_upload_pack(request.stream)


@app.route("/.git/git-receive-pack", methods=["POST"])
def git_receive_pack():
    return githttpserver.git_receive_pack(request.stream)


