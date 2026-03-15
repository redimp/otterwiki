#!/usr/bin/env python3
# vim: set et ts=8 sts=4 sw=4 ai:

from otterwiki.util import empty
from otterwiki.plugins import collect_hook, call_hook
from otterwiki.renderer import render


def generate_help():
    """
    List the help available for all plugins or display the help of the requested plugin.
    """
    content = "# Plugins\n"

    plugins_info = collect_hook("info")

    if len(plugins_info) < 1:
        content += "<em>No plugins found.</em>"

    # sort plugins_info by category, name
    plugins_info.sort(key=lambda info: (info[2], info[0]))

    plugins_without_help = []

    last_category = None
    last_category_printed = False
    # glue together all documentation
    for plugin, description, category in plugins_info:
        if category != last_category:

            last_category = category
            last_category_printed = False

        help = call_hook("help", plugin=plugin)
        if empty(help):
            plugins_without_help += [(plugin, description, category)]
        else:
            if last_category_printed is False:
                content += f"\n## {category}\n\n"
                category_prelude = "\n".join(
                    collect_hook("help_category_prelude", category)
                )
                if not empty(category_prelude):
                    content += category_prelude
                last_category_printed = True
            content += f"\n### {plugin}\n\n{help}\n<div style=\"clear:both;\"></div>\n"

    if plugins_without_help:
        content += "\n## Other Plugins\n\n"
        for plugin, description, category in plugins_without_help:
            content += f"- {plugin}: {description}\n"

    content, toc, library_requirements = render.markdown(content)

    return content, toc, library_requirements


def collect_plugin_info(category=None):
    """
    Lists the info for all plugins
    """
    plugins_info = collect_hook("info")
    if category:
        plugins_info = [p for p in plugins_info if p[2] == category]
    # sort plugins_info by category, name
    plugins_info.sort(key=lambda info: (info[2], info[0]))

    return plugins_info
