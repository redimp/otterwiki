#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import re
import mistune
from bs4 import BeautifulSoup
from markupsafe import Markup, escape
from mistune.plugins import (
    plugin_strikethrough,
    plugin_table,
    plugin_url,
    plugin_abbr,
)
from pygments.formatters import HtmlFormatter
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

from otterwiki.plugins import chain_hooks
from otterwiki.renderer_plugins import (
    plugin_alerts,
    plugin_fancy_blocks,
    plugin_fold,
    plugin_footnotes,
    plugin_mark,
    plugin_math,
    plugin_spoiler,
    plugin_task_lists,
    plugin_wikilink,
    plugin_frontmatter,
    plugin_frontmatter_title,
)
from otterwiki.util import empty, slugify, cursormagicword

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


class CodeHtmlFormatter(HtmlFormatter):
    def wrap(self, source):
        yield 0, _pre_copy_to_clipboard_tag()
        for i, t in source:
            yield i, t
        yield 0, '</pre></div>'


def pygments_render(code, lang, linenumbers=False):
    try:
        lexer = get_lexer_by_name(lang.strip(), stripall=False)
    except ClassNotFound:
        return (
            '\n'
            + _pre_copy_to_clipboard_tag()
            + '%s\n%s</pre></div>\n'
            % (
                mistune.escape(lang),
                mistune.escape(code),
            )
        )
    linenos = "table" if linenumbers else None
    formatter = CodeHtmlFormatter(classprefix=".highlight ", linenos=linenos)
    html = highlight(code, lexer, formatter)
    # make sure wikilinks are not present in the code block
    html = (
        html.replace("&#39;", "&apos;")
        .replace("[", "&#91;")
        .replace("]", "&#93;")
    )
    return html


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


def parse_custom_allowlist(custom_allowlist: str = None) -> tuple:
    """
    Parse custom allowlist string into tags and attributes dictionaries.
    """
    custom_tags = []
    custom_attributes = {}

    if custom_allowlist and custom_allowlist.strip():
        for item in custom_allowlist.split(','):
            item = item.strip()
            if not item:
                continue

            # to separate tag from attributes
            parts = item.split('[', 1)
            tag_name = parts[0].strip().lower()

            if tag_name:
                custom_tags.append(tag_name)

            if len(parts) > 1:
                attrs_str = parts[1].rstrip(']').strip()
                if attrs_str:
                    attrs = [
                        attr.strip().lower()
                        for attr in attrs_str.split()
                        if attr.strip()
                    ]
                    if attrs:
                        custom_attributes[tag_name] = attrs

    return custom_tags, custom_attributes


def clean_html(
    html: str, custom_tags: list = None, custom_attributes: dict = None
) -> str:
    """
    Clean HTML using an allowlist approach - only allow safe tags and attributes.
    This prevents XSS attacks via various vectors like:
    - <script> tags
    - Event handlers (onclick, onload, onbegin, etc.)
    - Dangerous protocols (javascript:, data:)
    - Dangerous tags (object, embed, iframe, svg with events, etc.)
    """

    # tags and attrs are logically groupped by types
    # fmt: off
    ALLOWED_TAGS = [
        'p', 'br', 'hr', 'span', 'div',
        'strong', 'em', 'b', 'i', 'u', 's', 'strike', 'del', 'ins', 'sub', 'sup', 'mark', 'small',
        'ul', 'ol', 'li', 'dl', 'dt', 'dd',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'code', 'pre', 'kbd', 'samp', 'var',
        'blockquote', 'q', 'cite',
        'table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th', 'caption', 'col', 'colgroup',
        'a', 'img',
        'abbr', 'address', 'time', 'details', 'summary',
        'video', 'audio', 'source',
    ]

    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title', 'name', 'id', 'class'],
        'img': ['src', 'alt', 'title', 'width', 'height', 'class'],
        'abbr': ['title'],
        'time': ['datetime'],
        'td': ['colspan', 'rowspan', 'align', 'valign'],
        'th': ['colspan', 'rowspan', 'align', 'valign', 'scope'],
        'col': ['span', 'width'],
        'colgroup': ['span', 'width'],
        'table': ['border', 'cellpadding', 'cellspacing', 'width'],
        'video': ['controls', 'width', 'height', 'poster'],
        'source': ['src', 'type'],
        'audio': ['controls', 'src'],
        # generic attributes allowed on most tags
        '*': ['id', 'class', 'title', 'style'],
    }
    # fmt: on

    DANGEROUS_PROTOCOLS = [
        'javascript:',
        'data:',
        'vbscript:',
        'file:',
        'about:',
    ]

    # extend with custom user-defined tags and attributes
    if custom_tags:
        for tag_name in custom_tags:
            if tag_name and tag_name not in ALLOWED_TAGS:
                ALLOWED_TAGS.append(tag_name)

    if custom_attributes:
        for tag_name, attrs in custom_attributes.items():
            if tag_name in ALLOWED_ATTRIBUTES:
                ALLOWED_ATTRIBUTES[tag_name] = (
                    ALLOWED_ATTRIBUTES[tag_name] + attrs
                )
            else:
                ALLOWED_ATTRIBUTES[tag_name] = attrs

    soup = BeautifulSoup(html, 'html.parser')
    _escape = False

    for element in soup:
        if not hasattr(element, 'name') or element.name is None:
            continue

        if element.name.lower() not in ALLOWED_TAGS:
            _escape = True
            break

        if hasattr(element, 'attrs'):
            tag_name_lower = element.name.lower()
            allowed_attrs = ALLOWED_ATTRIBUTES.get(
                tag_name_lower, []
            ) + ALLOWED_ATTRIBUTES.get('*', [])

            for attr_name, attr_value in list(element.attrs.items()):
                attr_name_lower = attr_name.lower()

                if attr_name_lower not in allowed_attrs:
                    _escape = True
                    break

                if attr_name_lower in ['href', 'src', 'poster']:
                    if isinstance(attr_value, str):
                        attr_lower = attr_value.lower().strip()
                        for protocol in DANGEROUS_PROTOCOLS:
                            if attr_lower.startswith(protocol):
                                _escape = True
                                break

                if _escape:
                    break

        if _escape:
            break

    if _escape:
        # take no prisoners
        html = escape(html)

    return html


