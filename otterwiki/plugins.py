#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
This file contains both the "plugin spec" for An Otter Wiki, and several
plugins included with the app itself. For now this is a proof of concept
that will be expanded in the future.

See docs/plugin_examples for examples.
"""

import pluggy

hookspec = pluggy.HookspecMarker("otterwiki")
hookimpl = pluggy.HookimplMarker("otterwiki")


class OtterWikiPluginSpec:
    """A hook specification namespace for OtterWiki."""

    @hookspec
    def setup(self, app, db, storage) -> None:
        """
        This hook receives the core objects and is to be used to
        initialize the plugin with the app, database, and storage.

        Args:
            app: The Flask application instance
            db: The SQLAlchemy database instance
            storage: The GitStorage instance for repository operations

        Returns:
            None
        """
        self.app = app
        self.db = db
        self.storage = storage

    @hookspec
    def renderer_markdown_preprocess(self, md: str) -> str | None:
        """
        This hook receives a markdown string, and can transform it any way it
        sees fit. It is called before the markdown is rendered into HTML.

        If multiple hooks exist, they will be chained, the output of
        each hook will be fed into the next one.

        Args:
            md: The raw markdown string to be processed

        Returns:
            The transformed markdown string
        """

    @hookspec
    def renderer_html_postprocess(self, html: str) -> str | None:
        """
        This hook receives an HTML string. It is called after the page's
        markdown has been rendered into HTML.

        Args:
            html: The rendered HTML string to be processed

        Returns:
            The transformed HTML string
        """

    @hookspec
    def page_view_htmlcontent_postprocess(self, html, page) -> str | None:
        """
        This hook receives the rendered HTML content of a page after markdown
        processing but before final display.

        Args:
            html: The rendered HTML content of the page
            page: The Page object representing the current page being viewed

        Returns:
            The transformed HTML content
        """

    @hookspec
    def template_html_head_inject(self, page) -> str | None:
        """
        This hook allows plugins to inject HTML content into the <head> section
        of the page template. The content will be added after the default CSS/JS.

        Args:
            page: The current page path (optional, may be None)

        Returns:
            HTML string to inject into the <head> section, or None
        """

    @hookspec
    def template_html_body_inject(self, page) -> str | None:
        """
        This hook allows plugins to inject HTML content at the end of the <body>
        section of the page template, before the closing </body> tag.

        Args:
            page: The current page path (optional, may be None)

        Returns:
            HTML string to inject before the closing </body> tag, or None
        """

    @hookspec
    def template_html_sidebar_left_inject(self, page) -> str | None:
        """
        This hook allows plugins to inject HTML content into the left sidebar
        (where the menu and optional page index are). The content will be appended
        to the existing sidebar content.

        Args:
            page: The current page path (optional, may be None)

        Returns:
            HTML string to inject to the left sidebar, or None
        """

    @hookspec
    def template_html_sidebar_right_inject(self, page) -> str | None:
        """
        This hook allows plugins to inject HTML content into the right sidebar
        (where the "On this page" block is). The content will be appended to the
        existing sidebar content.

        Args:
            page: The current page path (optional, may be None)

        Returns:
            HTML string to inject to the right sidebar, or None
        """

    @hookspec
    def renderer_process_link(
        self, link_html, link_url, link_text, link_title, page
    ) -> str | None:
        """
        This hook allows plugins to process and modify individual links during rendering.
        It's called for each link as it's being rendered from markdown.

        Args:
            link_html: The complete HTML string for the link (e.g., '<a href="...">text</a>')
            link_url: The URL/href attribute of the link
            link_text: The display text of the link
            link_title: The title attribute of the link (optional, may be None)
            page: The current page path (optional, may be None)

        Returns:
            The modified link HTML string
        """

    @hookspec
    def renderer_process_image(
        self, image_html, image_src, image_alt, image_title, page
    ) -> str | None:
        """
        This hook allows plugins to process and modify individual images during rendering.
        It's called for each image as it's being rendered from markdown.

        Args:
            image_html: The complete HTML string for the image (e.g., '<img src="..." alt="...">')
            image_src: The src attribute of the image
            image_alt: The alt text of the image
            image_title: The title attribute of the image (optional, may be None)
            page: The current page path (optional, may be None)

        Returns:
            The modified image HTML string
        """

    @hookspec
    def renderer_process_heading(
        self,
        heading_html,
        heading_text,
        heading_level,
        heading_anchor,
        page,
    ) -> str | None:
        """
        This hook allows plugins to process and modify individual headings during rendering.
        It's called for each heading as it's being rendered from markdown.

        Args:
            heading_html: The complete HTML string for the heading (e.g., '<h2 id="...">...</h2>')
            heading_text: The text content of the heading (may include HTML tags)
            heading_level: The heading level as an integer (1-6, corresponding to h1-h6)
            heading_anchor: The anchor/id attribute generated for the heading
            page: The current page path (optional, may be None)

        Returns:
            The modified heading HTML string
        """

    @hookspec
    def renderer_process_wikilink(
        self, wikilink_html, wikilink_url, wikilink_text, page
    ) -> str | None:
        """
        This hook allows plugins to process and modify individual wikilinks during rendering.
        It's called for each wikilink as it's being rendered from markdown.
        WikiLinks are defined in the format [[Page Name]] or [[Page Name|Display Text]].

        Args:
            wikilink_html: The complete HTML string for the wikilink (e.g., '<a href="...">text</a>')
            wikilink_url: The URL/href attribute of the wikilink
            wikilink_text: The display text of the wikilink
            page: The current page path (optional, may be None)

        Returns:
            The modified wikilink HTML string
        """

    @hookspec
    def repository_changed(self, changed_files: list) -> None:
        """
        This hook is triggered when the repository changes, including page/attachment
        creation, edit, or deletion. This also includes changes via the git web server
        or automatic pulls.

        Plugins cannot prevent the change, only read what was changed.

        Args:
            changed_files: List of file paths that were changed in the repository

        Returns:
            None
        """


# pluggy doesn't by default handle chaining the output of one plugin into
# another, so this is a small utility function to do this.
# this utility function will chain the result of each hook into the first
# argument of the next hook.
def chain_hooks(hook_name, value, *args, **kwargs):
    for impl in getattr(plugin_manager.hook, hook_name).get_hookimpls():
        fn = getattr(impl, 'function')
        value = fn(value, *args, **kwargs)
    return value


# this plugin_manager is exported so the normal pluggy API can be used in
# addition to the utility function above.
plugin_manager = pluggy.PluginManager("otterwiki")
plugin_manager.add_hookspecs(OtterWikiPluginSpec)
plugin_manager.load_setuptools_entrypoints("otterwiki")
