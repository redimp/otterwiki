#!/usr/bin/env python

import os
import re
from unidiff import PatchSet
from flask import (
    redirect,
    request,
    send_from_directory,
    abort,
    url_for,
    render_template,
    escape as html_escape,
    make_response,
    send_file,
    jsonify,
)
from otterwiki.gitstorage import StorageNotFound, StorageError
from otterwiki.server import app, db, storage
from otterwiki.renderer import render
from otterwiki.util import (
    split_path,
    join_path,
    empty,
    guess_mimetype,
    sizeof_fmt,
    get_filename,
    get_attachment_directoryname,
    get_pagename,
    get_pagepath,
    sanitize_pagename,
)
from otterwiki.helper import toast
from otterwiki.auth import has_permission, current_user
from datetime import datetime, timedelta
from werkzeug.http import http_date
from werkzeug.utils import secure_filename
from io import BytesIO
import pathlib

import PIL.Image
if not hasattr(PIL.Image, 'Resampling'):  # Pillow<9.0
    PIL.Image.Resampling = PIL.Image

from pprint import pprint, pformat


def get_breadcrumbs(pagepath):
    parents = []
    crumbs = []
    for e in split_path(pagepath):
        parents.append(e)
        crumbs.append((e, join_path(parents)))
    return crumbs


class PageIndex:
    def __init__(self, path=""):
        self.path = path

        files, directories = storage.list()
        files = [get_pagename(x, full=True) for x in files if x.endswith(".md")]
        self.pages = {}
        self.directories = {}
        for f in files:
            pair = (f, path + f)
            if f[0][0] in self.pages:
                self.pages[f[0]].append(pair)
            else:
                self.pages[f[0]] = [pair]

    def render(self):
        if not has_permission("READ"):
            abort(403)
        return render_template(
            "pageindex.html",
            title="Page Index",
            directories=self.directories,
            pages=self.pages,
        )

class WikiToc:
    def __init__(self, path=None):
        '''
        This will generate a TOC from a given path. Path is not yet implemented. But, the idea is that you could,
        for instance, create a feature where a toc could be automatically generated for a complicated sub folder.
        '''
        files, directories = storage.list(p=None)
        self.toc = [
                (len(split_path(f)), # depth
                 get_pagename(f), # title
                 f) # path
                 for f in files if f.endswith(".md") # filter .md files
            ]

    def render(self):
        if not has_permission("READ"):
            abort(403)
        return render_template(
            "global_toc.html",
            title="Table of Contents",
            pages=self.toc,
        )

class Changelog:
    def __init__(self, commit_start=None):
        self.commit_start = commit_start
        self.commit_count = 100
        pass

    def get(self):
        log = []
        # filter log
        for orig_entry in storage.log():
            entry = dict(orig_entry)
            entry["files"] = {}
            for filename in orig_entry["files"]:
                entry["files"][filename] = {}
                # handle attachments and pages
                arr = filename.split("/")
                if filename.endswith(".md"):
                    entry["files"][filename]["name"] = get_pagename(filename)
                    entry["files"][filename]["url"] = url_for(
                        "view", path=get_pagename(filename), revision=entry["revision"]
                    )
                # FIXME: if the subdirectory feature is there this has to be fixed
                if len(arr) >= 2:
                    pagename, attached_filename = get_pagename(arr[-2]), arr[-1]
                    entry["files"][filename]["name"] = filename
                    # FIXME: as soon as the attachments are, this needs an url
                    entry["files"][filename]["url"] = ""
                    # entry['files'][filename]['url'] = url_for('.get_attachment',
                    #         pagename=pagename, filename=filename, revision=entry['revision'])
            log.append(entry)
        # log.reverse()
        return log

    def render(self):
        if not has_permission("READ"):
            abort(403)
        log = self.get()
        pages = []
        next_page = None
        previous_page = None
        active_page = -1
        # pagination
        if self.commit_start is None:
            self.commit_start = log[0]["revision"]
        if self.commit_count is not None:
            log_page = []
            started = False
            start_n = None
            for n, entry in enumerate(log):
                if entry["revision"] == self.commit_start:
                    started = True
                    start_n = n
                elif not started:
                    continue
                log_page.append(entry)
                if len(log_page) > self.commit_count:
                    break
            # find paging revisions
            commit_i = 0
            page_i = 1
            while commit_i < len(log):
                if (commit_i >= start_n) and (commit_i < start_n + self.commit_count):
                    active_page = page_i
                    try:
                        previous_page = pages[-1]["revision"]
                    except IndexError:
                        pass
                pages.append(
                    {
                        "i": page_i,
                        "revision": log[commit_i]["revision"],
                        "active": active_page == page_i,
                        "dummy": False,
                    }
                )
                try:
                    if pages[-2]["active"]:
                        next_page = pages[-1]["revision"]
                except IndexError:
                    pass
                commit_i += self.commit_count
                page_i += 1
            log = log_page
        # TODO thin out pages ... remove pages, add "..." and set dummy = true
        return render_template(
            "changelog.html",
            log=log,
            title="Changelog",
            pages=pages,
            previous_page=previous_page,
            next_page=next_page,
        )

    def revert_form(self, revision, message):
        if not has_permission("WRITE"):
            abort(403)
        return render_template(
            "revert.html",
            revision=revision,
            message=message,
            title="Revert commit [{}]".format(revision),
        )

    def revert(self, revision, message, author):
        if not has_permission("WRITE"):
            abort(403)
        toast_message = "Reverted commit {}.".format(revision)
        if empty(message):
            message = toast_message
        try:
            storage.revert(revision, message=message, author=author)
        except StorageError as e:
            toast("Error: Unable to revert {}.".format(revision), "error")
        else:
            toast(toast_message)
        return redirect(url_for("changelog"))