class OtterwikiMdRenderer(mistune.HTMLRenderer):
    toc_count = 0
    toc_tree = []
    toc_anchors = {}

    def __init__(self, env, custom_allowlist=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.env = env
        self.custom_tags, self.custom_attributes = parse_custom_allowlist(
            custom_allowlist
        )

    def inline_html(self, html):
        return clean_html(
            html,
            custom_tags=self.custom_tags,
            custom_attributes=self.custom_attributes,
        )

    def block_html(self, html):
        return clean_html(
            html,
            custom_tags=self.custom_tags,
            custom_attributes=self.custom_attributes,
        )

    def reset_toc(self):
        self.toc_count = 0
        self.toc_tree = []
        self.toc_anchors = {}

    def image(self, src, alt="", title=None):
        # escape src, title and alt
        if title:
            title = mistune.escape(title)
        alt = mistune.escape(alt)
        src = mistune.escape_url(self._safe_url(src))

        if not empty(title):
            image_html = (
                '<img src="{}" class="img-fluid" title="{}" alt="{}">'.format(
                    src, title, alt
                )
            )
        else:
            image_html = '<img src="{}" class="img-fluid" alt="{}">'.format(
                src, alt
            )

        processed_html = chain_hooks(
            "renderer_process_image",
            image_html,
            src,
            alt,
            title,
            self.env.get('page'),
        )
        return processed_html

    def link(self, link, text=None, title=None):
        if empty(text):
            text = link
        # escape link, title
        link = mistune.escape_url(self._safe_url(link))

        if title:
            link_html = '<a href="{}" title="{}">{}</a>'.format(
                link, mistune.escape(title), text
            )
        else:
            link_html = '<a href="{}">{}</a>'.format(link, text)

        processed_html = chain_hooks(
            "renderer_process_link",
            link_html,
            link,
            text,
            title,
            self.env.get('page'),
        )
        return processed_html

    def codespan(self, text):
        if text.startswith("$") and text.endswith("$"):
            # mark that MathJax is required
            if hasattr(self, 'renderer'):
                self.renderer.requires_mathjax = True
            return "\\(" + mistune.escape(text[1:-1]) + "\\)"
        return "<code>" + mistune.escape(text) + "</code>"

    def block_code(self, code, info=None):
        prefix = ""
        linenumbers = False
        if not info or not len(info):
            html = (
                '\n'
                + _pre_copy_to_clipboard_tag()
                + '{}</pre></div>\n'.format(mistune.escape(code))
            )
            return html
        if cursormagicword in info:
            info = info.replace(cursormagicword, "")
            prefix = cursormagicword
        if info[-1] == "=":
            info = info[:-1]
            linenumbers = True
        cursorline, code = hidemagicword(code)
        if info == "math":
            # mark that MathJax is required
            if hasattr(self, 'renderer'):
                self.renderer.requires_mathjax = True
            html = "".join(
                ["\\[{}\\]".format(line) for line in code.strip().splitlines()]
            )
        elif info == "mermaid":
            # mark that Mermaid is required
            if hasattr(self, 'renderer'):
                self.renderer.requires_mermaid = True
            html = "".join(
                ["\\[{}\\]".format(line) for line in code.strip().splitlines()]
            )
            # replace \n with <br/> for convenient diagram writing (and match the github syntax)
            code = code.replace("\\n", "<br/>")
            html = '\n<pre class="mermaid">{}\n</pre>\n'.format(code.strip())
            return html
        else:
            html = prefix + pygments_render(
                code, info, linenumbers=linenumbers
            )
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

        processed_html = chain_hooks(
            "renderer_process_heading",
            rv,
            text,
            level,
            anchor,
            self.env.get('page'),
        )

        self.toc_tree.append((self.toc_count, text, level, raw, anchor))
        self.toc_count += 1
        return processed_html


class OtterwikiBlockParser(mistune.BlockParser):
    INDENT_CODE = re.compile(r'((?:\n*)(?:(?: {4}| *\t)[^\n]+\n*)+)\n')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse_indent_code(self, m, state):
        """
        Overrides mistunes rendering, since mistune catches one \n too much
        """
        raw = m.group(1)
        text = mistune.block_parser.expand_leading_tab(raw)
        code = mistune.block_parser._INDENT_CODE_TRIM.sub(  # pyright: ignore
            '', text
        )
        code = code.lstrip('\n')
        return self.tokenize_block_code(code, None, state)


class OtterwikiInlineParser(mistune.InlineParser):
    def __init__(self, env, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.env = env

    def parse_codespan(self, m, state):
        # mistune replaces multiple spaces and newlines with " "
        # and removes leading and trailing whitespace
        #    re.sub(r'[ \n]+', ' ', m.group(2).strip())

        code = re.sub(r'\n+', ' ', m.group(2))
        return 'codespan', code

    def parse_std_link(self, m, state):
        line = m.group(0)
        text = m.group(1)
        link = mistune.inline_parser.ESCAPE_CHAR.sub(r'\1', m.group(2))
        if link.startswith('<') and link.endswith('>'):
            link = link[1:-1]
        elif link.startswith("./"):
            if self.env.get("PAGE_URL", None) is not None:
                link = self.env["PAGE_URL"] + "/" + link

        title = m.group(3)
        if title:
            title = mistune.inline_parser.ESCAPE_CHAR.sub(r'\1', title[1:-1])

        if line[0] == '!':
            return 'image', mistune.escape_url(link), text, title

        return self.tokenize_link(line, link, text, title, state)


class OtterwikiMdParser(mistune.Markdown):
    def __init__(
        self, renderer, block=None, inline=None, plugins=None, env={}
    ):
        self.env = env
        super().__init__(
            renderer=renderer, block=block, inline=inline, plugins=plugins
        )


class OtterwikiRenderer:
    def __init__(self, config={}):
        self.env = {
            "config": config,
        }
        self.requires_mermaid = False
        self.requires_mathjax = False
        self.requires_datatables = True

        custom_allowlist = (
            config.get('RENDERER_HTML_ALLOWLIST', '').strip() or None
        )
        self.md_renderer = OtterwikiMdRenderer(
            env=self.env, custom_allowlist=custom_allowlist
        )

        # set reference to renderer in md_renderer for library requirement tracking
        self.md_renderer.renderer = self
        self.inline_parser = OtterwikiInlineParser(
            env=self.env, renderer=self.md_renderer, hard_wrap=False
        )
        self.block_parser = OtterwikiBlockParser()

        self.mistune = OtterwikiMdParser(
            renderer=self.md_renderer,
            inline=self.inline_parser,
            block=self.block_parser,
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
                plugin_frontmatter,
                plugin_frontmatter_title,
                plugin_abbr,
            ],
            env=self.env,
        )
        self.lastword = re.compile(r"([a-zA-Z\-0-9\.]+)$")
        self.htmlcursor = " <span id=\"otterwiki_cursor\"></span> "
        # thanks to https://github.com/lepture/mistune/issues/158#issuecomment-830481284
        # we can enable tables in lists
        self.mistune.block.list_rules += ['table', 'nptable']  # pyright:ignore

    def markdown(self, text, cursor=None, **kwargs):
        self.md_renderer.reset_toc()
        self.requires_mermaid = False
        self.requires_mathjax = False
        # do the preparsing
        text = chain_hooks("renderer_markdown_preprocess", text)
        # to avoid that preparsing removes the trailing newline and to be
        # able to deal with manually committed files that lack the trailing newline
        # we add one in case it is missing
        if len(text) < 1 or text[-1] != "\n":
            text += "\n"

        # add cursor position
        if cursor is not None:
            text_arr = text.splitlines()
            try:
                line = min(len(text_arr) - 1, int(cursor) + 1)
            except ValueError:
                line = 0
            # find a line to place the cursor
            while line > 0 and (
                not len(self.lastword.findall(text_arr[line])) > 0
                or text_arr[line].startswith(
                    "---"
                )  # --- (hr) needs extra space
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
        for k, v in kwargs.items():
            self.env[k.upper()] = v
        html = self.mistune(text)
        # clean extra kwargs from environment
        for k, v in kwargs.items():
            del self.env[k.upper()]
        # generate the toc
        toc = self.md_renderer.toc_tree.copy()
        if cursor is not None and line > 0:
            # replace the magic word with the cursor span

            # we have to make sure that the cursormagicword is not placed inside an element
            # which might break the html after replacing it with self.htmlcursor

            # find the line with the magic word
            lines = html.splitlines(True)
            for i, line in enumerate(lines):
                if cursormagicword in line:
                    # parse with bs4
                    soup = BeautifulSoup(line, 'html.parser')
                    prepend_cursor = False
                    for element in soup.find_all():
                        for attr_key, attr_value in element.attrs.items():
                            if cursormagicword in attr_value:
                                prepend_cursor = True
                                # remove cursormagicword from attr
                                element.attrs[attr_key] = attr_value.replace(
                                    cursormagicword, ""
                                )
                        if prepend_cursor:
                            element.insert_before(cursormagicword)
                    # only use the bs4 string if it has been used
                    if prepend_cursor:
                        line = str(soup)
                    lines[i] = line.replace(cursormagicword, self.htmlcursor)
                    # dont check other lines, there is only one cursor.
                    break

            html = "".join(lines)
        elif cursor is not None:
            html = self.htmlcursor + html

        html = chain_hooks("renderer_html_postprocess", html)

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

        return (
            html,
            toc,
            {
                'requires_mermaid': self.requires_mermaid,
                'requires_mathjax': self.requires_mathjax,
                'requires_datatables': self.requires_datatables,
            },
        )


# unconfigured renderer for testing and rendering about()
render = OtterwikiRenderer()
