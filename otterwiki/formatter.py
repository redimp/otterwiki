#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import re
import git

import mistune
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import html
from pygments.util import ClassNotFound

from flask import url_for
from otterwiki.storage import storage
from otterwiki.util import get_pagename

# Please check https://github.com/lepture/mistune-contrib
# for mistune extensions.

class HighlightRenderer(mistune.Renderer):
    def block_code(self, code, lang):
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % \
                mistune.escape(code.strip())
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
        except ClassNotFound:
            return '\n<pre><code>%s\n%s</code></pre>\n' % \
                (mistune.escape(lang.strip()), mistune.escape(code.strip()))
        formatter = html.HtmlFormatter(classprefix=".highlight ")
        return highlight(code, lexer, formatter)

def parse_wikilinks(md):
    wlre = re.compile(
        r'('
        r'(?<=\[\[)'
        r'[^\]]+?'
        r'(?=\]\])'
        r')'
        )
    matches = wlre.findall(md)
    # test if there are any wiki links
    if len(matches)<1:
        return md
    # compile re
    iwlre = re.compile(
            r'([^\|]+)\|?(.*)'
            )
    # fetch all existing pages
    pages = [get_pagename(x).lower() for x in storage.list_files() if x.endswith(".md")]
    # for every wikilink found ...
    for iwl in matches:
        style = ''
        title, pagename = iwlre.findall(iwl)[0]
        if pagename == '': pagename = title
        if pagename.lower() not in pages:
            style = ' class="notfound"'
        url = url_for('.view', pagename=pagename)
        link = '<a href="{}"{}>{}</a>'.format(url,style,title)
        md = md.replace("[[{}]]".format(iwl),link)

    return md


_renderer = HighlightRenderer()
_markdown = mistune.Markdown(renderer=_renderer)

def render_markdown(text):
    md = _markdown(text)
    md = parse_wikilinks(md)
    return md
