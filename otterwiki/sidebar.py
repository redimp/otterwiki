#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import re
import json
from collections import OrderedDict
from timeit import default_timer as timer
from flask import url_for
from otterwiki.plugins import call_hook
from otterwiki.server import storage, app
from otterwiki.util import (
    get_page_directoryname,
    split_path,
    join_path,
    empty,
)
from otterwiki.helper import (
    get_pagename,
    get_pagename_for_title,
)


class SidebarMenu:
    URI_SIMPLE = re.compile(r"^(((https?)\:\/\/)|(mailto:))\S+")

    def __init__(self):
        self.menu = []
        self.config = []
        if not app.config.get("SIDEBAR_CUSTOM_MENU", None):
            return
        try:
            raw_config = json.loads(
                app.config.get("SIDEBAR_CUSTOM_MENU", "[]")
            )
        except (ValueError, IndexError) as e:
            app.logger.error(
                f"Error decoding SIDEBAR_CUSTOM_MENU={app.config.get('SIDEBAR_CUSTOM_MENU','')}: {e}"
            )
            raw_config = []
        # generate both config and menu from raw_config
        for entry in raw_config:
            if (
                not entry.get("title", None)
                and not entry.get("link", None)
                and not entry.get("icon", None)
            ):
                continue
            link, title, icon = (
                entry.get("link", ""),
                entry.get("title", ""),
                entry.get("icon", ""),
            )
            self.config.append({"link": link, "title": title, "icon": icon})

            # handle separator
            if link == "---" and empty(title) and empty(icon):
                self.menu.append({"separator": True})
                continue

            if empty(link):
                if empty(title):
                    continue
                self.menu.append(
                    {
                        "link": url_for("view", path=title),
                        "title": title,
                        "icon": icon,
                    }
                )
            elif self.URI_SIMPLE.match(link):
                if empty(title):
                    title = link
                self.menu.append({"link": link, "title": title, "icon": icon})
            else:
                if empty(title):
                    title = link
                self.menu.append(
                    {
                        "link": url_for("view", path=link),
                        "title": title,
                        "icon": icon,
                    }
                )

    def query(self):
        return self.menu


class SidebarPageIndexEntry:
    def __init__(self, path: str, header: str):
        self.children: OrderedDict[str, SidebarPageIndexEntry] = OrderedDict()
        self.path: str = path
        self.header: str = header


