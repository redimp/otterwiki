#!/usr/bin/env python3

"""
Update Links on Rename Plugin for An Otter Wiki

When a page is renamed this plugin rewrites all WikiLinks (``[[...]]``)
in the wiki that point to the old page so that they point to the new
page name instead. This implements the request from
https://github.com/redimp/otterwiki/discussions/210 (issue #228).

It demonstrates the ``page_renamed`` hook and shows how a plugin can
read, modify and commit page content through the storage API.

Scope / limitations:
- Only WikiLinks (``[[Page]]``, ``[[Title|Page]]``) are updated, matching
  what the bundled "referencingpages" example can already discover. Plain
  Markdown links (``[text](/Page)``) are intentionally left untouched.
- Matching is exact for the renamed page. Child pages and attachment links
  are not rewritten (see issue #65 for attachments).
- Renaming pages is not the only way to opt out: set
  ``UPDATE_LINKS_ON_RENAME = False`` in your settings.cfg to keep the plugin
  installed but disabled (a per-rename checkbox is not currently exposable
  via the plugin API).
"""

import os
import re

from otterwiki.plugins import hookimpl, plugin_manager


class UpdateLinksOnRename:
    """Rewrite WikiLinks pointing to a renamed page."""

    # Matches a single WikiLink and captures its inner content.
    # WikiLink inner content never contains a closing bracket.
    WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

    @hookimpl
    def setup(self, app, db, storage):
        self.app = app
        self.storage = storage

    def _is_linktitle_style(self):
        """True if the link is the *left* side of ``[[left|right]]``."""
        style = (
            self.app.config.get("WIKILINK_STYLE", "")
            .upper()
            .replace("_", "")
            .strip()
        )
        return style in ("LINKTITLE", "PAGENAMETITLE")

    def _split_link_title(self, inner, linktitle_style):
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

    def _rewrite_inner(self, inner, old_key, new_pagepath, linktitle_style):
        """Return the rewritten inner content, or None if it doesn't match."""
        from otterwiki.helper import get_filename

        link_part, title_part = self._split_link_title(inner, linktitle_style)

        # preserve a leading slash (absolute links) and any #anchor
        leading_slash = link_part.startswith("/")
        page, hsep, anchor = link_part.strip().lstrip("/").partition("#")
        page = page.strip()
        if not page:
            # pure anchor link like [[#section]] - nothing to do
            return None

        # resolve the link target to its on-disk filename and compare. This
        # makes the match case-/slash-/".md"-insensitive, exactly how Otter
        # Wiki itself resolves a page path.
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

    def _rewrite_content(
        self, content, old_key, new_pagepath, linktitle_style
    ):
        def repl(match):
            new_inner = self._rewrite_inner(
                match.group(1), old_key, new_pagepath, linktitle_style
            )
            if new_inner is None:
                return match.group(0)
            return "[[" + new_inner + "]]"

        return self.WIKILINK_RE.sub(repl, content)

    @hookimpl
    def page_renamed(self, old_pagepath, new_pagepath, author, message):
        if not self.app.config.get("UPDATE_LINKS_ON_RENAME", True):
            return

        from otterwiki.helper import get_filename

        try:
            old_key = get_filename(old_pagepath)
            linktitle_style = self._is_linktitle_style()

            all_files, _ = self.storage.list()
            md_files = [f for f in all_files if f.endswith(".md")]

            updated = []
            for md_file in md_files:
                content = self.storage.load(md_file, mode="r")
                new_content = self._rewrite_content(
                    content, old_key, new_pagepath, linktitle_style
                )
                if new_content == content:
                    continue
                # storage.store() writes, commits, fires repository_changed
                # and auto-pushes - the same path a normal page edit takes.
                self.storage.store(
                    filename=md_file,
                    content=new_content,
                    author=author,
                    message="Updated link: renamed '{}' to '{}'".format(
                        old_pagepath, new_pagepath
                    ),
                )
                updated.append(md_file)

            if updated:
                self.app.logger.info(
                    "UpdateLinksOnRename: rewrote WikiLinks in %d page(s) "
                    "after renaming '%s' to '%s'",
                    len(updated),
                    old_pagepath,
                    new_pagepath,
                )
        except Exception as e:
            self.app.logger.error(
                "UpdateLinksOnRename: failed to update links after renaming "
                "'%s' to '%s': %s",
                old_pagepath,
                new_pagepath,
                e,
            )


plugin_manager.register(UpdateLinksOnRename())
