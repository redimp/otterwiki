#!/usr/bin/env python

import os
import re
from pprint import pprint

from otterwiki.server import storage, app
from otterwiki.util import (
    split_path,
    join_path,
    get_pagename,
)


class SidebarNavigation:
    AXT_HEADING = re.compile(
        r' {0,3}(#{1,6})(?!#+)(?: *\n+|' r'\s+([^\n]*?)(?:\n+|\s+?#+\s*\n+))'
    )
    SETEX_HEADING = re.compile(r'([^\n]+)\n *(=|-){2,}[ \t]*\n+')

    def __init__(self, path: str = "/"):
        self.path = path.lower()
        self.path_depth = len(split_path(self.path))
        try:
            self.max_depth = int(app.config["SIDEBAR_MENUTREE_MAXDEPTH"])
        except ValueError:
            self.max_depth = None
        self.mode = app.config["SIDEBAR_MENUTREE_MODE"]
        # TODO load existing config file
        # TODO check for cached pages
        # load pages
        self.tree = {}
        self.load()
        # TODO apply config file to pages
        pass

    def read_header(self, filename):
        filehead = storage.load(filename, size=512)
        # find first markdown header in filehead
        header = [line for (_, line) in self.AXT_HEADING.findall(filehead)]
        header += [line for (line, _) in self.SETEX_HEADING.findall(filehead)]
        if len(header):
            return header[0]
        return None

    def add_node(self, tree, prefix, parts, header=None):
        if parts[0] not in tree:
            tree[parts[0]] = {
                "children": {},
                "path": get_pagename(
                    join_path(prefix + parts),
                    full=True,
                    header=header if len(parts) == 1 else None,
                ),
                "header": get_pagename(
                    join_path(prefix + parts),
                    full=False,
                    header=header if len(parts) == 1 else None,
                ),
            }
        if len(parts) > 1:
            self.add_node(
                tree[parts[0]]["children"], prefix + [parts[0]], parts[1:]
            )

    def load(self):
        files, _ = storage.list(p=self.path)

        entries = []
        for filename in [
            f for f in files if f.endswith(".md")
        ]:  # filter .md files
            if self.path is not None:
                filename = os.path.join(self.path, filename)
            parents = split_path(filename)[:-1]
            # ensure all parents are in the entries
            for i in range(len(parents)):
                pp = join_path(parents[0 : i + 1])
                entries.append(pp)
            entries.append(filename)
        entries = sorted(list(set(entries)))

        for entry in entries:
            header = None
            if entry.endswith(".md"):
                header = self.read_header(entry)
                entry = entry[:-3]
            parts = split_path(entry)
            self.add_node(self.tree, [], parts, header)

    def query(self):
        return self.tree


# vim: set et ts=8 sts=4 sw=4 ai:
