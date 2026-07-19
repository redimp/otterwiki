#!/usr/bin/env python3

"""
When a page is renamed this module rewrites all links
in the wiki that point to the old page so that they point
to the new page name instead.
"""

import re

from otterwiki.server import app, storage
from urllib.parse import quote, unquote

"""Rewrite WikiLinks and images pointing to a renamed page."""

# Matches a single WikiLink and captures its inner content.
# WikiLink inner content never contains a closing bracket.
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

# Matches nested images inside links
IMAGE_LINK_WRAPPER_RE = re.compile(r"\[(!\[[^\]]*\]\([^)]+\))\]\((/[^)]+)\)")

# Matches a Markdown image link
IMAGE_LINK_RE = re.compile(r"!\[([^\]]*)\]\((/[^)]+)\)")

# Matches Markdown links
# Example: [text](/Parent/ChildPage)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((/[^)]+)\)")


def _is_linktitle_style():
    """True if the link is the *left* side of ``[[left|right]]``."""
    style = (
        app.config.get("WIKILINK_STYLE", "").upper().replace("_", "").strip()
    )
    return style in ("LINKTITLE", "PAGENAMETITLE")


def _split_link_title(inner, linktitle_style):
    """Split a WikiLink's inner content into (link_part, title_part).

    ``title_part`` is None when the link carries no explicit title, in
    which case the link doubles as the displayed text.
    """
    if "|" in inner:
        left, right = inner.split("|", 1)
        if linktitle_style:
            return left, right
        return right, left
    # no pipe: the whole content is both link and displayed text
    return inner, None


def _rewrite_inner(inner, old_key, new_pagepath, linktitle_style):
    """Return the rewritten inner content, or None if it doesn't match."""
    from otterwiki.helper import get_filename

    link_part, title_part = _split_link_title(inner, linktitle_style)

    # preserve a leading slash (absolute links) and any #anchor
    leading_slash = link_part.startswith("/")
    page, hsep, anchor = link_part.strip().lstrip("/").partition("#")
    page = unquote(page.strip())
    if not page:
        # pure anchor link like [[#section]] - nothing to do
        return None

    # resolve the link target to its on-disk filename and compare.
    if get_filename(page) != old_key:
        return None

    new_link = ("/" if leading_slash else "") + new_pagepath
    if hsep:
        new_link += "#" + anchor

    if title_part is None:
        return new_link
    if linktitle_style:
        return new_link + "|" + title_part
    return title_part + "|" + new_link


def _rewrite_attachment(match, old_pagepath, new_pagepath):
    """Rewrite Markdown image links pointing to attachments on a renamed page."""

    alt = match.group(1)
    url = match.group(2)

    new_url = _rewrite_url(
        url,
        old_pagepath,
        new_pagepath,
    )

    return f"![{alt}]({new_url})"


def _rewrite_markdown_link(match, new_pagepath, old_pagepath):
    """Rewrite Markdown links pointing to a renamed page."""

    text = match.group(1)
    url = match.group(2)

    new_url = _rewrite_url(
        url,
        old_pagepath,
        new_pagepath,
    )

    return f"[{text}]({new_url})"


def _rewrite_url(url, old_pagepath, new_pagepath):
    """Rewrite a Markdown URL pointing to a renamed page or one of its
    attachments.

    Returns the rewritten URL, or the original URL if no rewrite is needed.
    """

    from otterwiki.helper import get_filename

    retain_case = app.config.get("RETAIN_PAGE_NAME_CASE", False)

    # Split query string.
    path, qsep, query = url.partition("?")

    # Split anchor.
    path, hsep, anchor = path.partition("#")

    #
    # First: attachment URLs
    #
    old_page_dir = quote(old_pagepath.rsplit(".", 1)[0].strip("/"), safe="/")
    new_page_dir = quote(new_pagepath.rsplit(".", 1)[0].strip("/"), safe="/")

    old_prefix = "/" + old_page_dir + "/"

    if retain_case:
        matches = path.startswith(old_prefix)
    else:
        matches = path.lower().startswith(old_prefix.lower())

    if matches:
        relative = path[len(old_prefix) - 1 :]
        new_path = "/" + new_page_dir + relative

    else:
        #
        # Page URL
        #
        leading_slash = path.startswith("/")

        page = unquote(path.lstrip("/"))

        if not page:
            return url

        old_key = get_filename(old_pagepath)
        if get_filename(page) != old_key:
            return url

        encoded = quote(new_pagepath, safe="/")
        new_path = ("/" if leading_slash else "") + encoded

    # Restore anchor.
    if hsep:
        new_path += "#" + anchor

    # Restore query string.
    if qsep:
        new_path += "?" + query

    return new_path


def _rewrite_content(
    content, old_key, new_pagepath, linktitle_style, old_pagepath
):
    def repl(match):
        new_inner = _rewrite_inner(
            match.group(1), old_key, new_pagepath, linktitle_style
        )
        if new_inner is None:
            return match.group(0)
        return "[[" + new_inner + "]]"

    def wrapper_repl(match):
        image = match.group(1)
        url = _rewrite_url(match.group(2), old_pagepath, new_pagepath)
        return f"[{image}]({url})"

    def attachment_repl(match):
        return _rewrite_attachment(match, old_pagepath, new_pagepath)

    def markdown_link_repl(match):
        return _rewrite_markdown_link(
            match,
            new_pagepath,
            old_pagepath,
        )

    # Rewrite WikiLinks
    content = WIKILINK_RE.sub(repl, content)

    # Rewrite nested images inside links
    content = IMAGE_LINK_WRAPPER_RE.sub(wrapper_repl, content)

    # Rewrite image links
    content = IMAGE_LINK_RE.sub(attachment_repl, content)

    # Rewrite Markdown links
    content = MARKDOWN_LINK_RE.sub(markdown_link_repl, content)

    return content


def rename_backlinks(old_pagepath, new_pagepath):
    if not app.config.get("UPDATE_LINKS_ON_RENAME", True):
        return {}

    from otterwiki.helper import get_filename

    try:
        old_key = get_filename(old_pagepath)
        linktitle_style = _is_linktitle_style()

        all_files, _ = storage.list()
        md_files = [f for f in all_files if f.endswith(".md")]

        updated = {}
        for md_file in md_files:
            content = storage.load(md_file, mode="r")
            new_content = _rewrite_content(
                content, old_key, new_pagepath, linktitle_style, old_pagepath
            )
            if new_content == content:
                continue
            # storage.update() writes the updated content to file.
            storage.update(
                filename=md_file,
                content=new_content,
            )
            updated[md_file] = new_content

        if updated:
            app.logger.info(
                "rename_backlinks: rewrote backlinks in %d page(s) "
                "after renaming '%s' to '%s'",
                len(updated),
                old_pagepath,
                new_pagepath,
            )

        return updated

    except Exception as e:
        app.logger.error(
            "rename_backlinks: failed to update links after renaming "
            "'%s' to '%s': %s",
            old_pagepath,
            new_pagepath,
            e,
        )

        return {}
