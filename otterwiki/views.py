#!/usr/bin/env python

import os
import pathlib

from flask import (
    redirect,
    request,
    send_from_directory,
    abort,
    url_for,
    render_template,
    make_response,
)
from otterwiki.server import app, db
from otterwiki.wiki import Page, PageIndex, Changelog, Search, render
import otterwiki.auth
import otterwiki.preferences
from otterwiki.helper import toast
from otterwiki.util import sanitize_pagename
from otterwiki.auth import login_required, has_permission
from pprint import pprint, pformat

#
# techninal views/routes/redirects
#
@app.route("/")
def index():
    return view()


# @app.route('/robots.txt')
# @app.route('/sitemap.xml')
# def static_from_root():
#    return send_from_directory(app.static_folder, request.path[1:])


@app.route("/robots.txt")
def robotstxt():
    response = make_response(
        """User-agent: *
Allow: /""",
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


#
# wiki views
#
@app.route("/-/about")
def about():
    with open(os.path.join(app.root_path, "about.md")) as f:
        content = f.read()
    htmlcontent,_ = render.markdown(content)
    return render_template(
        "about.html",
        htmlcontent=htmlcontent,
    )


@app.route("/-/syntax")
def syntax():
    return render_template(
        "syntax.html",
    )


@app.route("/-/settings", methods=["POST", "GET"])
@login_required
def settings():
    if request.method == "GET":
        return otterwiki.auth.settings_form()
    else:
        return otterwiki.auth.handle_settings(request.form)

@app.route("/-/preferences", methods=["POST"])
@login_required
def preferences():
    return otterwiki.preferences.handle_preferences(request.form)


#
# index, changelog
#
@app.route("/-/log")
@app.route("/-/log/<string:revision>")
def changelog(revision=None):
    chlg = Changelog(revision)
    return chlg.render()


@app.route("/-/index")
def pageindex():
    idx = PageIndex("/")
    return idx.render()


@app.route("/-/create", methods=["POST", "GET"])
def create():
    pagename = request.form.get("pagename")
    is_folder = request.form.get("is-folder")
    pagename_sanitized = sanitize_pagename(pagename)
    if pagename is None:
        # This is the default creat page view
        return render_template("create.html", title="Create Page")
    elif pagename != pagename_sanitized:
        if pagename is not None and pagename != pagename_sanitized:
            toast("Please check the pagename ...", "warning")
        return render_template(
            "create.html", title="Create Page", pagename=pagename_sanitized
        )
    else:
        if is_folder:
            pagename = str(pathlib.Path(pagename, pagename))

        # this is the creation of a new page
        p = Page(pagename)
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
@app.route("/<path:path>/view")
# last matching endpoint seems to be the default for url_for
@app.route("/<path:path>")
@app.route("/<path:path>/view/<string:revision>")
def view(path="Home", revision=None):
    # return "path={}".format(path)
    p = Page(path)
    return p.view(revision)


@app.route("/<path:path>/history", methods=["POST", "GET"])
def history(path):
    # return "path={}".format(path)
    p = Page(path)
    return p.history(
        rev_a=request.form.get("rev_a"),
        rev_b=request.form.get("rev_b"),
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
        )
    return p.delete_form()


@app.route("/<path:path>/blame/", methods=["GET"])
@app.route("/<path:path>/blame", methods=["GET"])
@app.route("/<path:path>/blame/<string:revision>", methods=["GET"])
def blame(path, revision=None):
    p = Page(path)
    return p.blame(revision)


@app.route("/<path:path>/edit", methods=["POST", "GET"])
@app.route("/<path:path>/edit/<string:revision>", methods=["GET"])
def edit(path, revision=None):
    p = Page(path)
    return p.editor(
            content=request.form.get("content_editor"),
            cursor_line=request.form.get("cursor_line"),
            cursor_ch=request.form.get("cursor_ch"),
            )


@app.route("/<path:path>/save", methods=["POST"])
def save(path):
    # fetch form
    content = request.form.get("content_update")
    commit = request.form.get("commit").strip()
    # clean form data (make sure last character is a newline
    content = content.replace("\r\n", "\n").strip() + "\n"
    commit = commit.strip()
    # create page object
    p = Page(path)
    # and save
    return p.save(content=content, commit=commit, author=otterwiki.auth.get_author())


@app.route("/<path:path>/preview", methods=["POST", "GET"])
def preview(path):
    p = Page(path)
    return p.preview(
            content=request.form.get("content_editor"),
            cursor_line=request.form.get("cursor_line"),
            cursor_ch=request.form.get("cursor_ch"),
            )


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
    return p.get_attachment(filename, revision)


@app.route("/<path:pagepath>/t/<string:filename>")
@app.route("/<path:pagepath>/t/<string:filename>/<int:size>")
def get_attachment_thumbnail(pagepath, filename, size=80):
    p = Page(pagepath)
    return p.get_attachment_thumbnail(filename=filename, size=size, revision=None)


@app.route("/<path:pagepath>/attachment/<string:filename>", methods=["POST", "GET"])
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


# vim: set et ts=8 sts=4 sw=4 ai:
