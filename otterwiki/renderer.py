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
from otterwiki.util import slugify, empty

# Please check https://github.com/lepture/mistune-contrib
# for mistune extensions.


def pygments_render(code, lang):
    try:
        lexer = get_lexer_by_name(lang, stripall=True)
    except ClassNotFound:
        return '\n<pre class="code">%s\n%s</pre>\n' % (
            mistune.escape(lang.strip()),
            mistune.escape(code.strip()),
        )
    formatter = html.HtmlFormatter(classprefix=".highlight ")
    return highlight(code, lexer, formatter)


class MyRenderer(mistune.Renderer):
    toc_count = 0
    toc_tree = []
    toc_anchors = {}

    def reset_toc(self):
        self.toc_count = 0
        self.toc_tree = []
        self.toc_anchors = {}

    def image(self, src, title, alt_text):
        if not empty(title):
            return '<img src="{}" class="img-fluid" title="{}" alt="{}">'.format(
                src, title, alt_text
            )
        return '<img src="{}" class="img-fluid" alt="{}">'.format(src, alt_text)

    def codespan(self, text):
        if text.startswith("$") and text.endswith("$"):
            return "\\(" + mistune.escape(text[1:-1]) + "\\)"
        return "<code>" + mistune.escape(text) + "</code>"

    def block_code(self, code, lang):
        if lang == "math":
            return "".join(["\\[{}\\]".format(line) for line in code.strip().splitlines()])
        elif not lang:
            return '\n<pre class="code">%s</pre>\n' % mistune.escape(code.strip())
        return pygments_render(code, lang)

    def header(self, text, level, raw=None):
        anchor = slugify(text)
        try:
            self.toc_anchors[anchor] += 1
            anchor = "{}-{}".format(anchor, self.toc_anchors[anchor])
        except KeyError:
            self.toc_anchors[anchor] = 0

        rv = '<h{level} id="{anchor}">{text}<a href="#{anchor}" class="anchor"><i class="fas fa-link"></i></a></h{level}>\n'.format(
            level=level,
            count=self.toc_count,
            text=text,
            anchor=anchor,
        )
        self.toc_tree.append((self.toc_count, text, level, raw, anchor))
        self.toc_count += 1
        return rv


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
        #pages = [get_pagename(x).lower() for x in storage.list_files() if x.endswith(".md")]
        # if the pagename is empty the title is the pagename
        if pagename == '': pagename = title
        # check if page exists
        #if pagename.lower() not in pages:
        #style = ' class="notfound"'
        # generate link
        url = url_for('view', path=pagename)
        link = '<a href="{}"{}>{}</a>'.format(url,style,title)
        return link

__renderer = MyRenderer()
__inline = MyInlineLexer(__renderer)
__markdown = mistune.Markdown(renderer=__renderer, inline=__inline)


def markdown_render(text):
    global __renderer
    __renderer.reset_toc()
    md = __markdown(text)
    return md


def markdown_get_toc():
    global __renderer
    return __renderer.toc_tree.copy()
