#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai:

import re

import mistune
from mistune.plugins import (
    plugin_table,
    plugin_url,
    plugin_strikethrough,
)
import urllib.parse

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import html
from pygments.util import ClassNotFound

from flask import url_for
from markupsafe import Markup, escape
from otterwiki.util import slugify, empty
from otterwiki.renderer_plugins import (
        plugin_task_lists,
        plugin_footnotes,
        plugin_mark,
        plugin_fancy_blocks,
        plugin_spoiler,
        plugin_fold,
        plugin_math,
        )
from bs4 import BeautifulSoup

# the cursor magic word which is ignored by the rendering
cursormagicword = "CuRsoRm4g1cW0Rd"

#
# patch mistune table_plugin so that not all the newlines at the end of a table are removed
#
mistune.plugins.plugin_table.TABLE_PATTERN = re.compile( # pyright: ignore
    r' {0,3}\|(.+)\n *\|( *[-:]+[-| :]*)\n((?: *\|.*(?:\n|$))*)\n{0,1}'
)
mistune.plugins.plugin_table.NP_TABLE_PATTERN = re.compile( # pyright: ignore
    r' {0,3}(\S.*\|.*)\n *([-:]+ *\|[-| :]*)\n((?:.*\|.*(?:\n|$))*)\n{0,1}'
)

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
            arr[n] = line.replace(cursormagicword, "")
            return n, "".join(arr)
    return None, text


def showmagicword(line, html):
    if line is None:
        return html
    arr = html.splitlines(True)
    arr[line] = cursormagicword + arr[line]
    return "".join(arr)


def clean_html(html):
    # use BeautifulSoup to identify tags we want to remove / escape
    # since we get iincomplete tags via inline html we have to work
    # with the html string and can not use what bs makes out of it
    _escape = False
    soup = BeautifulSoup(html, 'html.parser')
    for element in soup:
        if element.name in ['script', 'marque', 'blink']: # pyright: ignore
            _escape = True
            break
        try:
            if any(x in element.attrs.keys() for x in ['onclick','onload']): # pyright: ignore
                _escape = True
                break
        except AttributeError:
            break
    if _escape:
        # take nom prisoners
       html = escape(html)
    return html


# wiki links


wiki_link_outer = re.compile(
    r'\[\[' r'([^\]]+)' r'\]\](?!\])'  # [[  # ...  # ]]
)
wiki_link_inner = re.compile(r'([^\|]+)\|?(.*)')


def preprocess_wiki_links(md):
    """
    pre-mistune-parser for wiki links. Will turn
        [[Page]]
        [[Title|Link]]
    into
        [Page](/Page)
        [Title](/Link)
    """
    for m in wiki_link_outer.finditer(md):
        title, link = wiki_link_inner.findall(m.group(1))[0]
        if link == '':
            link = title
        if not link.startswith("/"):
            link = f"/{link}"
        # quote link (and just in case someone encoded already: unquote)
        link = urllib.parse.quote(urllib.parse.unquote(link), safe="/#")
        md = md.replace(m.group(0), f'[{title}]({link})')

    return md


class OtterwikiMdRenderer(mistune.HTMLRenderer):
    toc_count = 0
    toc_tree = []
    toc_anchors = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def inline_html(self, html):
        return clean_html(html)

    def block_html(self, html):
        return clean_html(html)

    def reset_toc(self):
        self.toc_count = 0
        self.toc_tree = []
        self.toc_anchors = {}

    def image(self, src, alt="", title=None):
        if not empty(title):
            return (
                '<img src="{}" class="img-fluid" title="{}" alt="{}">'.format(
                    src, title, alt
                )
            )
        return '<img src="{}" class="img-fluid" alt="{}">'.format(
            src, alt
        )

    def codespan(self, text):
        if text.startswith("$") and text.endswith("$"):
            return "\\(" + mistune.escape(text[1:-1]) + "\\)"
        return "<code>" + mistune.escape(text) + "</code>"

    def block_code(self, code, info=None):
        prefix = ""
        if not info:
            return '\n<pre class="code">{}</pre>\n'.format(
                mistune.escape(code.strip())
            )
        if cursormagicword in info:
            info = info.replace(cursormagicword, "")
            prefix = cursormagicword
        cursorline, code = hidemagicword(code)
        if info == "math":
            html = "".join(
                ["\\[{}\\]".format(line) for line in code.strip().splitlines()]
            )
        else:
            html = prefix + pygments_render(code, info)
        html = showmagicword(cursorline, html)
        return prefix + html

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
        self.md_renderer = OtterwikiMdRenderer()
        # self.md_lexer = OtterwikiInlineLexer(self.md_renderer)
        self.mistune = mistune.create_markdown(
            renderer=self.md_renderer,
            plugins=[
                plugin_table,
                plugin_url,
                plugin_strikethrough,
                plugin_task_lists,
                plugin_footnotes,
                plugin_mark,
                plugin_fancy_blocks,
                plugin_spoiler,
                plugin_fold,
                plugin_math,
            ],
        )
        self.lastword = re.compile(r"([a-zA-Z_0-9\.]+)$")
        self.htmlcursor = "<span id=\"cursor\"></span>"
        # thanks to https://github.com/lepture/mistune/issues/158#issuecomment-830481284
        # we can enable tables in lists
        self.mistune.block.list_rules += ['table', 'nptable']  # pyright:ignore

    def markdown(self, text, cursor=None):
        self.md_renderer.reset_toc()
        # do the preparsing
        text = preprocess_wiki_links(text)
        # add cursor position
        if cursor is not None:
            text_arr = text.splitlines()
            try:
                line = min(len(text_arr) - 1, int(cursor) - 1)
            except ValueError:
                line = 0
            # find a line to place the cursor
            while (
                line > 0 and not len(self.lastword.findall(text_arr[line])) > 0
            ):
                line -= 1
            if line > 0:
                # add empty span at the end of the edited line
                text_arr[line] = self.lastword.sub(
                    r"\1{}".format(cursormagicword), text_arr[line], count=1
                )
                text = "\n".join(text_arr)
        else:
            line = 0

        html = self.mistune(text)
        # generate the toc
        toc = self.md_renderer.toc_tree.copy()
        if cursor is not None and line > 0:
            # replace the magic word with the cursor span
            html = html.replace(cursormagicword, self.htmlcursor)
        elif cursor is not None:
            html = self.htmlcursor + html

        # clean magicword out of toc
        toc = [
            (a, b.replace(cursormagicword, ""), c, d, e)
            for (a, b, c, d, e) in toc
        ]

        return html, toc

    def hilight(self, code, lang):
        return pygments_render(code, lang)


render = OtterwikiRenderer()
