#!/usr/bin/env python3

"""
This is an example plugin for An Otter Wiki.

The hook is a function that formats and appends some metadata
to the rendered page html.
"""

from otterwiki.plugins import hookimpl

@hookimpl
def page_view_htmlcontent_postprocess(html, page):
    if page.metadata is not None:
        html += \
        f"""
        <div style="margin-top: 5rem; padding-top: .5rem; border-top: 1px dashed rgba(128,128,128,0.2); color: rgba(128,128,128,0.5);" class="text-small">
            Last modified {page.metadata["datetime"].strftime("%Y-%m-%d %H:%M:%S")} by {page.metadata["author_name"]}
        </div>
        """
    return html
