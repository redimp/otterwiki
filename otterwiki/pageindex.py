#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
from timeit import default_timer as timer
from urllib.parse import unquote

from flask import (
    abort,
    redirect,
    render_template,
    url_for,
)

import textwrap
from typing import List, Tuple, Iterable

from otterwiki.auth import has_permission, current_user

from otterwiki.helper import (
    get_breadcrumbs,
    get_filename,
    get_ftoc,
    get_pagename,
    get_pagename_for_title,
    upsert_pagecrumbs,
)
from otterwiki.server import app, storage
from otterwiki.sidebar import SidebarMenu, SidebarPageIndex
from otterwiki.util import (
    get_page_directoryname,
    join_path,
    split_path,
)


from dataclasses import dataclass


@dataclass
class PageIndexEntry:
    depth: int
    title: str
    url: str
    toc: List[Tuple[int, str, str]] | None = None
    has_children: bool = False


class PageIndex:
    toc: dict[str, List[PageIndexEntry]] = {}

    def __init__(self, path: str | None = None):
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
            firstletter = get_pagename_for_title(fn, full=True)[0].upper()
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
                        PageIndexEntry(
                            depth=subdir_depth,
                            title=get_pagename_for_title(
                                subdir_path, full=False
                            )
                            + "/",
                            url=url_for(
                                "view",
                                path=get_pagename(subdir_path_full, full=True),
                            ),
                            toc=[],
                            has_children=True,
                        )
                    )
                    page_indices.append(subdir_path)
            pagetoc = []
            # default pagename is the pagename derived from the filename
            pagename = get_pagename(
                f,
                full=False,
            )
            ftoc = get_ftoc(f)

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
            # strip self.path from displayname and apply title formatting
            displayname = get_pagename_for_title(
                f,
                full=False,
                header=pagename,
            )
            if self.path is not None:
                # for nested pages, we need to strip the path prefix from the display name
                full_display_name = get_pagename_for_title(
                    f,
                    full=True,
                    header=pagename,
                )
                if full_display_name.lower().startswith(self.path.lower()):
                    displayname = full_display_name[len(self.path) + 1 :]
            has_children = False
            for other in md_files:
                if other.startswith(f[:-3] + "/"):
                    has_children = True
                    break
            self.toc[firstletter].append(
                PageIndexEntry(
                    depth=page_depth - self.index_depth,
                    title=displayname,
                    url=url_for(
                        "view",
                        path=get_pagename(f, full=True, header=pagename),
                    ),
                    toc=pagetoc,
                    has_children=has_children,
                )
            )

        app.logger.debug(
            f"PageIndex({self.path}) parsing files took {timer() - t_start:.3f} seconds."
        )

    def meta_description(self) -> str:
        """
        Generate a description used as <meta og:description> containing the Pages
        listed in the index.
        """
        pages = [p[0] for p in self.pages()]

        if len(self.toc) == 1:
            description = f"{len(pages)} entry: "
        else:
            description = f"{len(pages)} entries: "

        description += ", ".join([x.strip("/") for x in pages])

        description = textwrap.shorten(
            description,
            width=254,
            placeholder="…",
        )

        return description

    def render(self):
        if not has_permission("READ"):
            if not current_user.is_authenticated:
                return redirect(url_for("login"))
            abort(403)
        menutree = SidebarPageIndex(get_page_directoryname(self.path or "/"))

        # build the title and description used in the meta og tags ...
        if self.path is None or self.path.rstrip("/") == "":
            title = "Page Index"
        else:
            title = f"Page Index: /{self.path}"

        upsert_pagecrumbs(get_pagename(self.path or "/", full=True))
        return render_template(
            "pageindex.html",
            title=title,
            pages=self.toc,
            pagepath=self.path or "/",
            menutree=menutree.query(),
            custom_menu=SidebarMenu().query(),
            breadcrumbs=self.breadcrumbs,
            description=self.meta_description(),
        )

    def pages(self) -> Iterable[Tuple[str, str, str]]:
        for letter in self.toc:
            for entry in self.toc[letter]:
                yield entry.title, unquote(entry.url)[1:], entry.url
