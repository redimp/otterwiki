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

# the cursor magic word which is ignored by the rendering
cursormagicword = "CuRsoRm4g1cW0Rd"

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

def hidemagicword(text):
    arr = text.splitlines(True)
    for n, line in enumerate(arr):
        if cursormagicword in line:
            arr[n] = line.replace(cursormagicword,"")
            return n, "".join(arr)
    return None, text

def showmagicword(line, html):
    if line is None:
        return html
    arr = html.splitlines(True)
    arr[line]=cursormagicword+arr[line]
    return "".join(arr)

class OtterwikiMdRenderer(mistune.HTMLRenderer):
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

    def block_code(self, code, lang=None):
        prefix = ""
        if not lang:
            return '\n<pre class="code">{}</pre>\n'.format(mistune.escape(code.strip()))
        if cursormagicword in lang:
            lang = lang.replace(cursormagicword,"")
            prefix = cursormagicword
        cursorline, code = hidemagicword(code)
        if lang == "math":
            html = "".join(["\\[{}\\]".format(line) for line in code.strip().splitlines()])
        else:
            html = prefix+pygments_render(code, lang)
        html = showmagicword(cursorline, html)
        return prefix+html

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


#class OtterwikiInlineLexer(mistune.InlineLexer):
#    def __init__(self, *args, **kwargs):
#        super(OtterwikiInlineLexer, self).__init__(*args, **kwargs)
#        self.enable_wiki_link()
#
#    def enable_wiki_link(self):
#        self.rules.wiki_link = re.compile(
#            r'\[\['                   # [[
#            r'([^\]]+)'               # ...
#            r'\]\]'                   # ]]
#        )
#        self.default_rules.insert(0, 'wiki_link')
#        # inner regular expression
#        self.wiki_link_iwlre = re.compile(
#                r'([^\|]+)\|?(.*)'
#                )
#
#    def output_wiki_link(self, m):
#        # initial style
#        style = ''
#        # parse for title and pagename
#        title, pagename = self.wiki_link_iwlre.findall(m.group(1))[0]
#        # fetch all existing pages
#        #pages = [get_pagename(x).lower() for x in storage.list_files() if x.endswith(".md")]
#        # if the pagename is empty the title is the pagename
#        if pagename == '': pagename = title
#        # check if page exists
#        #if pagename.lower() not in pages:
#        #style = ' class="notfound"'
#        # generate link
#        url = url_for('view', path=pagename)
#        link = '<a href="{}"{}>{}</a>'.format(url,style,title)
#        return link

class OtterwikiRenderer:
    def __init__(self):
        self.md_renderer = OtterwikiMdRenderer()
        # self.md_lexer = OtterwikiInlineLexer(self.md_renderer)
        self.mistune = mistune.create_markdown(renderer=self.md_renderer)
        self.lastword = re.compile("([a-zA-Z_0-9\.]+)$")

    def markdown(self, text, cursor=None):
        self.md_renderer.reset_toc()
        # add cursor position
        if cursor is not None:
            text_arr = text.splitlines(True)
            try:
                line = min(len(text_arr)-1, int(cursor)-1)
            except ValueError:
                line = 0
            # find a line to place the cursor
            while line > 0 and not len(self.lastword.findall(text_arr[line])) > 0:
                line -= 1
            if line > 0:
                # add empty span at the end of the edited line
                text_arr[line] = self.lastword.sub(r"\1{}".format(cursormagicword), text_arr[line], count=1)
                text = "".join(text_arr)

        html = self.mistune(text)
        toc = self.md_renderer.toc_tree.copy()
        if cursor is not None and line > 0:
            # replace the magic word with the cursor span
            html = html.replace(cursormagicword,"<span id=\"cursor\"></span>")
        elif cursor is not None:
            html = "<span id=\"cursor\"></span>" + html

        # clean magicword out of toc
        toc = [
            (a, b.replace(cursormagicword,""), c, d, e) for (a,b,c,d,e) in toc
        ]

        return html, toc

    def hilight(self, code, lang):
        return pygments_render(code, lang)

render = OtterwikiRenderer()
