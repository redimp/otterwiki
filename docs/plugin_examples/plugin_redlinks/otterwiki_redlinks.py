#!/usr/bin/env python3

"""
This is an example plugin for An Otter Wiki that demonstrates the
renderer_process_wikilink hook.

The RedLinks plugin checks if a WikiLink points to an existing page and
marks non-existent pages with a red color, similar to MediaWiki's behavior.

This plugin uses the setup() hook to get access to the storage object,
and the renderer_process_wikilink() hook to modify WikiLink rendering.
"""

import urllib.parse
from otterwiki.plugins import hookimpl, plugin_manager


class RedLinks:
    @hookimpl
    def setup(self, app, db, storage) -> None:
        """Initialize the plugin with access to core objects."""
        self.app = app
        self.storage = storage

    @hookimpl
    def renderer_process_wikilink(
        self, wikilink_html, wikilink_url, wikilink_text, page=None
    ):
        """
        Process WikiLinks and mark non-existent pages with red color.

        Args:
            wikilink_html: The generated HTML for the wikilink
            wikilink_url: The URL the wikilink points to (e.g., "/Page%20Name")
            wikilink_text: The display text of the wikilink
            page: The current page object (optional)

        Returns:
            Modified HTML with red styling for non-existent pages
        """
        # Parse the URL to get the page path
        parsed_url = urllib.parse.urlparse(wikilink_url)
        page_path = urllib.parse.unquote(parsed_url.path)
        page_path = page_path.strip('/')
        if not page_path:
            return wikilink_html

        # Unless case is retained, convert to lowercase for storage check
        page_path = (
            page_path
            if self.app.config["RETAIN_PAGE_NAME_CASE"]
            else page_path.lower()
        )

        # Check both with and without .md extension for directories
        page_file = (
            page_path if page_path.endswith('.md') else f"{page_path}.md"
        )

        # Check if the page exists in storage (as .md file or as directory)
        page_exists = self.storage.exists(page_file) or self.storage.isdir(
            page_path
        )

        # If page doesn't exist, add red styling
        if not page_exists:
            # Add a class and inline style for red links
            wikilink_html = wikilink_html.replace(
                '<a href=',
                '<a class="redlink" style="color: #d33; text-decoration: none; border-bottom: 1px dotted #d33;" href=',
            )

        return wikilink_html


plugin_manager.register(RedLinks())
