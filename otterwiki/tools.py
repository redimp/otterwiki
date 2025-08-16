#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import re
import os.path

from flask import (
    redirect,
    url_for,
    render_template,
    abort,
)

from timeit import default_timer as timer

from otterwiki.gitstorage import StorageNotFound
from otterwiki.server import app, db, storage
from otterwiki.models import Drafts
from otterwiki.auth import has_permission, get_author

from otterwiki.helper import (
    toast,
    get_filename,
    get_pagename,
)

from otterwiki.util import (
    empty,
)


def housekeeping_form():
    author_email = get_author()[1]
    drafts = []
    if not empty(author_email):
        db_drafts = (
            Drafts.query.filter_by(author_email=author_email)
            .order_by(Drafts.pagepath)
            .all()
        )
        for draft in db_drafts:
            try:
                entries = storage.log(get_filename(draft.pagepath))
                entry = entries[0]
            except StorageNotFound:
                entries = []
                entry = {}
            d = {
                "id": draft.id,
                "pagepath": draft.pagepath,
                "revision": draft.revision,
                "revision_text": (
                    "Latest"
                    if draft.revision == entry.get("revision", None)
                    else draft.revision
                ),
                "datetime": draft.datetime,
                "page_datetime": entry.get("datetime", None),
            }
            drafts.append(d)
    return render_template(
        "tools/housekeeping.html",
        title="Housekeeping",
        drafts=drafts,
    )


def handle_housekeeping_drafts(form):
    # fetch list of ids with drafts to delete
    drafts_to_delete = form.getlist("delete_draft")
    if drafts_to_delete:
        deleted = 0
        author_email = get_author()[1]
        for id in drafts_to_delete:
            draft = Drafts.query.filter_by(
                id=id, author_email=author_email
            ).first()
            if draft:
                db.session.delete(draft)
                deleted += 1
        if deleted > 0:
            toast(f"Deleted {deleted} draft(s).")
            db.session.commit()
    return redirect(url_for("housekeeping"))


def handle_housekeeping_emptypages(form):
    if not has_permission("WRITE"):
        abort(403)

    if form.get("clean", None):
        t_start = timer()
        pages_to_delete = form.getlist("delete_empty_page")
        files_to_delete = [get_filename(p) for p in pages_to_delete]
        if len(files_to_delete):
            storage.delete(
                files_to_delete,
                message=f"Housekeeping: Removed empty page{'s'[:len(files_to_delete)^1]}",
                author=get_author(),
            )
            app.logger.debug(
                f"housekeeping_emptypages cleaning {len(files_to_delete)} files took {timer() - t_start:.3f} seconds."
            )
    t_start = timer()
    files, directories = storage.list()
    app.logger.debug(
        f"housekeeping_emptypages storage.list() files took {timer() - t_start:.3f} seconds."
    )
    # attachments_counts:
    attachments_counts = {d: 0 for d in directories}
    # files:
    for filename in files:
        d = os.path.dirname(filename)
        try:
            attachments_counts[d] += 1
        except KeyError:
            attachments_counts[d] = 1
    t_start = timer()
    files_md = [f for f in files if f.endswith(".md")]  # filter .md files
    pages: dict[str, str] = {}
    for filename in files_md:
        if storage.size(filename) > 512:
            # file is at least 512 bytes, so probably not "empty"
            continue
        if attachments_counts.get(filename[:-3], 0) > 0:
            # file has attachments
            pass  # continue
        # read file
        pagename = get_pagename(filename, full=True)
        content = storage.load(filename, size=512).strip()
        if len(content) < 1:
            pages[pagename] = "Page is empty"
            continue
        # check for header only
        if re.match(r"^# ([^ \r\n]+)$", content):
            if pagename == "Imageresize":
                print(f"{content=}")
            pages[pagename] = "Header only"
            continue
        lines = content.count("\n") + 1
        if lines < 3:
            pages[pagename] = "Less than three lines"
            continue
    duration = timer() - t_start
    app.logger.debug(
        f"housekeeping_emptypages scanning files took {duration:.3f} seconds."
    )
    stats = {
        "pages": len(files_md),
        "duration": f"{duration:.3f}s",
    }
    return render_template(
        "tools/housekeeping_emptypages.html",
        pages=pages,
        stats=stats,
    )


def handle_housekeeping(form):
    if form.get("task", None) == "drafts":
        return handle_housekeeping_drafts(form)
    if form.get("task", None) == "emptypages":
        return handle_housekeeping_emptypages(form)
    # unkown task: display the form
    toast("Unkown task", "error")
    return redirect(url_for("housekeeping"))
