#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import re
from collections import namedtuple
from unidiff import PatchSet
from flask import (
    redirect,
    abort,
    url_for,
    render_template,
    make_response,
    send_file,
    jsonify,
    session,
)
from markupsafe import escape as html_escape
from otterwiki.gitstorage import StorageNotFound, StorageError
from otterwiki.server import app, storage, db, app_renderer
from otterwiki.models import Drafts
from otterwiki.renderer import pygments_render
from otterwiki.sidebar import SidebarPageIndex, SidebarMenu
from otterwiki.util import (
    split_path,
    join_path,
    empty,
    guess_mimetype,
    sizeof_fmt,
    get_pagepath,
    get_page_directoryname,
    sanitize_pagename,
    patchset2filedict,
    get_header,
)
from otterwiki.helper import (
    toast,
    auto_url,
    get_filename,
    get_attachment_directoryname,
    get_pagename,
    get_pagename_prefixes,
    patchset2urlmap,
    get_breadcrumbs,
    upsert_pagecrumbs,
)
from otterwiki.auth import has_permission, current_user
from otterwiki.plugins import chain_hooks
from datetime import timedelta, datetime, UTC
from timeit import default_timer as timer
from werkzeug.http import http_date
from werkzeug.utils import secure_filename
from urllib.parse import unquote
from io import BytesIO

import PIL.Image

if not hasattr(PIL.Image, 'Resampling'):  # Pillow<9.0
    PIL.Image.Resampling = PIL.Image