class Page:
    def __init__(self, pagepath=None, pagename=None):

        if pagepath is not None:
            self.pagepath = pagepath
            self.pagename = get_pagename(pagepath)
        elif pagename is not None:
            self.pagename = pagename
            self.pagepath = get_pagepath(pagename)

        self.filename = get_filename(pagepath)
        self.attachment_directoryname = get_attachment_directoryname(self.filename)

    def breadcrumbs(self):
        return get_breadcrumbs(self.pagepath)

    def load(self, revision):
        metadata = None
        content = None
        try:
            content = storage.load(self.filename, revision=revision)
            metadata = storage.metadata(self.filename, revision=revision)
        except StorageNotFound as e:
            if all([
                not metadata,
                not content
            ]):
                # If both are None, raise the exception. Otherwise, a warning will show on the page that
                # the file is not under version control.
                raise

        return content, metadata

    def view(self, revision=None):
        # handle permissions
        if not has_permission("READ"):
            if current_user.is_authenticated and not current_user.is_approved:
                toast(
                    "You lack the permissions to access this wiki. Please wait for approval."
                )
            else:
                toast("You lack the permissions to access this wiki. Please login.")
            return redirect(url_for("login"))
        # handle page
        try:
            content, metadata = self.load(revision=revision)
        except StorageNotFound:
            app.logger.warning("Not found {}".format(self.pagename))
            return render_template("page404.html", pagename=self.pagename, pagepath=self.pagepath), 404

        danger_alert = False
        if not metadata:
            danger_alert = [
                "Not under version control",
                f"""This page was loaded from the repository but is not added under git version control. Make a commit on the <a href="{self.pagename}/edit" class="alert-link">Edit page</a> to add it."""
            ]

        # set title
        title = self.pagename
        if revision is not None:
            title = "{} ({})".format(self.pagename, revision)
        # render markdown
        htmlcontent, toc = render.markdown(content)
        # render template
        return render_template(
            "page.html",
            title=title,
            revision=revision,
            pagename=self.pagename,
            pagepath=self.pagepath,
            htmlcontent=htmlcontent,
            toc=toc,
            breadcrumbs=self.breadcrumbs(),
            danger_alert=danger_alert
        )

    def preview(self, content=None, cursor_line=None, cursor_ch=None):
        if content is None:
            try:
                content, metadata = self.load(revision=None)
            except StorageNotFound:
                app.logger.warning("Not found {}".format(self.pagename))
                return render_template("page404.html", pagename=self.pagename, pagepath=self.pagepath)
        content_html, toc = render.markdown(content, cursor=cursor_line)

        return render_template(
            "preview.html",
            pagename=self.pagename,
            pagepath=self.pagepath,
            content_html=content_html,
            toc=toc,
            content_editor=content,
            cursor_line=cursor_line,
            cursor_ch=cursor_ch,
        )

    def editor(self, revision=None, content=None, cursor_line=None, cursor_ch=None):
        if not has_permission("WRITE"):
            abort(403)
        if content is None:
            try:
                content, _ = self.load(revision=revision)
            except StorageNotFound:
                content = ""
            content = content.rstrip()
        return render_template(
            "editor.html",
            pagename=self.pagename,
            pagepath=self.pagepath,
            content_editor=content,
            cursor_line=cursor_line,
            cursor_ch=cursor_ch,
        )

    def save(self, content, commit, author):
        if not has_permission("WRITE"):
            abort(403)
        # store page
        changed = storage.store(
            filename=self.filename,
            content=content,
            message=commit,
            author=author,
        )
        if not changed:
            toast("Nothing changed.", "warning")
        else:
            toast("{} saved.".format(self.pagename))
        # redirect to view
        return redirect(url_for("view", path=self.pagepath))

    def create(self):
        if not has_permission("WRITE"):
            abort(403)
        # check if page exists
        try:
            content, metadata = self.load(revision=None)
        except StorageNotFound:
            content, metadata = None, None

        if content is not None:
            toast("{} exists already.".format(self.pagename), "warning")

        return redirect(url_for("edit", path=self.pagepath))

    def blame(self, revision=None):
        if not has_permission("READ"):
            abort(403)
        try:
            data = storage.blame(self.filename, revision)
            content, _ = self.load(revision=revision)
        except StorageNotFound:
            return render_template("page404.html", pagename=self.pagename, pagepath=self.pagepath), 404
        markup_lines = render.hilight(content, lang="markdown")
        # fix markup_lines
        markup_lines = markup_lines.replace(
            '<div class="highlight"><pre><span></span>', ""
        )
        markup_lines = markup_lines.replace("</pre></div>", "")
        markup_lines = markup_lines.splitlines()
        # filter data
        fdata = []
        # helper
        last = None
        oddeven = "odd"
        # use highlighted lines
        for row in data:
            line = markup_lines[int(row[3]) - 1]
            # line = row[4] # markup_lines[int(row[3])-1]
            if row[0] != last:
                oddeven = "odd" if oddeven == "even" else "even"
                fdata.append((row[0], row[1], row[2], int(row[3]), line, oddeven))
                last = row[0]
            else:
                fdata.append(("", "", "", int(row[3]), line, oddeven))
        return render_template(
            "blame.html",
            title="{} - blame {}".format(self.pagename, revision),
            pagepath=self.pagepath,
            pagename=self.pagename,
            blame=fdata,
            breadcrumbs=self.breadcrumbs(),
        )

    def diff(self, rev_a=None, rev_b=None):
        if not has_permission("READ"):
            abort(403)
        diff = storage.diff(self.filename, rev_b, rev_a)
        patchset = PatchSet(diff)
        hunk_helper = {}
        _line_type_style = {
            " ": "",
            "+": "added",
            "-": "removed",
        }
        for file in patchset:
            for hunk in file:
                lines = {}
                for l in hunk.source_lines():
                    if not l.source_line_no in lines:
                        lines[l.source_line_no] = []
                    lines[l.source_line_no].append(
                        {
                            "source": l.source_line_no,
                            "target": l.target_line_no or "",
                            "type": l.line_type,
                            "style": _line_type_style[l.line_type],
                            "value": l.value,
                        }
                    )
                for l in hunk.target_lines():
                    if l.source_line_no is not None:
                        continue
                    if not l.target_line_no in lines:
                        lines[l.target_line_no] = []
                    lines[l.target_line_no].append(
                        {
                            "source": l.source_line_no or "",
                            "target": l.target_line_no,
                            "type": l.line_type,
                            "style": _line_type_style[l.line_type],
                            "value": l.value,
                        }
                    )
                hunk_helper[
                    (
                        file.source_file,
                        file.target_file,
                        hunk.source_start,
                        hunk.source_length,
                    )
                ] = lines

        return render_template(
            "diff.html",
            title="{} - diff {} {}".format(self.pagename, rev_a, rev_b),
            pagepath=self.pagepath,
            pagename=self.pagename,
            patchset=patchset,
            hunk_helper=hunk_helper,
            rev_a=rev_a,
            rev_b=rev_b,
        )

    def history(self, rev_a=None, rev_b=None):
        if not has_permission("READ"):
            abort(403)
        try:
            orig_log = storage.log(self.filename)
        except StorageNotFound:
            return render_template("page404.html", pagename=self.pagename, pagepath=self.pagepath), 404
        if rev_a is not None and rev_b is not None and rev_a != rev_b:
            return self.diff(rev_a=rev_a, rev_b=rev_b)

        log = []
        for orig_entry in orig_log:
            entry = dict(orig_entry)
            entry["url"] = url_for(
                "view", path=self.pagepath, revision=entry["revision"]
            )
            log.append(entry)
        return render_template(
            "history.html",
            title="{} - History".format(self.pagename),
            pagename=self.pagename,
            pagepath=self.pagepath,
            log=log,
            rev_a=rev_a,
            rev_b=rev_b,
            breadcrumbs=self.breadcrumbs(),
        )

    def rename(self, new_pagename, message, author):
        if not has_permission("WRITE"):
            abort(403)
        # filename
        new_filename = get_filename(new_pagename)
        # check for attachments
        files, directories = storage.list(self.attachment_directoryname)
        if (len(files) + len(directories)) > 0:
            # rename attachment directory
            new_attachment_directoryname = get_attachment_directoryname(new_filename)
            # rename attachment directory
            storage.rename(
                self.attachment_directoryname,
                new_attachment_directoryname,
                author=author,
                message=message,
                no_commit=True,
            )
        # rename page
        storage.rename(self.filename, new_filename, message=message, author=author)

    def handle_rename(self, new_pagename, message, author):
        if not has_permission("WRITE"):
            abort(403)
        if empty(new_pagename):
            toast("Please provide a name.", "error")
        elif sanitize_pagename(new_pagename) != new_pagename:
            toast("Please check the pagename ...", "warning")
            new_pagename = sanitize_pagename(new_pagename)
        elif new_pagename == self.pagename:
            toast("New and old name are the same.", "error")
        else:
            # rename
            if empty(message):
                message = "Renamed {} to {}.".format(self.pagename, new_pagename)
            try:
                self.rename(new_pagename, message, author)
            except Exception as e:
                # I tried to plumb an error message in here, but it did not show up in the UI - turns out these messages
                # get stored in the cookie, and some browsers don't like big cookies:
                # https://flask.palletsprojects.com/en/2.2.x/patterns/flashing/
                #   "Note that browsers and sometimes web servers enforce a limit on cookie sizes. This means that
                #    flashing messages that are too large for session cookies causes message flashing to fail silently."
                toast("Renaming failed.", "error")
            else:
                return redirect(url_for("view", path=new_pagename))
        return self.rename_form(new_pagename, message)

    def rename_form(self, new_pagename=None, message=None):
        if not has_permission("WRITE"):
            abort(403)
        return render_template(
            "rename.html",
            title="Rename {}".format(self.pagename),
            pagepath=self.pagepath,
            pagename=self.pagename,
            new_pagename=new_pagename,
            message=message,
        )

    def delete(self, message, author):
        if not has_permission("WRITE"):
            abort(403)
        if empty(message):
            message = "{} deleted.".format(self.pagename)
        storage.delete([self.filename, self.attachment_directoryname], 
                        message=message, author=author)
        toast("{} deleted.".format(self.pagename))
        return redirect(url_for("changelog"))

    def delete_form(self):
        if not has_permission("WRITE"):
            abort(403)
        # count attachments and subpages
        files, directories = storage.list(self.attachment_directoryname)
        if len(files)>0:
            title="Delete {} and the {} file(s) attached?".format(self.pagename, len(files))
        else:
            title="Delete {} ?".format(self.pagename)
        return render_template(
            "delete.html",
            title=title,
            pagepath=self.pagepath,
            pagename=self.pagename,
        )

    def _attachments(self):
        files, directories = storage.list(self.attachment_directoryname)
        # currently only attached files are handled
        return [
            Attachment(
                self.pagepath, f
            )
            for f in files
        ]

    def render_attachments(self):
        if not has_permission("READ"):
            abort(403)
        files = [f.data for f in self._attachments() if f.metadata is not None]
        return render_template(
            "attachments.html",
            title="{} - Attachments".format(self.pagename),
            pagepath=self.pagepath,
            pagename=self.pagename,
            files=files,
            breadcrumbs=self.breadcrumbs(),
        )

    def upload_attachments(self, files, message, filename, author, inline=False):
        if not has_permission("UPLOAD"):
            abort(403)
        # attachments to commit in the second step
        to_commit = []
        for upload in files:
            if upload.filename == "":
                # no file selected
                continue
            if not empty(filename):
                fn = secure_filename(filename)
            else:
                fn = secure_filename(upload.filename)
            attachment = Attachment(self.pagepath, fn)
            # make sure the directory exists
            os.makedirs(attachment.absdirectory, mode=0o775, exist_ok=True)
            upload.save(attachment.abspath)
            to_commit.append(attachment)
        if len(to_commit) > 0:
            if filename is None:
                toastmsg = "Added attachment(s): {}.".format(
                    ", ".join([c.filename for c in to_commit])
                )
            else:
                toastmsg = "Updated attachment: {}.".format(
                    ", ".join([c.filename for c in to_commit])
                )
            # default message
            if empty(message):
                message = toastmsg
            storage.commit(
                [a.filepath for a in to_commit], message=message, author=author
            )
            if not inline:
                toast(toastmsg)
        if inline:
            attachment_url = url_for(
                "get_attachment", pagepath=self.pagepath, filename=fn
            )
            return jsonify(filename=attachment_url)
        return redirect(url_for("attachments", pagepath=self.pagepath))

    def get_attachment(self, filename, revision=None):
        return Attachment(self.pagepath, filename, revision).get()

    def get_attachment_thumbnail(self, filename, size=80, revision=None):
        return Attachment(self.pagepath, filename, revision).get_thumbnail()

    def edit_attachment(self, filename, author, new_filename=None, message=None, delete=None):
        if not has_permission("READ"):
            abort(403)
        a = Attachment(self.pagepath, filename)
        if not a.exists():
            return abort(404)
        if not empty(delete):
            if not has_permission("WRITE"):
                return abort(403)
            return a.delete(message=message, author=author)
        # rename
        if not empty(new_filename):
            if not has_permission("WRITE"):
                return abort(403)
            if new_filename != filename:
                return a.rename(new_filename, message=message, author=author)
        # show edit form
        return a.edit()


