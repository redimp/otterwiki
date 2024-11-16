#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import re

import mistune
from mistune.plugins import (
    plugin_table,
    plugin_url,
    plugin_strikethrough,
)

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import html
from pygments.util import ClassNotFound

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
    plugin_alerts,
    plugin_wikilink,
)
from otterwiki.plugins import chain_hooks
from bs4 import BeautifulSoup

# the cursor magic word which is ignored by the rendering
cursormagicword = "CuRsoRm4g1cW0Rd"

#
# patch mistune table_plugin so that not all the newlines at the end of a table are removed
#
mistune.plugins.plugin_table.TABLE_PATTERN = re.compile(  # pyright: ignore
    r' {0,3}\|(.+)\n *\|( *[-:]+[-| :]*)\n((?: *\|.*(?:\n|$))*)\n{0,1}'
)
mistune.plugins.plugin_table.NP_TABLE_PATTERN = re.compile(  # pyright: ignore
    r' {0,3}(\S.*\|.*)\n *([-:]+ *\|[-| :]*)\n((?:.*\|.*(?:\n|$))*)\n{0,1}'
)


def _pre_copy_to_clipboard_tag():
    return f"""<div class="copy-to-clipboard-outer"><div class="copy-to-clipboard-inner"><button class="btn alt-dm btn-xsm copy-to-clipboard" type="button"  onclick="otterwiki.copy_to_clipboard(this);"><i class="fa fa-copy" aria-hidden="true" alt="Copy to clipboard""></i></button></div><pre class="copy-to-clipboard code">"""


class CodeHtmlFormatter(html.HtmlFormatter):

    def wrap(self, source):
        yield 0, _pre_copy_to_clipboard_tag()
        for i, t in source:
            yield i, t
        yield 0, '</pre></div>'


def pygments_render(code, lang):
    try:
        lexer = get_lexer_by_name(lang, stripall=True)
    except ClassNotFound:
        return (
            '\n'
            + _pre_copy_to_clipboard_tag()
            + '%s\n%s</pre></div>\n'
            % (
                mistune.escape(lang.strip()),
                mistune.escape(code.strip()),
            )
        )
    formatter = CodeHtmlFormatter(classprefix=".highlight ")
    # formatter = html.HtmlFormatter(classprefix=".highlight ")
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


def clean_html(html: str) -> str:
    # use BeautifulSoup to identify tags we want to remove / escape
    # since we get incomplete tags via inline html we have to work
    # with the html string and can not use what bs makes out of it
    REMOVE_ATTRIBUTES = [
        'onclick',
        'onload',
        'onerror',
        'onfocus',
        'onbeforeprint',
        'beforeunload',
        'onblur',
        'onchange',
        'oncopy',
        'oncut',
        'ondblclick',
        'ondrag',
        'draggable',
        'ondragend',
        'ondragenter',
        'ondragleave',
        'ondragover',
        'ondragstart',
        'ondrop',
        'onfocus',
        'onfocusin',
        'onfocusout',
        'onhashchange',
        'oninput',
        'oninvalid',
        'onkeydown',
        'onkeypress',
        'onkeyup',
        'onload',
        'onmousedown',
        'onmouseenter',
        'onmouseleave',
        'onmousemove',
        'onmouseover',
        'onmouseout',
        'onmouseup',
        'onoffline',
        'ononline',
        'onpagehide',
        'onpageshow',
        'onpaste',
        'onresize',
        'onreset',
        'onscroll',
        'onsearch',
        'onselect',
        'ontoggle',
        'ontouchcancel',
        'ontouchend',
        'ontouchmove',
        'ontouchstart',
        'onunload',
    ]
    REMOVE_TAGS = ['style', 'script', 'blink', 'marque']

    _escape = False
    soup = BeautifulSoup(html, 'html.parser')
    for element in soup:
        if element.name in REMOVE_TAGS:  # pyright: ignore
            _escape = True
            break
        try:
            if any(
                x in element.attrs.keys() for x in REMOVE_ATTRIBUTES
            ):  # pyright: ignore
                _escape = True
                break
        except AttributeError:
            break
    if _escape:
        # take nom prisoners
        html = escape(html)
    return html


class OtterwikiMdRenderer(mistune.HTMLRenderer):
    toc_count = 0
    toc_tree = []
    toc_anchors = {}

    def __init__(self, env, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.env = env

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
        return '<img src="{}" class="img-fluid" alt="{}">'.format(src, alt)

    def codespan(self, text):
        if text.startswith("$") and text.endswith("$"):
            return "\\(" + mistune.escape(text[1:-1]) + "\\)"
        return "<code>" + mistune.escape(text) + "</code>"

    def block_code(self, code, info=None):
        prefix = ""
        if not info:
            return (
                '\n'
                + _pre_copy_to_clipboard_tag()
                + '{}</pre></div>\n'.format(mistune.escape(code.strip()))
            )
        if cursormagicword in info:
            info = info.replace(cursormagicword, "")
            prefix = cursormagicword
        cursorline, code = hidemagicword(code)
        if info == "math":
            html = "".join(
                ["\\[{}\\]".format(line) for line in code.strip().splitlines()]
            )
        elif info == "mermaid":
            html = "".join(
                ["\\[{}\\]".format(line) for line in code.strip().splitlines()]
            )
            # replace \n with <br/> for convinient diagram writing (and match the github syntax)
            code = code.replace("\\n", "<br/>")
            html = '\n<pre class="mermaid">{}\n</pre>\n'.format(code.strip())
            return html
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


class OtterwikiInlineParser(mistune.InlineParser):
    def __init__(self, env, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.env = env

    def parse_std_link(self, m, state):
        line = m.group(0)
        text = m.group(1)
        link = mistune.inline_parser.ESCAPE_CHAR.sub(r'\1', m.group(2))
        if link.startswith('<') and link.endswith('>'):
            link = link[1:-1]
        elif link.startswith("./"):
            if self.env.get("PAGE_URL", None) is not None:
                link = self.env["PAGE_URL"]+"/"+link

        title = m.group(3)
        if title:
            title = mistune.inline_parser.ESCAPE_CHAR.sub(r'\1', title[1:-1])

        if line[0] == '!':
            return 'image', mistune.escape_url(link), text, title

        return self.tokenize_link(line, link, text, title, state)

class OtterwikiMdParser(mistune.Markdown):
    def __init__(self, renderer, block=None, inline=None, plugins=None, env={}):
        self.env = env
        super().__init__(renderer=renderer, block=block, inline=inline, plugins=plugins)

class OtterwikiRenderer:
    def __init__(self, config={}):
        self.env = {
            "config" : config,
        }
        self.md_renderer = OtterwikiMdRenderer(env=self.env)
        self.inline_renderer = OtterwikiInlineParser(env=self.env, renderer=self.md_renderer, hard_wrap=False)
        self.mistune = OtterwikiMdParser(
            renderer=self.md_renderer,
            inline=self.inline_renderer,
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
                plugin_alerts,
                plugin_wikilink,
            ],
            env=self.env,
        )
        self.lastword = re.compile(r"([a-zA-Z_0-9\.]+)$")
        self.htmlcursor = " <span id=\"otterwiki_cursor\"></span> "
        # thanks to https://github.com/lepture/mistune/issues/158#issuecomment-830481284
        # we can enable tables in lists
        self.mistune.block.list_rules += ['table', 'nptable']  # pyright:ignore

    def markdown(self, text, cursor=None, **kwargs):
        self.md_renderer.reset_toc()
        # do the preparsing
        text = chain_hooks("renderer_markdown_preprocess", text)
        # add cursor position
        if cursor is not None:
            text_arr = text.splitlines()
            try:
                line = min(len(text_arr) - 1, int(cursor) + 1)
            except ValueError:
                line = 0
            # find a line to place the cursor
            while (
                line > 0 and not len(self.lastword.findall(text_arr[line])) > 0
            ):
                line -= 1
            if line > 0:
                # add empty span at the beginning of the edited line
                text_arr[line] = self.lastword.sub(
                    r"\1{}".format(cursormagicword), text_arr[line], count=1
                )
                text = "\n".join(text_arr)
        else:
            line = 0

        # store extra kwargs in environment
        for k,v in kwargs.items():
            self.env[k.upper()] = v
        html = self.mistune(text)
        # clean extra kwargs from environment
        for k,v in kwargs.items():
            del self.env[k.upper()]
        # generate the toc
        toc = self.md_renderer.toc_tree.copy()
        if cursor is not None and line > 0:
            # replace the magic word with the cursor span
            html = html.replace(cursormagicword, self.htmlcursor)
        elif cursor is not None:
            html = self.htmlcursor + html

        text = chain_hooks("renderer_html_postprocess", text)

        # clean magicword out of toc
        toc = [
            (
                a,
                b.replace(cursormagicword, ""),
                c,
                d.replace(cursormagicword, ""),
                e,
            )
            for (a, b, c, d, e) in toc
        ]

        # make sure the page content is clean html.
        # we shove it through BeautifulSoup.prettify this will get rid
        # of wrong placed tags, too many closed tags and so on.
        soup = BeautifulSoup(html, 'html.parser')
        html = str(soup)

        return html, toc

# unconfigured renderer for testing and rendering about()
render = OtterwikiRenderer()