class PageIndex:
    def __init__(self, path=None):
        '''
        This will generate an index of pages/toc of pages from a given path.
        '''
        self.toc = {}
        page_indices = []

        if path is not None:
            self.path = (
                path if app.config["RETAIN_PAGE_NAME_CASE"] else path.lower()
            )
            self.path = self.path.rstrip("/")
            self.breadcrumbs = get_breadcrumbs(
                get_pagename(
                    path,
                    full=True,
                )
            )
            self.index_depth = len(split_path(self.path))
        else:
            self.path, self.breadcrumbs = None, None
            self.index_depth = 0

        t_start = timer()
        # get all files in the storage
        files, _ = storage.list(p=self.path)
        app.logger.debug(
            f"PageIndex({self.path}) storage.list() files took {timer() - t_start:.3f} seconds."
        )
        # restart timer
        t_start = timer()
        # filter .md files
        md_files = [f for f in files if f.endswith(".md")]
        for fn in md_files:
            if self.path is None:
                f = fn
            else:
                f = os.path.join(self.path, fn)
            page_depth = len(split_path(f)) - 1
            firstletter = get_pagename(fn, full=True)[0].upper()
            if firstletter not in self.toc.keys():
                self.toc[firstletter] = []
            # add the subdirectories the page is in to the page index
            subdirectories = split_path(fn)[:-1]
            for subdir_depth in range(len(subdirectories)):
                subdir_path = join_path(subdirectories[0 : subdir_depth + 1])
                if self.path is None:
                    subdir_path_full = subdir_path
                else:
                    subdir_path_full = join_path([self.path, subdir_path])
                if storage.exists(
                    get_filename(
                        subdir_path,
                    )
                ):
                    # if page exists don't add the directory
                    continue
                if subdir_path not in page_indices:
                    self.toc[firstletter].append(
                        (
                            subdir_depth,
                            get_pagename(
                                subdir_path,
                                full=False,
                            )
                            + "/",  # title
                            url_for(
                                "view",
                                path=get_pagename(
                                    subdir_path_full,
                                    full=True,
                                ),
                            ),  # url
                            [],
                            True,
                        )
                    )
                    page_indices.append(subdir_path)
            pagetoc = []
            # default pagename is the pagename derived from the filename
            pagename = get_pagename(
                f,
                full=False,
            )
            # read file
            content = storage.load(f)
            # parse file contents
            _, ftoc = app_renderer.markdown(content)
            # add headers to page toc
            # (4, '2 L <strong>bold</strong>', 1, '2 L bold', '2-l-bold')
            for i, header in enumerate(ftoc):
                if i == 0 and len(pagetoc) == 0:
                    # overwrite pagename with the first header found on the page as hint for upper/lower casing
                    pagename = get_pagename(
                        f,
                        full=False,
                        header=header[3],
                    )
                else:
                    pagetoc.append(
                        (
                            header[2],  # depth
                            header[3],  # title without formatting
                            url_for(
                                "view",
                                path=get_pagename(
                                    f,
                                    full=True,
                                    header=pagename,
                                ),
                                _anchor=header[4],
                            ),
                        )
                    )
            # strip self.path from displayname
            displayname = pagename
            if self.path is not None and displayname.lower().startswith(
                self.path.lower()
            ):
                displayname = displayname[len(self.path) + 1 :]
            has_children = False
            for other in md_files:
                if other.startswith(f[:-3] + "/"):
                    has_children = True
                    break
            self.toc[firstletter].append(
                (
                    page_depth - self.index_depth,
                    displayname,  # title
                    url_for(
                        "view",
                        path=get_pagename(
                            f,
                            full=True,
                            header=pagename,
                        ),
                    ),  # url
                    pagetoc,
                    has_children,
                )
            )

        app.logger.debug(
            f"PageIndex({self.path}) parsing files took {timer() - t_start:.3f} seconds."
        )

    def render(self):
        if not has_permission("READ"):
            abort(403)
        menutree = SidebarPageIndex(get_page_directoryname(self.path or "/"))

        upsert_pagecrumbs(get_pagename(self.path or "/", full=True))
        return render_template(
            "pageindex.html",
            title="Page Index",
            pages=self.toc,
            pagepath=self.path or "/",
            menutree=menutree.query(),
            custom_menu=SidebarMenu().query(),
            breadcrumbs=self.breadcrumbs,
        )

    def pages(self):
        for letter in self.toc:
            for _, pagename, url, _, _ in self.toc[letter]:
                pagepath = unquote(url)[1:]
                yield pagename, pagepath, url


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
                (
                    entry["files"][filename]["name"],
                    entry["files"][filename]["url"],
                ) = auto_url(
                    filename,
                    entry["revision"],
                )
            log.append(entry)
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
            start_n = 0
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
                if (commit_i >= start_n) and (
                    commit_i < start_n + self.commit_count
                ):
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
        # store first and last page
        first_page = pages[0]["revision"]
        last_page = pages[-1]["revision"]
        # thin out pages
        page_span = 4
        max_pages = 8
        if len(pages) > max_pages:
            # calculate how many pages would be displayed left and right of the active page
            l_len = active_page - max(1, active_page - page_span)
            r_len = min(active_page + page_span, len(pages)) - active_page
            # to have a fixed length of displayed pages add the missing
            # lengths to the respectively other side
            if l_len < page_span:
                r_len += page_span - l_len
            if r_len < page_span:
                l_len += page_span - r_len
            # calculate array positions
            l_pos = active_page - l_len - 1
            r_pos = active_page + r_len
            # left of active page
            pages_short = pages[l_pos:active_page]
            if l_pos > 0:
                # insert dummy (and remove page to not break the layout)
                pages_short = [{"dummy": True}] + pages_short[1:]
            # right of active page
            pages_short += pages[active_page:r_pos]
            if r_pos < len(pages):
                # insert dummy (and remove page to not break the layout)
                pages_short = pages_short[:-1] + [{"dummy": True}]
            # use the shorter page list
            pages = pages_short

        menutree = SidebarPageIndex(get_page_directoryname("/"))
        return render_template(
            "changelog.html",
            log=log,
            title="Changelog",
            pages=pages,
            first_page=first_page,
            last_page=last_page,
            previous_page=previous_page,
            next_page=next_page,
            menutree=menutree.query(),
            custom_menu=SidebarMenu().query(),
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

    def show_commit(self, revision):
        if not has_permission("READ"):
            abort(403)
        try:
            metadata, diff = storage.show_commit(revision)
        except StorageError as e:
            app.logger.error(e)
            abort(404)

        patchset = PatchSet(diff)
        pagepath = None

        url_map = patchset2urlmap(patchset, revision)
        if len(url_map) == 1:
            pagepath = get_pagepath(get_pagename(list(url_map.keys())[0]))

        menutree = SidebarPageIndex(get_page_directoryname(pagepath or "/"))

        file_diffs = patchset2filedict(patchset)
        return render_template(
            "diff.html",
            title="commit {}".format(revision),
            metadata=metadata,
            url_map=url_map,
            file_diffs=file_diffs,
            patchset=patchset,
            revision=revision,
            withlinenumbers=False,
            pagepath=pagepath,
            breadcrumbs=get_breadcrumbs(pagepath),
            menutree=menutree.query(),
            custom_menu=SidebarMenu().query(),
        )


class Page:
    def __init__(self, pagepath=None, pagename=None, revision=None):

        if pagepath is not None:
            self.pagepath = sanitize_pagename(pagepath)
            self.pagename = get_pagename(pagepath)
        elif pagename is not None:
            self.pagename = sanitize_pagename(pagename)
            self.pagepath = get_pagepath(pagename)

        self.page_url = url_for("view", path=self.pagepath)

        self.pagename_full = get_pagename(self.pagepath, full=True)
        self.revision = revision

        self.filename = get_filename(self.pagepath)
        self.attachment_directoryname = get_attachment_directoryname(
            self.filename
        )

        # load page content and metadata
        try:
            self.content, self.metadata = self.load(revision=self.revision)
            self.exists = True
        except StorageNotFound:
            self.metadata = None
            self.content = None
            self.exists = False

        if self.content is not None:
            header = get_header(self.content)
            self.pagename = get_pagename(
                self.pagepath, full=False, header=header
            )
            self.pagename_full = get_pagename(
                self.pagepath, full=True, header=header
            )

    def breadcrumbs(self):
        return get_breadcrumbs(self.pagepath)

    def load(self, revision):
        metadata = None
        content = None
        try:
            content = storage.load(self.filename, revision=revision)
            metadata = storage.metadata(self.filename, revision=revision)
        except StorageNotFound as e:
            if all([not metadata, not content]):
                # If both are None, raise the exception. Otherwise, a warning will show on the page that
                # the file is not under version control.
                raise

        return content, metadata

    def exists_or_404(self):
        if not self.exists:
            app.logger.warning("Not found {}".format(self.pagename))
            response404 = make_response(
                render_template(
                    "page404.html",
                    pagename=self.pagename_full,
                    pagepath=self.pagepath,
                ),
                404,
            )
            abort(response404)
        return True

    def source(self, raw=False):
        # handle permissions
        if not has_permission("READ"):
            abort(403)
        # handle case that the page doesn't exists
        self.exists_or_404()

        # set title
        title = self.pagename
        if self.revision is not None:
            title = "{} ({})".format(self.pagename, self.revision)

        if raw:
            if self.content is None:
                self.content = ""
            # build a reference link that is appended to the content as markdown comment
            reference = f"\n[]: # ({url_for('source', pagepath=self.pagepath, _external=True)})"
            return (
                self.content + reference,
                200,
                {'Content-Type': 'text/plain; charset=utf-8'},
            )

        source = pygments_render(self.content, lang='markdown')
        menutree = SidebarPageIndex(get_page_directoryname(self.pagepath))

        return render_template(
            "source.html",
            title=title,
            revision=self.revision,
            pagename=self.pagename,
            pagepath=self.pagepath,
            menutree=menutree.query(),
            custom_menu=SidebarMenu().query(),
            source=source,
            breadcrumbs=self.breadcrumbs(),
        )

    def view(self):
        # handle permissions
        if not has_permission("READ"):
            if current_user.is_authenticated and not current_user.is_approved:
                toast(
                    "You lack the permissions to access this wiki. Please wait for approval."
                )
            elif current_user.is_authenticated and current_user.is_approved:
                toast(
                    "You are logged in but lack READ permissions. Please wait for an administrator to grant access."
                )
            else:
                toast(
                    "You lack the permissions to access this wiki. Please login."
                )
            return redirect(url_for("login"))
        # handle case that page doesn't exists
        self.exists_or_404()

        upsert_pagecrumbs(get_pagename(self.pagepath, full=True))

        danger_alert = False
        if not self.metadata:
            danger_alert = [
                "Not under version control",
                f"""This page was loaded from the repository but is not added under git version control. Make a commit on the <a href="/{self.pagepath}/edit" class="alert-link">Edit page</a> to add it.""",
            ]

        # render markdown
        htmlcontent, toc = app_renderer.markdown(self.content, page_url=self.page_url)

        if len(toc) > 0:
            # use first headline to overwrite pagename
            self.pagename = get_pagename(
                self.pagename,
                full=False,
                header=toc[0][3],
            )

        # set title
        title = self.pagename
        if self.revision is not None:
            title = "{} ({})".format(self.pagename, self.revision)

        menutree = SidebarPageIndex(get_page_directoryname(self.pagepath))

        htmlcontent = chain_hooks(
            "page_view_htmlcontent_postprocess", htmlcontent, self
        )

        # render template
        return render_template(
            "page.html",
            title=title,
            revision=self.revision,
            pagename=self.pagename,
            pagepath=self.pagepath,
            htmlcontent=htmlcontent,
            toc=toc,
            breadcrumbs=self.breadcrumbs(),
            danger_alert=danger_alert,
            menutree=menutree.query(),
            custom_menu=SidebarMenu().query(),
        )

    def preview(self, content=None, cursor_line=None):
        if content is None:
            # handle case that the page doesn't exists
            self.exists_or_404()
            # no content in form use loaded page
            content = self.content

        # render preview html from markdown
        content_html, toc = app_renderer.markdown(content, cursor=cursor_line, page_url=self.page_url)
        # update pagename from toc
        if len(toc) > 0:
            # use first headline to overwrite pagename
            self.pagename = get_pagename(
                self.pagename,
                full=False,
                header=toc[0][3],
            )

        # render toc into the html template
        toc_html = render_template(
            "snippets/toc.html",
            toc=toc,
        )
        # render preview into the html template
        preview_html = render_template(
            "preview.html",
            pagename=self.pagename,
            pagepath=self.pagepath,
            content_html=content_html,
            breadcrumbs=self.breadcrumbs(),
        )

        return {
            "preview_content": preview_html,
            "preview_toc": toc_html,
        }

    def editor(self, author, handle_draft=None):
        if not has_permission("WRITE"):
            abort(403)
        if self.exists:
            content = self.content
            # FIXME: This could be improved by storing the last position a user
            #        edited on a page.
            cursor_line = 0
            cursor_ch = 0
        else:
            content = f"# {self.pagename}\n\n"
            # Place the cursor in the beginning of the first (empty) line of the\
            # new document
            cursor_line = 2
            cursor_ch = 0

        # check Drafts
        draft = self.load_draft(author=author)
        if draft is not None:
            if handle_draft is None:
                return render_template(
                    "draft.html",
                    pagename=self.pagename,
                    pagepath=self.pagepath,
                    revision=(
                        self.metadata["revision"] if self.metadata else None
                    ),
                    draft_revision=self.revision,
                    content=(
                        pygments_render(self.content, lang='markdown')
                        if self.content
                        else None
                    ),
                    draft_content=pygments_render(
                        draft.content, lang='markdown'
                    ),
                    draft_datetime=draft.datetime.astimezone(UTC),
                )
            if handle_draft == "discard":
                self.discard_draft(author=author)
            if handle_draft == "edit":
                content = draft.content
                cursor_line = draft.cursor_line
                cursor_ch = draft.cursor_ch

        # get file listing
        files = [f.data for f in self._attachments() if f.metadata is not None]
        # get page listing
        page_idx = PageIndex()

        return render_template(
            "editor.html",
            pagename=self.pagename,
            pagepath=self.pagepath,
            content_editor=content,
            files=files,
            pages=list(page_idx.pages()),
            cursor_line=cursor_line,
            cursor_ch=cursor_ch,
            revision=(
                self.metadata.get("revision", "") if self.metadata else ""
            ),
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
            toast("{} saved.".format(self.pagename_full))
        # take care of drafts
        self.discard_draft(author)
        # redirect to view
        return redirect(url_for("view", path=self.pagepath))

    def create(self):
        if not has_permission("WRITE"):
            abort(403)

        if self.exists:
            toast("{} exists already.".format(self.pagename), "warning")

        return redirect(url_for("edit", path=self.pagepath))

    def blame(self):
        if not has_permission("READ"):
            abort(403)
        # handle case that the page doesn't exists
        self.exists_or_404()

        data = storage.blame(self.filename, self.revision)

        markup_lines = pygments_render(self.content, lang="markdown")
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
                fdata.append(
                    (
                        row[0],
                        row[1],
                        row[2],
                        int(row[3]),
                        line,
                        f"chunk-start chunk-start-{oddeven}",
                        row[0],
                    )
                )
                last = row[0]
            else:
                fdata.append(("", "", "", int(row[3]), line, oddeven, row[0]))
        menutree = SidebarPageIndex(get_page_directoryname(self.pagepath))
        return render_template(
            "blame.html",
            title="{} - blame {}".format(self.pagename, self.revision),
            pagepath=self.pagepath,
            pagename=self.pagename,
            blame=fdata,
            menutree=menutree.query(),
            custom_menu=SidebarMenu().query(),
            breadcrumbs=self.breadcrumbs(),
        )

    def diff(self, rev_a=None, rev_b=None):
        if not has_permission("READ"):
            abort(403)
        # handle case that the page doesn't exists
        self.exists_or_404()

        diff = storage.diff(rev_a, rev_b)
        patchset = PatchSet(diff)
        url_map = patchset2urlmap(patchset, rev_b, rev_a)
        file_diffs = patchset2filedict(patchset)

        menutree = SidebarPageIndex(get_page_directoryname(self.pagepath))
        return render_template(
            "diff.html",
            title="{} - diff {} {}".format(self.pagename, rev_a, rev_b),
            pagepath=self.pagepath,
            pagename=self.pagename,
            page_filename=self.filename,
            file_diffs=file_diffs,
            patchset=patchset,
            url_map=url_map,
            rev_a=rev_a,
            rev_b=rev_b,
            withlinenumbers=False,
            menutree=menutree.query(),
            custom_menu=SidebarMenu().query(),
            breadcrumbs=self.breadcrumbs(),
        )

    def history(self, rev_a=None, rev_b=None):
        if not has_permission("READ"):
            abort(403)
        try:
            orig_log = storage.log(self.filename)
        except StorageNotFound:
            return (
                render_template(
                    "page404.html",
                    pagename=self.pagename,
                    pagepath=self.pagepath,
                ),
                404,
            )
        if rev_a is not None and rev_b is not None and rev_a != rev_b:
            return redirect(
                url_for("diff", path=self.pagepath, rev_a=rev_a, rev_b=rev_b)
            )

        log = []
        for i, orig_entry in enumerate(orig_log):
            if len(orig_log) > 1 and i == 0 and rev_b is None:
                rev_b = orig_entry['revision']
            elif len(orig_log) > 1 and i == 1 and rev_a is None:
                rev_a = orig_entry['revision']
            entry = dict(orig_entry)
            entry["url"] = url_for(
                "view", path=self.pagepath, revision=entry["revision"]
            )
            log.append(entry)
        menutree = SidebarPageIndex(get_page_directoryname(self.pagepath))
        return render_template(
            "history.html",
            title="{} - History".format(self.pagename),
            pagename=self.pagename,
            pagepath=self.pagepath,
            log=log,
            rev_a=rev_a,
            rev_b=rev_b,
            menutree=menutree.query(),
            custom_menu=SidebarMenu().query(),
            breadcrumbs=self.breadcrumbs(),
        )

    def rename(self, new_pagename, message, author):
        if not has_permission("WRITE"):
            abort(403)
        # filename
        new_filename = get_filename(new_pagename)
        # check for attachments
        files, directories = storage.list(self.attachment_directoryname)

        # handle case that the page and no attachments exist
        if not self.exists and (len(files) + len(directories)) == 0:
            self.exists_or_404()

        if (len(files) + len(directories)) > 0:
            # rename attachment directory
            new_attachment_directoryname = get_attachment_directoryname(
                new_filename
            )
            # rename attachment directory
            storage.rename(
                self.attachment_directoryname,
                new_attachment_directoryname,
                author=author,
                message=message,
                # if self.exists, do not commit yet, commit will follow below, when the md file is renamed
                # if not self.exists, do commit, since no md file will be renamed
                no_commit=self.exists,
            )
        # rename page
        if self.exists:
            storage.rename(
                self.filename, new_filename, message=message, author=author
            )

    def handle_rename(self, new_pagename, message, author):
        if not has_permission("WRITE"):
            abort(403)
        if empty(new_pagename):
            toast("Please provide a name.", "error")
        elif sanitize_pagename(new_pagename) != new_pagename:
            toast("Please check the pagename ...", "warning")
            new_pagename = sanitize_pagename(new_pagename)
        elif get_pagename(new_pagename, full=True) == self.pagepath:
            toast("New and old name are the same.", "error")
        elif Page(new_pagename).exists:
            toast(
                f"Unable to rename: {new_pagename} already exists.", "warning"
            )
        else:
            # rename
            if empty(message):
                message = "Renamed {} to {}.".format(
                    self.pagename, new_pagename
                )
            try:
                self.rename(new_pagename, message, author)
            except Exception as e:
                # I tried to plumb an error message in here, but it did not show up in the UI - turns out these messages
                # get stored in the cookie, and some browsers don't like big cookies:
                # https://flask.palletsprojects.com/en/2.2.x/patterns/flashing/
                #   "Note that browsers and sometimes web servers enforce a limit on cookie sizes. This means that
                #    flashing messages that are too large for session cookies causes message flashing to fail silently."
                toast("Renaming failed.", "error")
                app.logger.error(f"Renaming failed: {e}")
            else:
                return redirect(url_for("view", path=new_pagename))
        return self.rename_form(new_pagename, message)

    def rename_form(self, new_pagename=None, message=None):
        if not has_permission("WRITE"):
            abort(403)
        menutree = SidebarPageIndex(get_page_directoryname(self.pagepath))
        olddrafts = Drafts.query.filter_by(pagepath=self.pagepath).all()
        if new_pagename != self.pagepath:
            newdrafts = Drafts.query.filter_by(
                pagepath=get_pagepath(new_pagename)
            ).all()
        else:
            newdrafts = []

        return render_template(
            "rename.html",
            title="Rename {}".format(self.pagename),
            pagepath=self.pagepath,
            pagename=self.pagename_full,
            new_pagename=new_pagename,
            message=message,
            menutree=menutree.query(),
            custom_menu=SidebarMenu().query(),
            olddrafts=olddrafts,
            newdrafts=newdrafts,
            pagename_prefixes=get_pagename_prefixes(
                filter=[self.pagename, self.pagename_full]
            ),
        )

    def delete(self, message, author, recursive=True):
        if not has_permission("WRITE"):
            abort(403)
        if empty(message):
            message = "{} deleted.".format(self.pagename)
        files = []
        if self.exists:
            files.append(self.filename)
        if recursive:
            files.append(self.attachment_directoryname)
        if len(files) < 1:
            toast("Nothing to delete.")
            return redirect(url_for("view", path=self.pagepath))
        storage.delete(
            files,
            message=message,
            author=author,
        )
        toast("{} deleted.".format(self.pagename))
        return redirect(url_for("changelog"))

    def delete_form(self):
        if not has_permission("WRITE"):
            abort(403)
        # count attachments and subpages
        files, _ = storage.list(self.attachment_directoryname)
        if len(files) > 0:
            title = "Delete {} and the {} file(s) attached?".format(
                self.pagename, len(files)
            )
        else:
            title = "Delete {} ?".format(self.pagename)
        return render_template(
            "delete.html",
            title=title,
            pagepath=self.pagepath,
            pagename=self.pagename,
        )

    def _attachments(self, maximum=None):
        files, _ = storage.list(self.attachment_directoryname, depth=0)
        if maximum:
            files = files[:maximum]
        # currently only attached files are handled
        return [Attachment(self.pagepath, f) for f in files]

    def render_attachments(self):
        if not has_permission("READ"):
            abort(403)
        # handle case that the page doesn't exists
        self.exists_or_404()
        # get all attachments with metadata
        files = [f.data for f in self._attachments() if f.metadata is not None]
        return render_template(
            "attachments.html",
            title="{} - Attachments".format(self.pagename),
            pagepath=self.pagepath,
            pagename=self.pagename,
            files=files,
            breadcrumbs=self.breadcrumbs(),
        )

    def upload_attachments(
        self, files, message, filename, author, inline=False
    ):
        last_uploaded_filename = None
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
            last_uploaded_filename = fn
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
            if last_uploaded_filename is None:
                abort(500)
            return jsonify(filename=f"./{last_uploaded_filename}")
        return redirect(url_for("attachments", pagepath=self.pagepath))

    def get_attachment(self, filename, revision=None):
        return Attachment(self.pagepath, filename, revision).get()

    def get_attachment_thumbnail(self, filename, size=None, revision=None):
        try:
            size = int(
                size  # pyright: ignore -- the except takes care of None
            )
        except (TypeError, ValueError):
            size = 80
        return Attachment(self.pagepath, filename, revision).get_thumbnail(
            size=size
        )

    def edit_attachment(
        self, filename, author, new_filename=None, message=None, delete=None
    ):
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

    def load_draft(self, author):
        if current_user.is_anonymous:
            try:
                d = session["drafts"][self.pagepath]
                return namedtuple('SessionDraft', d.keys())(*d.values())
            except KeyError:
                return None
        else:
            draft = Drafts.query.filter_by(
                pagepath=self.pagepath, author_email=author[1]
            ).first()
            return draft

    def discard_draft(self, author):
        if current_user.is_anonymous:
            if "drafts" not in session:
                session["drafts"] = {}
            else:
                try:
                    # delete draft from session
                    del session["drafts"][self.pagepath]
                    session.modified = True
                except KeyError:
                    pass
        else:
            Drafts.query.filter_by(
                pagepath=self.pagepath, author_email=author[1]
            ).delete()
            db.session.commit()

    def save_draft(
        self, author, content, revision="", cursor_line=0, cursor_ch=0
    ):
        if not has_permission("WRITE"):
            abort(403)
        # Handle anonymous users, save draft in session
        if current_user.is_anonymous:
            if "drafts" not in session:
                session["drafts"] = {}
            # save draft in session
            d = {
                "content": content,
                "revision": revision,
                "cursor_line": cursor_line,
                "cursor_ch": cursor_ch,
                "datetime": datetime.now(UTC),
            }
            session["drafts"][self.pagepath] = d
            # flask.session: modifications on mutable structures are not picked up automatically
            session.modified = True
            return {
                "status": "draft saved in session",
            }

        # find existing Draft
        draft = Drafts.query.filter_by(
            pagepath=self.pagepath, author_email=author[1]
        ).first()
        if draft is None:
            draft = Drafts()
            draft.pagepath = self.pagepath
            draft.author_email = author[1]
        # update content, timestamp, revision, line
        draft.content = content
        draft.datetime = datetime.now(UTC)
        draft.revision = revision
        draft.cursor_line = cursor_line
        draft.cursor_ch = cursor_ch

        db.session.add(draft)
        db.session.commit()

        return {
            "status": "draft saved",
        }


class Attachment:
    def __init__(self, pagepath, filename, revision=None):
        self.pagepath = pagepath
        self.filename = filename
        self.revision = revision
        self.absdirectory = os.path.join(
            storage.path,
            get_attachment_directoryname(
                get_filename(pagepath),
            ),
        )
        self.fullpath = os.path.join(pagepath, filename)
        self.directory = get_attachment_directoryname(
            get_filename(pagepath),
        )
        self.filepath = os.path.join(self.directory, filename)
        self.abspath = os.path.join(storage.path, self.filepath)
        self.mimetype = guess_mimetype(self.filepath)
        try:
            self.metadata = storage.metadata(
                self.filepath, revision=self.revision
            )
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
            self.datetime = datetime.now(UTC)
            self._revision = None

    def exists(self):
        return os.path.exists(self.abspath)

    def get_thumbnail_url(self):
        if self.mimetype is not None and self.mimetype.startswith("image"):
            return (
                url_for(
                    "view",
                    path=self.fullpath,
                )
                + "?thumbnail"
            )
        return None

    def get_url(self):
        if self.revision is None:
            return url_for(
                "view",
                path=self.fullpath,
            )
        else:
            url_for(
                "get_attachment",
                pagepath=self.pagepath,
                filename=self.filename,
                revision=self.revision,
            )

    def get_thumbnail_icon(self):
        if self.mimetype is not None:
            if self.mimetype == "application/pdf":
                return (
                    '<i class="far fa-file-pdf" style="font-size:48px;"></i>'
                )
            if self.mimetype.startswith("text"):
                return (
                    '<i class="far fa-file-alt" style="font-size:48px;"></i>'
                )
        return '<i class="far fa-file" style="font-size:48px;"></i>'

    @property
    def data(self):
        return {
            "filename": self.filename,
            "filepath": self.filepath,
            "url": self.get_url(),
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
            storage.rename(
                self.filepath, new_filepath, message=message, author=author
            )
        except StorageError:
            toast("Renaming failed", "error")
            return redirect(url_for("attachments", pagepath=self.pagepath))
        toast(toast_message)
        return redirect(
            url_for(
                "edit_attachment",
                pagepath=self.pagepath,
                filename=new_filename,
            )
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
        if self.revision is None:
            if not storage.exists(self.filepath):
                return abort(404)
            # headers are already set correctly by send_file
            response = make_response(send_file(self.abspath))
        else:
            # revision is given
            try:
                content = storage.load(
                    self.filepath, revision=self.revision, mode="rb"
                )
                metadata = storage.metadata(
                    self.filepath, revision=self.revision
                )
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
            response.headers["Last-Modified"] = http_date(metadata['datetime'])
            response.headers["Cache-Control"] = "max-age=604800, immutable"
            response.headers["Date"] = http_date(self.datetime.utctimetuple())

        return response

    def get_thumbnail(self, size=80):
        if not has_permission("READ"):
            abort(403)
        if (
            not self.exists()
            or not self.mimetype
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
            "Thumbnail generation took {:.3f} seconds.".format(
                timer() - t_start
            )
        )
        # build response
        response = make_response(send_file(buffer, mimetype=self.mimetype))
        response.headers["Date"] = http_date(self.datetime.utctimetuple())
        response.headers["Expires"] = http_date(
            (self.datetime + timedelta(hours=1)).utctimetuple()
        )
        response.headers["Last-Modified"] = http_date(
            self.datetime.utctimetuple()
        )

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
            toast("Error in search term: {}".format(e), "error")
            return

    def search(self):
        if self.re is None:
            return {}
        # find all markdown files
        t_start = timer()
        files, _ = storage.list()
        md_files = [filename for filename in files if filename.endswith(".md")]
        app.logger.debug(
            f"Search storage.list() and filter took {timer() - t_start:.3f} seconds."
        )
        fn_result = {}

        t_start = timer()
        for fn in md_files:
            # check if pagename matches
            mi = self.rei.search(get_pagename(fn))
            if mi is not None:
                fn_result[fn] = [
                    True,
                    get_pagename(
                        fn,
                        full=True,
                    ),
                ]
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
        app.logger.debug(
            f"Search storage.load() and re.search('{self.needle}') took {timer() - t_start:.3f} seconds."
        )
        if self.in_history:
            # TODO
            # use git log -S
            # see https://git-scm.com/docs/git-log#Documentation/git-log.txt--Sltstringgt
            # search trough commits to find the one that added the string
            pass

        t_start = timer()
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
            key = [
                fnmatch,
                n,
                fn,
                get_pagename(fn, full=True),
                get_pagename(fn, full=True),
            ]
            summary = []
            if fnmatch == 1:
                summary = [matches.pop(0)]
                # overwrite key[4]
                key[4] = self.rei.sub(
                    r'<span class="page-match">\1</span>', key[4]
                )
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
                    summary[i] = None
                else:
                    summary[i] = self.re.sub(
                        r'<span class="text-match">\1</span>', l
                    )
            # store summary with key
            result[tuple(key)] = summary
        app.logger.debug(
            f"Search simplify result took {timer() - t_start:.3f} seconds."
        )

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
            title=(
                "Search '{}'".format(self.query)
                if not empty(self.query)
                else "Search"
            ),
            query=self.query,
            is_regexp=self.is_regexp,
            is_casesensitive=self.is_casesensitive,
            keys=keys,
            result=result,
        )


class AutoRoute:
    def __init__(self, path, values={}):
        self.path = path
        self.values = values
        # split path in path and filename
        *prefix, self.filename = split_path(self.path)
        if len(prefix):
            self.pagepath = join_path(prefix)
        else:
            self.pagepath = ""

        # glue together storage path
        if app.config["RETAIN_PAGE_NAME_CASE"]:
            self.storage_path = join_path([self.pagepath, self.filename])
        else:
            self.storage_path = join_path(
                [self.pagepath.lower(), self.filename]
            )

    def view(self):
        # check if the path leads to an attachment
        if (
            not empty(self.pagepath)
            and not self.filename.lower().endswith(".md")
            and not storage.isdir(
                self.path
                if app.config["RETAIN_PAGE_NAME_CASE"]
                else self.path.lower()
            )
            and storage.exists(self.storage_path)
        ):
            # create page
            p = Page(self.pagepath)
            # is this a thumbnail?
            if 'thumbnail' in self.values:
                # handle size parameter
                try:
                    size = int(self.values['thumbnail'])
                except:
                    size = None
                return p.get_attachment_thumbnail(
                    filename=self.filename, size=size, revision=None
                )
            # this is an attachment
            return p.get_attachment(self.filename)
        try:
            revision = self.values['revision']
        except KeyError:
            revision = None
        # create page object
        p = Page(self.path, revision=revision)
        # if page md doesn't exist, but the folder exists, show index
        if not storage.exists(p.filename) and storage.exists(
            p.attachment_directoryname
        ):
            pi = PageIndex(p.pagepath)
            return pi.render()
        # default to Page view
        return p.view()