class Attachment:
    def __init__(self, pagepath, filename, revision=None):
        self.pagepath = pagepath
        self.filename = filename
        self.revision = revision
        self.absdirectory = os.path.join(
            storage.path, get_attachment_directoryname(get_filename(pagepath))
        )
        self.directory = get_attachment_directoryname(get_filename(pagepath))
        self.filepath = os.path.join(self.directory, filename)
        self.abspath = os.path.join(storage.path, self.filepath)
        self.mimetype = guess_mimetype(self.filepath)
        try:
            self.metadata = storage.metadata(self.filepath, revision=self.revision)
            self.message = self.metadata["message"]
            self._revision = self.metadata["revision"]
            self.author_name = self.metadata["author_name"]
            self.author_email = self.metadata["author_email"]
            self.datetime = self.metadata["datetime"]
        except StorageNotFound:
            self.metadata = None
            self.message = None
            self.author_name = None
            self.author_email = None
            self.datetime = None
            self._revision = None

    def exists(self):
        return os.path.exists(self.abspath)

    def get_thumbnail_url(self):
        if self.mimetype is not None and self.mimetype.startswith("image"):
            return url_for(
                "get_attachment_thumbnail",
                pagepath=self.pagepath,
                filename=self.filename,
            )
        return None

    def get_thumbnail_icon(self):
        if self.mimetype is not None:
            if self.mimetype == "application/pdf":
                return '<i class="far fa-file-pdf" style="font-size:48px;"></i>'
            if self.mimetype.startswith("text"):
                return '<i class="far fa-file-alt" style="font-size:48px;"></i>'
        return '<i class="far fa-file" style="font-size:48px;"></i>'

    @property
    def data(self):
        return {
            "filename": self.filename,
            "filepath": self.filepath,
            "url": url_for(
                "get_attachment",
                pagepath=self.pagepath,
                filename=self.filename,
                revision=self.revision,
            ),
            "thumbnail_url": self.get_thumbnail_url(),
            "thumbnail_icon": self.get_thumbnail_icon(),
            "filesize": sizeof_fmt(os.stat(self.abspath).st_size),
            "datetime": self.datetime,
            "mimetype": self.mimetype,
            "revision": self._revision,
            "author_name": self.author_name,
            "author_email": self.author_email,
            "message": self.message,
        }

    def __repr__(self):
        return "<Attachemnt '{}' of '{}'>".format(self.filename, self.pagepath)

    def rename(self, new_filename, message, author):
        if not has_permission("UPLOAD"):
            abort(403)
        toast_message = "Renamed {} to {}".format(self.filename, new_filename)
        new_filepath = os.path.join(self.directory, new_filename)
        if empty(message):
            message = toast_message
        try:
            storage.rename(self.filepath, new_filepath, message=message, author=author)
        except StorageError:
            toast("Renaming failed", "error")
            return redirect(
                url_for("attachments", pagepath=self.pagepath)
            )
        toast(toast_message)
        return redirect(
            url_for("edit_attachment", pagepath=self.pagepath, filename=new_filename)
        )

    def delete(self, message, author):
        if not has_permission("WRITE"):
            abort(403)
        toast_message = "Deleted {}".format(self.filename)
        if empty(message):
            message = toast_message
        try:
            storage.delete(self.filepath, message=message, author=author)
            toast(toast_message)
        except StorageError:
            toast("Deleting failed", "error")
        return redirect(url_for("attachments", pagepath=self.pagepath))


    def edit(self):
        if not has_permission("READ"):
            abort(403)
        if not self.exists():
            return abort(404)
        # fetch attachment histoy
        try:
            orig_log = storage.log(self.filepath)
        except StorageNotFound:
            return abort(404)
        # enrich log
        log = []
        for entry in orig_log:
            log.append(entry)
        return render_template(
            "edit_attachment.html",
            title="Edit {}".format(self.filename),
            pagepath=self.pagepath,
            filename=self.filename,
            log=log,
            breadcrumbs=get_breadcrumbs(self.pagepath),
        )

    def get(self):
        if not has_permission("READ"):
            abort(403)
        if not self.exists():
            return abort(404)
        if self.revision is None:
            if not storage.exists(self.filepath):
                return abort(404)
            # headers are already set correctly by send_file
            return make_response(send_file(self.abspath))
        else:
            # revision is given
            try:
                content = storage.load(self.filepath, revision=self.revision, mode="rb")
                metadata = storage.metadata(self.filepath, revision=self.revision)
            except StorageNotFound:
                abort(404)
            # create buffer
            buffer = BytesIO()
            try:
                buffer.write(content)
            except:
                abort(500)
            buffer.seek(0)
            # create response
            response = make_response(send_file(buffer, mimetype=self.mimetype))

        # set header, caching, etc
        response.headers["Date"] = http_date(self.datetime.utctimetuple())
        response.headers["Expires"] = http_date(
            (self.datetime + timedelta(hours=1)).utctimetuple()
        )
        response.headers["Last-Modified"] = http_date(self.datetime.utctimetuple())

        return response

    def get_thumbnail(self, size=80):
        if not has_permission("READ"):
            abort(403)
        if (
            not self.exists()
            or not self.mimetype.startswith("image")
            or self.metadata is None
        ):
            return abort(404)
        from timeit import default_timer as timer

        t_start = timer()
        image = PIL.Image.open(BytesIO(storage.load(self.filepath, mode="rb")))
        # resample thumbnail
        image.thumbnail((size, size), resample=PIL.Image.Resampling.LANCZOS)
        # create byteobject
        buffer = BytesIO()
        # store image in byteobject
        image.save(buffer, format=image.format, quality=80)
        buffer.seek(0)
        app.logger.info(
            "Thumbnail generation took {:.3f} seconds.".format(timer() - t_start)
        )
        # build response
        response = make_response(send_file(buffer, mimetype=self.mimetype))
        response.headers["Date"] = http_date(self.datetime.utctimetuple())
        response.headers["Expires"] = http_date(
            (self.datetime + timedelta(hours=1)).utctimetuple()
        )
        response.headers["Last-Modified"] = http_date(self.datetime.utctimetuple())

        return response


class Search:
    def __init__(
        self, query, is_casesensitive=False, is_regexp=False, in_history=False
    ):
        self.query = query
        self.in_history = in_history
        self.is_regexp = is_regexp
        self.is_casesensitive = is_casesensitive
        self.re = None

    def compile(self):
        if empty(self.query):
            return
        if not self.is_regexp:
            self.needle = "(" + re.escape(self.query) + ")"
        else:
            self.needle = "(" + self.query + ")"
        try:
            # compile regexp
            if self.is_casesensitive:
                self.re = re.compile(self.needle)
            else:
                self.re = re.compile(self.needle, re.IGNORECASE)
            self.rei = re.compile(self.needle, re.IGNORECASE)
        except Exception as e:
            toast("Error in search term: {}".format(e.msg), "error")
            return

    def search(self):
        if self.re is None:
            return {}
        # find all markdown files
        files, _ = storage.list()
        md_files = [filename for filename in files if filename.endswith(".md")]
        fn_result = {}

        for fn in md_files:
            # check if pagename matches
            mi = self.rei.search(get_pagename(fn))
            if mi is not None:
                fn_result[fn] = [True, "{}".format(get_pagename(fn, full=True))]
            # open file, read file
            haystack = storage.load(fn)
            lastlinematched = False
            for i, line in enumerate(haystack.splitlines()):
                m = self.re.search(line)
                if m:
                    if fn not in fn_result:
                        fn_result[fn] = [False]
                    if lastlinematched or i == 0:
                        fn_result[fn] += [line]
                    else:
                        fn_result[fn] += ["[..]", line]
                    lastlinematched = True
                else:
                    lastlinematched = False
        if self.in_history:
            # TODO
            # use git log -S
            # see https://git-scm.com/docs/git-log#Documentation/git-log.txt--Sltstringgt
            # search trough commits to find the one that added the string
            pass

        result = {}
        # simplify result
        for fn, matches in fn_result.items():
            fnmatch = 1 if matches.pop(0) else 0
            # count matches
            n = 0
            for i, line in enumerate(matches):
                # filenames are not casesensitive ...
                if i == 0 and fnmatch == 1:
                    n += len(self.rei.findall(line))
                else:
                    n += len(self.re.findall(line))
            key = (fnmatch, n, fn, get_pagename(fn, full=True))
            summary = []
            if fnmatch == 1:
                summary = [matches.pop(0)]
            front, end = [], []
            while len("".join(front) + "".join(end)) < 200:
                try:
                    front.insert(0, matches.pop(0))
                    end.insert(0, matches.pop(-1))
                except IndexError:
                    break
            match_summary = " ".join(front)
            if len(matches) > 0:
                match_summary += "[..]"
            match_summary += " ".join(end)
            # TODO: check if the number of words have to be limited, too
            match_summary = match_summary.replace("[..][..]", "[..]")
            summary.append(match_summary)
            # colorize summary
            for i, l in enumerate(summary):
                # are you kidding me? html_escape(l) is evaluated later so that the span below
                # would be escaped too.
                l = str(html_escape(l))
                # filenames are not casesensitive ...
                if i == 0 and fnmatch == 1:
                    summary[i] = 'Name "{}" matches.'.format(
                        self.rei.sub(r'<span class="text-match">\1</span>', l)
                    )
                else:
                    summary[i] = self.re.sub(r'<span class="text-match">\1</span>', l)
            # store summary with key
            result[key] = summary

        return result

    def render(self):
        if not has_permission("READ"):
            abort(403)
        self.compile()
        result = self.search()
        # sort keys
        keys = sorted(result.keys(), key=lambda x: (-x[0], -x[1], x[2]))
        return render_template(
            "search.html",
            title="Search '{}'".format(self.query)
            if not empty(self.query)
            else "Search",
            query=self.query,
            in_history=self.in_history,
            is_regexp=self.is_regexp,
            is_casesensitive=self.is_casesensitive,
            keys=keys,
            result=result,
        )


# vim: set et ts=8 sts=4 sw=4 ai:
