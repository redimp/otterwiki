#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import re
import git

import mistune
from mistune.plugins import plugin_table, plugin_url, plugin_task_lists, plugin_strikethrough

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import html
from pygments.util import ClassNotFound

from flask import url_for
from markupsafe import Markup
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

# inner wiki link regular expression
wiki_link_iwlre = re.compile(r'([^\|]+)\|?(.*)')

def plugin_wiki(md):
    """
    Plugin for rendering wiki Links:
    [[Page]]
    [[Title|Link]]
    """
    # define regex for Wiki links
    WIKI_PATTERN = (
        r'\[\['                   # [[
        r'([^\]]+)'               # ...
        r'\]\](?!\])'             # ]]
    )
    # define how to parse matched item
    def parse_wiki(inline, m, state):
        # ``inline`` is ``md.inline``, see below
        # ``m`` is matched regex item
        title, page = wiki_link_iwlre.findall(m.group(1))[0]
        if page == '': page = title
        return 'wiki', url_for('view', path=page), title

    # define how to render HTML
    def render_html_wiki(link, title):
        return f'<a href="{link}">{title}</a>'

    # this is an inline grammar, so we register wiki rule into md.inline
    md.inline.register_rule('wiki', WIKI_PATTERN, parse_wiki)
    # add wiki rule into active rules
    md.inline.rules.append('wiki')
    # add HTML renderer
    if md.renderer.NAME == 'html':
        md.renderer.register('wiki', render_html_wiki)

class OtterwikiMdRenderer(mistune.HTMLRenderer):
    toc_count = 0
    toc_tree = []
    toc_anchors = {}

    def reset_toc(self):
        self.toc_count = 0
        self.toc_tree = []
        self.toc_anchors = {}

    def image(self, src, alt_text, title):
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

    def heading(self, text, level):
        raw = Markup(text).striptags()
        anchor = slugify(raw)
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


class OtterwikiRenderer:
    def __init__(self):
        self.md_renderer = OtterwikiMdRenderer(escape=False)
        # self.md_lexer = OtterwikiInlineLexer(self.md_renderer)
        self.mistune = mistune.create_markdown(renderer=self.md_renderer,
                plugins=[
                    plugin_task_lists,
                    plugin_table,
                    plugin_url,
                    plugin_strikethrough,
                    plugin_wiki,
                ])
        self.lastword = re.compile(r"([a-zA-Z_0-9\.]+)$")
        self.htmlcursor = "<span id=\"cursor\"></span>"

    def markdown(self, text, cursor=None):
        self.md_renderer.reset_toc()
        #import pdb; pdb.set_trace()
        # add cursor position
        if cursor is not None:
            text_arr = text.splitlines()
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
                text = "\n".join(text_arr)

        html = self.mistune(text)
        toc = self.md_renderer.toc_tree.copy()
        if cursor is not None and line > 0:
            # replace the magic word with the cursor span
            html = html.replace(cursormagicword,self.htmlcursor)
        elif cursor is not None:
            html = self.htmlcursor + html

        # clean magicword out of toc
        toc = [
            (a, b.replace(cursormagicword,""), c, d, e) for (a,b,c,d,e) in toc
        ]

        return html, toc

    def hilight(self, code, lang):
        return pygments_render(code, lang)

render = OtterwikiRenderer()
