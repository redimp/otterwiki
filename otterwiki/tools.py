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


def handle_housekeeping_brokenwikilinks(form):
    """Analyze pages for broken WikiLinks."""
    if not has_permission("WRITE"):
        abort(403)

    # WikiLink pattern: [[Page Name]] or [[Page Name|Display Text]]
    WIKI_LINK_PATTERN = re.compile(
        r"\[\[(([^|\]]+)(?:#[^\]]*)?(?:(\|)([^\]]+))?)\]\]"
    )
    WIKILINK_STYLE = app.config.get("WIKILINK_STYLE", "")

    t_start = timer()
    files, directories = storage.list()
    files_md = [f for f in files if f.endswith(".md")]

    pages_with_broken_links = {}
    broken_links_occurrences = {}

    for filename in files_md:
        content = storage.load(filename)
        current_pagename = get_pagename(filename, full=True)

        wikilinks = WIKI_LINK_PATTERN.findall(content)

        if not wikilinks:
            continue

        broken_links = []

        for match in wikilinks:
            # match[1] contains the first part (before | if present)
            # match[3] contains the second part (after | if present)
            left = match[1].strip()
            right = match[3].strip() if match[3] else left

            # default behavior: [[Title|Link]] or [[Title]]
            # LINK_TITLE or PAGE_NAME_TITLE: [[Link|Title]] or [[Link]]
            if WIKILINK_STYLE.upper().replace("_", "").strip() in [
                "LINKTITLE",
                "PAGENAMETITLE",
            ]:
                link_text = left
            else:
                link_text = right

            if link_text.startswith("#"):
                continue

            # remove fragment for display
            display_link = (
                link_text.split("#")[0] if "#" in link_text else link_text
            )

            # resolve relative paths
            page_path = (
                link_text.split("#")[0] if "#" in link_text else link_text
            )
            page_path = page_path.lstrip("/")

            if not page_path:
                continue

            if "../" in page_path:
                current_dir = os.path.dirname(
                    filename[:-3] if filename.endswith(".md") else filename
                )
                resolved_path = os.path.normpath(
                    os.path.join(current_dir, page_path)
                )
                page_path = resolved_path.replace(os.sep, "/").lstrip("./")

            page_file = get_filename(page_path)

            # check if page exists as file or directory
            page_exists = storage.exists(page_file) or storage.isdir(page_path)

            if not page_exists:
                broken_links.append(display_link)
                if display_link not in broken_links_occurrences:
                    broken_links_occurrences[display_link] = []
                broken_links_occurrences[display_link].append(current_pagename)

        if broken_links:
            seen = set()
            unique_broken_links = []
            for link in broken_links:
                if link not in seen:
                    seen.add(link)
                    unique_broken_links.append(link)
            pages_with_broken_links[current_pagename] = unique_broken_links

    pages_with_broken_links = dict(
        sorted(
            pages_with_broken_links.items(),
            key=lambda item: len(item[1]),
            reverse=True,
        )
    )

    most_wanted_pages = []
    for link_text, found_in_pages in broken_links_occurrences.items():
        unique_found_in = list(dict.fromkeys(found_in_pages))
        most_wanted_pages.append(
            {
                "page": link_text,
                "found_in": unique_found_in,
                "occurrences": len(unique_found_in),
            }
        )
    most_wanted_pages.sort(key=lambda x: x["occurrences"], reverse=True)

    duration = timer() - t_start
    app.logger.debug(
        f"housekeeping_brokenwikilinks scanning files took {duration:.3f} seconds."
    )

    stats = {
        "pages": len(files_md),
        "duration": f"{duration:.3f}s",
    }

    return render_template(
        "tools/housekeeping_brokenwikilinks.html",
        pages=pages_with_broken_links,
        most_wanted=most_wanted_pages,
        stats=stats,
    )


def handle_housekeeping(form):
    if form.get("task", None) == "drafts":
        return handle_housekeeping_drafts(form)
    if form.get("task", None) == "emptypages":
        return handle_housekeeping_emptypages(form)
    if form.get("task", None) == "brokenwikilinks":
        return handle_housekeeping_brokenwikilinks(form)
    # unkown task: display the form
    toast("Unkown task", "error")
    return redirect(url_for("housekeeping"))
