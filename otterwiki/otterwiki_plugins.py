# This file contains both the "plugin spec" for OtterWiki, and several
# plugins included with the app itself.

import pluggy
import re
import urllib

hookspec = pluggy.HookspecMarker("otterwiki")
hookimpl = pluggy.HookimplMarker("otterwiki")


class OtterWikiPluginSpec:
    """A hook specification namespace for OtterWiki."""

    @hookspec
    def preprocess_markdown(self, md):
        """
        This hook receives a markdown string, and can transform it any way it
        sees fit. It is called before the markdown is rendered into HTML.
        """


class WikiLinkPlugin:
    """This plugin preprocesses links in the [[WikiLink]] style."""

    wiki_link_outer = re.compile(
        r'\[\['
        r'([^\]]+)'
        r'\]\](?!\])'  # [[  # ...  # ]]
    )
    wiki_link_inner = re.compile(r'([^\|]+)\|?(.*)')

    @hookimpl
    def preprocess_markdown(self, md):
        """
        Will turn
            [[Page]]
            [[Title|Link]]
        into
            [Page](/Page)
            [Title](/Link)
        """
        for m in self.wiki_link_outer.finditer(md):
            title, link = self.wiki_link_inner.findall(m.group(1))[0]
            if link == '':
                link = title
            if not link.startswith("/"):
                link = f"/{link}"
            # quote link (and just in case someone encoded already: unquote)
            link = urllib.parse.quote(urllib.parse.unquote(link), safe="/#")
            md = md.replace(m.group(0), f'[{title}]({link})')

        return md


# pluggy doesn't by default handle chaining the output of one plugin into
# another, so this is a small utility function to do this. it likely does not
# support hook wrappers correctly.
def chain_hooks_single_arg(hook_name, **kwargs):
    if len(kwargs.keys()) > 1:
        raise "chain_hooks_single_arg is designed to handle a single argument."

    [(arg_name, arg)] = list(kwargs.items())
    impls = getattr(plugin_manager.hook, hook_name).get_hookimpls()

    result = arg
    for impl in impls:
        fn = getattr(impl, 'function')
        result = fn(**{arg_name: result})

    return result


# this plugin_manager is exported so the normal pluggy API can be used in
# addition to the utility function above.
plugin_manager = pluggy.PluginManager("otterwiki")
plugin_manager.add_hookspecs(OtterWikiPluginSpec)
plugin_manager.register(WikiLinkPlugin())
plugin_manager.load_setuptools_entrypoints("otterwiki")
