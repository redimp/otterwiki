#!/usr/bin/env python3

"""
This is an example plugin for An Otter Wiki.

The hook is inside a class named AuthorSignature.

This class is making use of the setup() hook which gives the plugin access to
An Otter Wikis core objects: The Flask app, the database and the storage.

Note: To make the plugin_manager find it, the class has to be registered.
"""

from otterwiki.plugins import hookimpl, plugin_manager


class AuthorSignature:
    @hookimpl
    def setup(
        self, app, db, storage
    ) -> None:  # pyright: ignore [reportUnusedVariable]
        self.storage = storage

    @hookimpl
    def page_view_htmlcontent_postprocess(self, html, page):
        if page.metadata is not None:
            # Getting the first sha of the page file to request the metadata to be used
            # for the page creation info.
            first_sha = self.storage.repo.git.rev_list(
                "--max-parents=0", "HEAD", page.filename
            )
            creation_metadata = self.storage.metadata(page.filename, first_sha)
            html += f"""
            <div style="margin-top: 5rem; padding-top: .5rem; border-top: 1px dashed rgba(128,128,128,0.2); color: rgba(128,128,128,0.5);" class="text-small">
                Last modified {page.metadata["datetime"].strftime("%Y-%m-%d %H:%M:%S")} by {page.metadata["author_name"]}.
                <br/>Created {creation_metadata['datetime'].strftime("%Y-%m-%d %H:%M:%S")} by {creation_metadata['author_name']}.
            </div>
            """
        return html


plugin_manager.register(AuthorSignature())
