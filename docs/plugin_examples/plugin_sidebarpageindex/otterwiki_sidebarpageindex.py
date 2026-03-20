#!/usr/bin/env python3

"""
Sidebar Page Index Filter and Sort Example Plugin for An Otter Wiki

This is an example plugin that demonstrates the new sidebar page index filter and sort processing hooks.
The plugin might not work as expected based on the wiki settings of Page Index. Recommended are settings
"Page Index Mode" to "Directories and pages, sorter" and "Page Index Focus" to "Always display all pages".

Features:
- Removes pages with "_hidden" suffix from Page Index
- Reverse sort pages by their name
"""

from collections import OrderedDict
from otterwiki.plugins import hookimpl, plugin_manager
from otterwiki.util import (
    split_path,
)


class SidebarPageIndexExample:
    """
    Example plugin demonstrating Sidebar Page Index filter and sort processing hooks.
    """

    @hookimpl
    def setup(self, app, db, storage):
        """Initialize the plugin with the core objects."""
        self.app = app
        self.db = db
        self.storage = storage

    @hookimpl
    def sidebar_page_index_filter_entries(
        self,
        sidebarPageIndexEntries: list[tuple],
        file_path: str | None,
        mode: str,
    ) -> None:
        """
        This hook allows plugins to filter sidebar page index entries.
        Only root entries needs to be filtered as the hook is called for list
        of children of every entry.

        Args:
            sidebarPageIndexEntries: Tree roots of entries that will be shown
            file_path: Path to current open viewed
            mode: filter/sort mode to use (constants from config)
        """

        def should_show(
            entry: tuple,
        ) -> bool:
            if file_path:
                paths = split_path(file_path)
                for path in paths:
                    if path == entry[1].header:
                        return True
            return not entry[0].endswith("_hidden")

        sidebarPageIndexEntries[:] = [
            e for e in sidebarPageIndexEntries if should_show(e)
        ]

    @hookimpl
    def sidebar_page_index_sort_entries(
        self,
        sidebarPageIndexEntries: list[tuple],
        file_path: str | None,
        mode: str,
    ) -> None:
        """
        This hook allows plugins to order sidebar page index entries.
        Only root entries needs to be sorted as the hook is called for list
        of children of every entry.

        Args:
            sidebarPageIndexEntries: Tree roots of entries that will be shown
            file_path: Path to current open viewed
            mode: filter/sort mode to use (constants from config)
        """

        def sort_by_lower_reverse(
            key: tuple,
        ) -> str:
            return str.lower(key[0])

        sidebarPageIndexEntries.sort(key=sort_by_lower_reverse, reverse=True)


plugin_manager.register(SidebarPageIndexExample())
