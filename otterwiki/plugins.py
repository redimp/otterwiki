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
        """
        self.app = app
        self.db = db
        self.storage = storage

    @hookspec
    def renderer_markdown_preprocess(self, md: str) -> str | None:
        """
        This hook receives a markdown string, and can transform it any way it
        sees fit. It is called before the markdown is rendered into HTML.

        If multiple hooks exits, they will be chained, the output of
        each hook will be fed into the next one.
        """

    @hookspec
    def renderer_html_postprocess(self, html: str) -> str | None:
        """
        This hooks receive a html string. It is called after the pages
        markdown has been rendered into html.
        """

    @hookspec
    def page_view_htmlcontent_postprocess(self, html, page) -> str | None:
        """
        This hooks receives a html string containing the page content.
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