class SidebarPageIndex:

    AXT_HEADING = re.compile(
        r' {0,3}(#{1,6})(?!#+)(?: *\n+|' r'\s+([^\n]*?)(?:\n+|\s+?#+\s*\n+))'
    )
    SETEX_HEADING = re.compile(r'([^\n]+)\n *(=|-){2,}[ \t]*\n+')

    def __init__(
        self,
        path: str | None = None,
        mode: str = "",
        filter_order: bool = True,
    ):
        """
        Initialize SidebarPageIndex

        Args:
            path: path to current file
            mode: filter/sort mode to use (constants from config)
            filter_order: if to use filters and sorting on page index
        """
        self.file_path = path
        self.path = get_page_directoryname(path or "/")
        if not app.config["RETAIN_PAGE_NAME_CASE"]:
            self.file_path = self.file_path.lower() if self.file_path else None
            self.path = self.path.lower()
        self.path_depth = len(split_path(self.path))
        try:
            self.max_depth = int(app.config["SIDEBAR_MENUTREE_MAXDEPTH"])
        except ValueError:
            self.max_depth = None
        self.mode = app.config["SIDEBAR_MENUTREE_MODE"]
        self.focus = app.config["SIDEBAR_MENUTREE_FOCUS"]
        # overwrite mode if argument is given
        if mode:
            self.mode = mode

        self.filenames_and_header = []

        # load pages
        self.tree: OrderedDict[str, SidebarPageIndexEntry] = OrderedDict()
        if self.mode != "":
            # check if focus has been disabled, via SIDEBAR_MENUTREE_FOCUS
            if self.focus == "OFF":
                # without focus load all pages
                self.load(path="")
            else:
                # load all siblings and parents of the current page
                self.load(self.path)

            if filter_order:
                self.tree = self.filter_order_tree(self.tree)

    def read_header(self, filename: str) -> str | None:
        """
        Read header of the file

        Args:
            filename: File from which to read header

        Returns:
            header string or none if not found
        """
        filehead = storage.load(filename, size=512)
        # find first markdown header in filehead
        header = [line for (_, line) in self.AXT_HEADING.findall(filehead)]
        if len(header):
            return header[0]

        header = [line for (line, _) in self.SETEX_HEADING.findall(filehead)]
        if len(header):
            return header[0]

        return None

    def filter_order_tree(
        self,
        tree: OrderedDict[str, SidebarPageIndexEntry],
    ) -> OrderedDict[str, SidebarPageIndexEntry]:
        """
        Filter and order passed tree

        Args:
            tree: Tree to filter and order

        Returns:
            new filtered and ordered tree
        """
        entries = list(tree.items())

        def sort_by_lower(
            key: tuple[str, SidebarPageIndexEntry],
        ) -> str:
            return str.lower(key[0])

        def sort_by_lower_directories(
            key: tuple[str, SidebarPageIndexEntry],
        ) -> tuple[bool, str]:
            return (len(key[1].children) == 0, str.lower(key[0]))

        def sort_by_ignore_case(
            key: tuple[str, SidebarPageIndexEntry],
        ) -> str:
            return key[0]

        def sort_by_ignore_case_directories(
            key: tuple[str, SidebarPageIndexEntry],
        ) -> tuple[bool, str]:
            return (len(key[1].children) == 0, key[0])

        # filter entries
        if self.mode in ["DIRECTORIES_ONLY"]:
            entries = [x for x in entries if len(x[1].children) > 0]

        call_hook(
            "sidebar_page_index_filter_entries",
            sidebarPageIndexEntries=entries,
            file_path=self.file_path,
            mode=self.mode,
        )

        # sort entries
        if app.config["SIDEBAR_MENUTREE_IGNORE_CASE"]:
            sort_key = sort_by_lower
        else:
            sort_key = sort_by_ignore_case
        if self.mode in ["DIRECTORIES_GROUPED"]:
            if app.config["SIDEBAR_MENUTREE_IGNORE_CASE"]:
                sort_key = sort_by_lower_directories
            else:
                sort_key = sort_by_ignore_case_directories

        entries.sort(key=sort_key)

        call_hook(
            "sidebar_page_index_sort_entries",
            sidebarPageIndexEntries=entries,
            file_path=self.file_path,
            mode=self.mode,
        )

        # after filtering and ordering: back to OrderedDict
        sorted_tree = OrderedDict(entries)

        # recursively take care of the child nodes
        for key, values in sorted_tree.items():
            if values.children:
                sorted_tree[key].children = self.filter_order_tree(
                    values.children,
                )
        return sorted_tree

    def add_node(
        self,
        tree: OrderedDict[str, SidebarPageIndexEntry],
        prefix: list[str],
        parts: list[str],
        header: str | None = None,
    ):
        """
        Add new nodes based of 'prefix' and 'parts' into the given position in the 'tree'

        Args:
            tree: Tree where to insert new node
        """
        # handle max_depth
        if (
            self.max_depth
            and len(prefix) + len(parts) > self.path_depth + self.max_depth
        ):
            return
        if parts[0] not in tree:
            new_entry = SidebarPageIndexEntry(
                path=get_pagename(
                    join_path(prefix + parts),
                    full=True,
                    header=header if len(parts) == 1 else None,
                ),
                header=get_pagename_for_title(
                    join_path(prefix + parts),
                    full=False,
                    header=header if len(parts) == 1 else None,
                ),
            )
            tree[parts[0]] = new_entry
        if len(parts) > 1:
            self.add_node(
                tree[parts[0]].children,
                prefix + [parts[0]],
                parts[1:],
                header,
            )

    def load(self, path: str):
        """
        Add sidebar page index entries into self.tree

        Args:
            path: Path within storage from which to get entries
        """
        t_start = timer()
        files, _ = storage.list(p=path)
        app.logger.debug(
            f"SidebarPageIndex.load({path}) storage.list() files took {timer() - t_start:.3f} seconds."
        )

        t_start = timer()
        entries: list[str] = []
        for filename in [
            f for f in files if f.endswith(".md")
        ]:  # filter .md files
            filename = os.path.join(path, filename)
            parents = split_path(filename)[:-1]
            # ensure all parents are in the entries
            for i in range(len(parents)):
                pp = join_path(parents[0 : i + 1])
                entries.append(pp)
            entries.append(filename)
        entries = list(set(entries))
        entries.sort()

        for entry in entries:
            header = None
            if entry.endswith(".md"):
                header = self.read_header(entry)
                entry = entry[:-3]
            self.filenames_and_header.append((entry, header))
            parts = split_path(entry)
            self.add_node(self.tree, [], parts, header)
        app.logger.debug(
            f"SidebarPageIndex.load({path}) reading entries, adding nodes took {timer() - t_start:.3f} seconds."
        )

    def query(self) -> OrderedDict[str, SidebarPageIndexEntry]:
        return self.tree
