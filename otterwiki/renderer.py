#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import re
import git

import mistune
from mistune.plugins import (
    plugin_table,
    plugin_url,
    plugin_strikethrough,
)
import bleach
from bleach.css_sanitizer import CSSSanitizer
import urllib.parse

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
            arr[n] = line.replace(cursormagicword, "")
            return n, "".join(arr)
    return None, text


def showmagicword(line, html):
    if line is None:
        return html
    arr = html.splitlines(True)
    arr[line] = cursormagicword + arr[line]
    return "".join(arr)



class mistunePluginTaskLists:
    """
    Rewrote plugin_task_lists from mistune/plugins/task_lists.py
    """
    TASK_LIST_ITEM = re.compile(r'^(\[[ xX]\])\s+')


    def task_lists_hook(self, md, tokens, state):
        return self._rewrite_all_list_items(tokens)


    def render_ast_task_list_item(self, children, level, checked):
        return {
            'type': 'task_list_item',
            'children': children,
            'level': level,
            'checked': checked,
        }


    def render_html_task_list_item(self, text, level, checked):
        checkbox = (
            '<input class="task-list-item-checkbox" '
            'type="checkbox" '
        )
        if checked:
            checkbox += ' checked/>'
        else:
            checkbox += '/>'

        if text.startswith('<p>'):
            text = text.replace('<p>', '<p>' + checkbox, 1)
        else:
            text = checkbox + text

        return '<li class="task-list-item">' + text + '</li>\n'


    def __call__(self, md):
        md.before_render_hooks.append(self.task_lists_hook)

        if md.renderer.NAME == 'html':
            md.renderer.register('task_list_item', self.render_html_task_list_item)
        elif md.renderer.NAME == 'ast':
            md.renderer.register('task_list_item', self.render_ast_task_list_item)


    def _rewrite_all_list_items(self, tokens):
        for tok in tokens:
            if tok['type'] == 'list_item':
                self._rewrite_list_item(tok)
            if 'children' in tok.keys():
                self._rewrite_all_list_items(tok['children'])
        return tokens


    def _rewrite_list_item(self, item):
        children = item['children']
        if children:
            first_child = children[0]
            text = first_child.get('text', '')
            m = self.TASK_LIST_ITEM.match(text)
            if m:
                mark = m.group(1)
                first_child['text'] = text[m.end():]

                params = item['params']
                if mark == '[ ]':
                    params = (params[0], False)
                else:
                    params = (params[0], True)

                item['type'] = 'task_list_item'
                item['params'] = params

plugin_task_lists = mistunePluginTaskLists()

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

    def reset_toc(self):
        self.toc_count = 0
        self.toc_tree = []
        self.toc_anchors = {}

    def image(self, src, alt_text, title):
        if not empty(title):
            return (
                '<img src="{}" class="img-fluid" title="{}" alt="{}">'.format(
                    src, title, alt_text
                )
            )
        return '<img src="{}" class="img-fluid" alt="{}">'.format(
            src, alt_text
        )

    def codespan(self, text):
        if text.startswith("$") and text.endswith("$"):
            return "\\(" + mistune.escape(text[1:-1]) + "\\)"
        return "<code>" + mistune.escape(text) + "</code>"

    def block_code(self, code, lang=None):
        prefix = ""
        if not lang:
            return '\n<pre class="code">{}</pre>\n'.format(
                mistune.escape(code.strip())
            )
        if cursormagicword in lang:
            lang = lang.replace(cursormagicword, "")
            prefix = cursormagicword
        cursorline, code = hidemagicword(code)
        if lang == "math":
            html = "".join(
                ["\\[{}\\]".format(line) for line in code.strip().splitlines()]
            )
        else:
            html = prefix + pygments_render(code, lang)
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
        self.md_renderer = OtterwikiMdRenderer(escape=False)
        # self.md_lexer = OtterwikiInlineLexer(self.md_renderer)
        self.mistune = mistune.create_markdown(
            renderer=self.md_renderer,
            plugins=[
                plugin_table,
                plugin_url,
                plugin_strikethrough,
                plugin_task_lists,
            ],
        )
        self.lastword = re.compile(r"([a-zA-Z_0-9\.]+)$")
        self.htmlcursor = "<span id=\"cursor\"></span>"
        # thanks to https://github.com/lepture/mistune/issues/158#issuecomment-830481284
        # we can enable tables in lists
        self.mistune.block.list_rules += ['table', 'nptable']

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

        html = self.mistune(text)
        # clean up html
        css_sanitizer = CSSSanitizer(
            allowed_css_properties=[
                'azimuth', 'background-color', 'border-bottom-color',
                'border-collapse', 'border-color', 'border-left-color',
                'border-right-color', 'border-top-color', 'clear',
                'color', 'cursor', 'direction', 'display', 'elevation',
                'float', 'font', 'font-family', 'font-size',
                'font-style', 'font-variant', 'font-weight', 'height',
                'letter-spacing', 'line-height', 'overflow', 'margin',
                'margin-bottom', 'margin-left', 'margin-right',
                'margin-top', 'pause', 'pause-after', 'pause-before',
                'padding', 'padding-bottom', 'padding-left',
                'padding-right', 'padding-top', 'pitch', 'pitch-range',
                'richness', 'speak', 'speak-header', 'speak-numeral',
                'speak-punctuation', 'speech-rate', 'stress',
                'text-align', 'text-decoration', 'text-indent',
                'unicode-bidi', 'vertical-align', 'voice-family',
                'volume', 'white-space', 'width',
            ]
        )
        html = bleach.clean(
            html,
            tags={
                'a', 'blockquote', 'br', 'code', 'del', 'div', 'em', 'h1',
                'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'hr', 'i',
                'img', 'input', 'ins', 'li', 'mark', 'ol', 'p', 'pre',
                'span', 'strong', 'table', 'tbody', 'td', 'th', 'thead',
                'tr', 'ul', 'video', 'audio', 'picture', 'source',
                'dl', 'dt', 'dd',
            },
            attributes={
                '*': ['class', 'style', 'width', 'height', 'id'],
                'a': ['href', 'rel'],
                'img': ['alt', 'title', 'src'],
                'input': ['type', 'disabled', 'checked'],
                'video' : ['controls', 'loop', 'muted'],
                'audio' : ['controls', 'loop', 'muted'],
                'picture' : ['media','srcset'],
                'source' : ['src', 'type', 'sizes'],
            },
            css_sanitizer=css_sanitizer,
        )

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
