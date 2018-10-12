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

from pprint import pprint

# Please check https://github.com/lepture/mistune-contrib
# for mistune extensions.

#class MyPygmentsMixin(object):
class MyRenderer(mistune.Renderer):
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

#class MyRenderer(mistune.Renderer, MyPygmentsMixin):
#    def __init__(self, *args, **kwargs):
#        super(MyRenderer, self).__init__(*args, **kwargs)

class MyInlineLexer(mistune.InlineLexer):
    def __init__(self, *args, **kwargs):
        super(MyInlineLexer, self).__init__(*args, **kwargs)
        self.enable_wiki_link()

    def enable_wiki_link(self):
        self.rules.wiki_link = re.compile(
            r'\[\['                   # [[
            r'([^\]]+)'               # ...
            r'\]\]'                   # ]]
        )
        self.default_rules.insert(0, 'wiki_link')
        # inner regular expression
        self.wiki_link_iwlre = re.compile(
                r'([^\|]+)\|?(.*)'
                )

    def output_wiki_link(self, m):
        # initial style
        style = ''
        # parse for title and pagename
        title, pagename = self.wiki_link_iwlre.findall(m.group(1))[0]
        # fetch all existing pages
        pages = [get_pagename(x).lower() for x in storage.list_files() if x.endswith(".md")]
        # if the pagename is empty the title is the pagename
        if pagename == '': pagename = title
        # check if page exists
        if pagename.lower() not in pages:
            style = ' class="notfound"'
        # generate link
        url = url_for('view', pagename=pagename)
        link = '<a href="{}"{}>{}</a>'.format(url,style,title)
        return link

_renderer = MyRenderer()
_inline = MyInlineLexer(_renderer)
_markdown = mistune.Markdown(renderer=_renderer, inline=_inline)

def render_markdown(text):
    md = _markdown(text)
    return md
