#!/usr/bin/env python3

"""
Referencing Pages Plugin for An Otter Wiki

This plugin demonstrates the template_html_sidebar_right_inject and repository_changed hooks.

Features:
- Builds an in-memory index of page references (which pages link to which)
- Updates the index when repository changes are detected
- Displays a "This page is referenced by" block in the right sidebar
  showing pages that have WikiLinks pointing to the current page

This plugin demonstrates:
1. setup() - Initialize the plugin and build the initial reference index
2. repository_changed() - Update the index when files change
3. template_html_sidebar_right_inject() - Add content to the right sidebar
"""

import os
import re
import urllib.parse
from otterwiki.plugins import hookimpl, plugin_manager


class ReferencingPages:
    """
    Plugin that tracks and displays which pages reference the current page.
    """

    def __init__(self):
        # Dictionary mapping page paths to lists of pages that reference them
        # Format: {referenced_page: [referencing_page1, referencing_page2, ...]}
        self.references = {}

    @hookimpl
    def setup(self, app, db, storage):
        """Initialize the plugin with access to core objects and build initial index."""
        self.app = app
        self.storage = storage

        self._build_reference_index()

    def _build_reference_index(self):
        """
        Scan all markdown files in the repository and build the reference index.
        """
        self.references = {}

        try:
            all_files, _ = self.storage.list()
            md_files = [f for f in all_files if f.endswith('.md')]

            for md_file in md_files:
                self._update_references_for_file(md_file)

            # Count total reference entries
            total_entries = sum(len(refs) for refs in self.references.values())
            self.app.logger.info(
                f"ReferencingPages: Built reference index with {total_entries} entries "
                f"across {len(self.references)} referenced pages from {len(md_files)} files"
            )

        except Exception as e:
            try:
                self.app.logger.error(
                    f"ReferencingPages: Failed to build index: {e}"
                )
            except:
                pass

    def _update_references_for_file(self, filepath):
        """
        Parse a markdown file and update the reference index with its WikiLinks.
        """
        try:
            # Read the file content
            content = self.storage.load(filepath, mode='r')

            # Remove this file's old references from the index
            self._remove_file_from_index(filepath)

            # Find all WikiLinks in the content
            # WikiLink patterns: [[Page Name]] or [[Page Name|Display Text]]
            wikilink_pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
            matches = re.findall(wikilink_pattern, content)

            # Get the source page path (remove .md extension)
            source_page = (
                filepath[:-3] if filepath.endswith('.md') else filepath
            )

            # Process each WikiLink
            for match in matches:
                # Clean up the page name
                target_page = match.strip()

                # Normalize the page path (handle case sensitivity)
                if not self.app.config.get("RETAIN_PAGE_NAME_CASE", False):
                    target_page = target_page.lower()

                # Skip self-references (a page cannot reference itself)
                if target_page == source_page:
                    continue

                # Add to references index
                if target_page not in self.references:
                    self.references[target_page] = []

                if source_page not in self.references[target_page]:
                    self.references[target_page].append(source_page)

        except Exception as e:
            # Log error but don't fail
            try:
                self.app.logger.error(
                    f"ReferencingPages: Failed to update references for {filepath}: {e}"
                )
            except:
                pass

    def _remove_file_from_index(self, filepath):
        """
        Remove all references from a file from the index.
        """
        source_page = filepath[:-3] if filepath.endswith('.md') else filepath

        # Remove this page from all reference lists
        for target_page in list(self.references.keys()):
            if source_page in self.references[target_page]:
                self.references[target_page].remove(source_page)
            # Clean up empty lists
            if not self.references[target_page]:
                del self.references[target_page]

    @hookimpl
    def repository_changed(self, changed_files):
        """
        Update the reference index when repository changes are detected.
        """
        try:
            # Track changes for logging
            md_files_changed = []

            for filepath in changed_files:
                # Only process markdown files
                if filepath.endswith('.md'):
                    md_files_changed.append(filepath)
                    # Check if file still exists (not deleted)
                    if self.storage.exists(filepath):
                        self._update_references_for_file(filepath)
                    else:
                        # File was deleted, remove it from index
                        self._remove_file_from_index(filepath)

            # Log the update if any markdown files were changed
            if md_files_changed:
                total_entries = sum(
                    len(refs) for refs in self.references.values()
                )
                self.app.logger.info(
                    f"ReferencingPages: Updated index for {len(md_files_changed)} file(s). "
                    f"Index now has {total_entries} entries across {len(self.references)} referenced pages"
                )
        except Exception as e:
            # Log error but don't fail
            try:
                self.app.logger.error(
                    f"ReferencingPages: Failed to handle repository change: {e}"
                )
            except:
                pass

    @hookimpl
    def template_html_sidebar_right_inject(self, page):
        """
        Inject the "Referencing pages" block into the right sidebar.
        """
        from otterwiki.helper import get_pagename

        try:

            # Only show on page views where we have a page path
            if not page:
                return None

            # page is the pagepath string
            page_path = page

            # Normalize the page path
            if not self.app.config.get("RETAIN_PAGE_NAME_CASE", False):
                page_path = page_path.lower()

            # Get the list of pages that reference this page
            referencing_pages = self.references.get(page_path, [])

            if not referencing_pages:
                return None

            # Puzzle into a dictionary, makes the references uniq and better printable.
            referencing_pages = dict(
                (k, [get_pagename(k), get_pagename(k, full=True)])
                for k in referencing_pages
            )
            # Build the HTML for the sidebar block
            # Using the same structure as the "On this page" block
            html = '''
    <details class="collapse-panel" open>
        <summary class="collapse-header">Referencing pages</summary>

        <div class="collapse-content">
'''

            # Add links to each referencing page, sorted by the displayed pagename
            for pagepath in sorted(
                referencing_pages, key=lambda x: referencing_pages[x][0]
            ):
                # Create a display name (use the last part of the path)
                pagename = referencing_pages[pagepath][0]
                pagename_full = referencing_pages[pagepath][1]
                # URL encode the page path
                url_path = urllib.parse.quote(pagename_full)

                html += f'            <a href="/{url_path}" class="sidebar-link" title="{pagename_full}">{pagename}</a>\n'

            html += '''        </div>
    </details>
'''

            return html

        except Exception as e:
            # Log error but don't fail
            try:
                self.app.logger.error(
                    f"ReferencingPages: Failed to inject sidebar content: {e}"
                )
            except:
                pass
            return None


plugin_manager.register(ReferencingPages())
