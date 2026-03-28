#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
This file contains plugins that extend the mistune Markdown renderer.

Specifically, it includes plugins for:

- Alerts: Adds the ability to create highlighted alert messages.
- Embeddings: Allows embedding external plugins providing functionality beyond markdown.
- Fancy Blocks: Allows for creating visually distinct blocks with custom styles (e.g., info, warning).
- Folding: Enables collapsing blocks of text.
- Footnotes: Adds support for creating and displaying footnotes in Markdown.
- Frontmatter: Parses and utilizes frontmatter information (e.g., title, metadata) at the beginning of a document.
- Math: Supports rendering mathematical expressions using LaTeX syntax.
- Spoilers: Provides functionality to hide content behind a button.
- Task Lists: Enables the creation of to-do lists with checkboxes.
- Wiki Links: Handles wiki links.
"""

import re
import string
import yaml
import base64

from mistune.helpers import LINK_LABEL
from mistune.util import unikey
import urllib.parse

# ESCAPE_TEXT was removed from mistune.util in v3; reconstruct it locally
ESCAPE_TEXT = r"\\" + r"[" + re.escape(string.punctuation) + r"]"
from otterwiki.plugins import chain_hooks
from otterwiki.util import slugify, cursormagicword
from otterwiki.plugins import EmbeddingArgs, call_hook

import otterwiki.renderer_embeddings  # pyright: ignore

__all__ = ['plugin_task_lists', 'plugin_footnotes']


def _rm(method):
    """Wrap a plugin instance method for use with md.renderer.register().

    md.renderer.register() calls the function as func(renderer, *args, **kwargs),
    injecting the renderer as first positional argument. Plugin render methods
    use 'self' (the plugin), not the renderer, so we need to drop that first arg.
    """
    return lambda _renderer, *args, **kwargs: method(*args, **kwargs)


class mistunePluginFootnotes:
    """
    mistune footnote plugin

    fixed to match bitnotes like[^bignote]

    [^bignote]: Here's one with multiple paragraphs and code.

        Indent paragraphs to include them in the footnote.

        `{ my code }`

        Add as many paragraphs as you like.
    """

    #: inline footnote syntax looks like::
    #:
    #:    [^key]
    INLINE_FOOTNOTE_PATTERN = r'\[\^(' + LINK_LABEL + r')\]'
    INLINE_FOOTNOTE_RE = re.compile(INLINE_FOOTNOTE_PATTERN)

    #: define a footnote item like::
    #:
    #:    [^key]: paragraph text to describe the note
    DEF_FOOTNOTE = re.compile(
        r'( {0,3})\[\^(' + LINK_LABEL + r')\]:[ \t]*('
        r'[^\n]*\n+'
        r'(?:\1 {1,4}(?! )[^\n]*\n*)*'
        r')'
    )

    def _letter_from_index(self, num):
        """
        1->a, 2->b, 26->z, 27->aa, 28->ab, 54->bb
        """

        num2alphadict = dict(zip(range(1, 27), 'abcdefghijklmnopqrstuvwxyz'))
        outval = ""
        numloops = (num - 1) // 26

        if numloops > 0:
            outval = outval + self._letter_from_index(numloops)

        remainder = num % 26
        if remainder > 0:
            outval = outval + num2alphadict[remainder]
        else:
            outval = outval + "z"
        return outval

    def parse_inline_footnote(self, inline, m, state):
        m2 = self.INLINE_FOOTNOTE_RE.match(m.group(0))
        key = unikey(m2.group(1)) if m2 else None
        def_footnotes = state.env.get('def_footnotes')
        if not def_footnotes or key not in def_footnotes:
            state.append_token({'type': 'text', 'raw': m.group(0)})
            return m.end()

        index = state.env.get('footnote_index', 0)
        index += 1
        state.env['footnote_index'] = index
        state.env.setdefault('footnotes', []).append(key)
        # footnote number
        fn = list(state.env['def_footnotes'].keys()).index(key) + 1
        state.append_token(
            {
                'type': 'footnote_ref',
                'attrs': {'key': key, 'fn': fn, 'index': index},
            }
        )
        return m.end()

    def parse_def_footnote(self, block, m, state):
        m2 = self.DEF_FOOTNOTE.match(m.group(0))
        if not m2:
            return m.end()
        key = unikey(m2.group(2))
        if key not in state.env.get('def_footnotes', {}):
            if 'def_footnotes' not in state.env:
                state.env['def_footnotes'] = {}
            state.env['def_footnotes'][key] = m2.group(3)
        return m.end()

    def parse_footnote_item(self, block, k, refs, state):
        def_footnotes = state.env['def_footnotes']
        text = def_footnotes[k]
        idx = list(def_footnotes.keys()).index(k) + 1
        stripped_text = text.strip()
        if '\n' not in stripped_text:
            children = [{'type': 'paragraph', 'text': stripped_text}]
        else:
            lines = text.splitlines()
            second_line = ""
            for second_line in lines[1:]:
                if second_line:
                    break
            spaces = len(second_line) - len(second_line.lstrip())
            pattern = re.compile(r'^ {' + str(spaces) + r',}', flags=re.M)
            text = pattern.sub('', text)
            child = state.child_state(text)
            block.parse(child)
            children = child.tokens

        return {
            'type': 'footnote_item',
            'children': children,
            'attrs': {'key': k, 'kindex': idx, 'refs': refs},
        }

    def md_footnotes_hook(self, md, result, state):
        from mistune.core import BlockState as _BlockState

        footnotes = state.env.get('footnotes')
        if not footnotes:
            return result

        children = []
        for k in state.env.get('def_footnotes', {}):
            refs = [i + 1 for i, j in enumerate(footnotes) if j == k]
            children.append(self.parse_footnote_item(md.block, k, refs, state))

        child_state = _BlockState(parent=state)
        child_state.tokens = [{'type': 'footnotes', 'children': children}]
        output = md.render_state(child_state)
        return result + output

    def render_html_footnote_ref(self, key, fn, index):
        return f'<sup class="footnote-ref" id="fnref-{index}"><a href="#fn-{fn}">{index}</a></sup>'

    def render_html_footnotes(self, text):
        return (
            '<hr/><section class="footnotes">\n<ol>\n'
            + text
            + '</ol>\n</section>\n'
        )

    def render_html_footnote_item(self, text, key, kindex, refs):
        if len(refs) == 1:
            back = (
                '<a href="#fnref-'
                + str(refs[0])
                + '" class="footnote"><i class="fas fa-long-arrow-alt-up"></i></a> '
            )
        else:
            ref_list = []
            for i, r in enumerate(refs):
                letter = self._letter_from_index(i + 1)
                ref_list.append(
                    f'<a href="#fnref-{r}" class="footnote">{letter}</a>'
                )
            back = (
                '<i class="fas fa-long-arrow-alt-up"></i> '
                + ', '.join(ref_list)
                + ' '
            )

        text = text.rstrip()
        if text.startswith('<p>'):
            text = text[3:]
        if text.endswith('</p>'):
            text = text[:-4]
        text = back + text
        return '<li id="fn-' + str(kindex) + '">' + text + '</li>\n'

    def __call__(self, md):
        md.inline.register(
            'footnote',
            self.INLINE_FOOTNOTE_PATTERN,
            self.parse_inline_footnote,
            before='link',
        )

        md.block.register(
            'def_footnote',
            self.DEF_FOOTNOTE.pattern,
            self.parse_def_footnote,
            before='ref_link',
        )

        if md.renderer.NAME == 'html':
            md.renderer.register(
                'footnote_ref', _rm(self.render_html_footnote_ref)
            )
            md.renderer.register(
                'footnote_item', _rm(self.render_html_footnote_item)
            )
            md.renderer.register('footnotes', _rm(self.render_html_footnotes))

        md.after_render_hooks.append(self.md_footnotes_hook)


class mistunePluginTaskLists:
    """
    Rewrote plugin_task_lists from mistune/plugins/task_lists.py
    """

    TASK_LIST_ITEM = re.compile(r'^(\[[ xX]\])\s+')

    def task_lists_hook(self, md, state):
        self._rewrite_all_list_items(state.tokens)

    def render_ast_task_list_item(self, children, checked):
        return {
            'type': 'task_list_item',
            'children': children,
            'checked': checked,
        }

    def render_html_task_list_item(self, text, checked=False):
        checkbox = '<input class="task-list-item-checkbox" ' 'type="checkbox" '
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
            md.renderer.register(
                'task_list_item', _rm(self.render_html_task_list_item)
            )
        elif md.renderer.NAME == 'ast':
            md.renderer.register(
                'task_list_item', _rm(self.render_ast_task_list_item)
            )

    def _rewrite_all_list_items(self, tokens):
        for tok in tokens:
            if tok['type'] == 'list_item':
                self._rewrite_list_item(tok)
            if 'children' in tok.keys():
                self._rewrite_all_list_items(tok['children'])

    def _rewrite_list_item(self, item):
        children = item['children']
        if children:
            first_child = children[0]
            text = first_child.get('text', '')
            m = self.TASK_LIST_ITEM.match(text)
            if m:
                mark = m.group(1)
                first_child['text'] = text[m.end() :]

                checked = mark != '[ ]'
                item['type'] = 'task_list_item'
                item['attrs'] = {'checked': checked}


class mistunePluginMark:
    #: mark syntax looks like: ``==word==``
    MARK_PATTERN = (
        r'==(?=[^\s=])(' r'(?:\\=|[^=])*' r'(?:' + ESCAPE_TEXT + r'|[^\s=]))=='
    )
    MARK_RE = None  # type: ignore[assignment] # compiled lazily in __call__

    def parse_mark(self, inline, m, state):
        m2 = self.MARK_RE.match(m.group(0))
        new_state = state.copy()
        new_state.src = m2.group(1) if m2 else m.group(0)[2:-2]
        children = inline.render(new_state)
        state.append_token({'type': 'mark', 'children': children})
        return m.end()

    def render_html_mark(self, text):
        return '<mark>' + text + '</mark>'

    def __call__(self, md):
        self.MARK_RE = re.compile(self.MARK_PATTERN)
        md.inline.register(
            'mark', self.MARK_PATTERN, self.parse_mark, before='emphasis'
        )

        if md.renderer.NAME == 'html':
            md.renderer.register('mark', _rm(self.render_html_mark))


class mistunePluginFancyBlocks:
    """
    ::: info
    :::
    """

    FANCY_BLOCK = re.compile(
        r'( {0,3})(\:{3,}|~{3,})([^\:\n]*)\n'
        r'(?:|([\s\S]*?)\n)'
        r'(?: {0,3}\2[~\:]* *\n+|$)'
    )
    FANCY_BLOCK_HEADER = re.compile(r'^#{1,5}\s*(.*)\n+')
    # Scanner pattern without backreference (\2): when combined into the
    # scanner regex, \2 refers to the wrong group and causes catastrophic
    # backtracking. Replace with explicit alternation.
    _FANCY_BLOCK_SCANNER_PATTERN = (
        r'( {0,3})(\:{3,}|~{3,})([^\:\n]*)\n'
        r'(?:|([\s\S]*?)\n)'
        r'(?: {0,3}(?:\:{3,}|~{3,})[~\:]* *\n+|\Z)'
    )

    def parse_fancy_block(self, block, m, state):
        cursor = False
        end_pos = (
            m.end()
        )  # save original scanner match end before re-assigning m
        # check if the cursor was set inside the fancy block (in preview mode)
        if cursormagicword in m.group(0):
            cursor = True
            m = self.FANCY_BLOCK.match(m.group(0).replace(cursormagicword, ""))
            if not m:
                return
        else:
            # Re-match with standalone regex so sub-groups are accessible
            # (in the combined scanner, numbered groups are offset/None)
            m = self.FANCY_BLOCK.match(m.group(0))
            if not m:
                return
        text = m.group(4) or ""
        family = m.group(3).strip().lower()

        # find (and remove) the header from the text block
        header = self.FANCY_BLOCK_HEADER.match(text)
        if header is not None:
            header = header.group(1)
            text = self.FANCY_BLOCK_HEADER.sub('', text, 1)

        # parse the text inside the block, remove headings from the rules
        # -- we don't want them in the toc so these are handled extra
        rules = list(block.rules)
        for r in ('axt_heading', 'setex_heading'):
            if r in rules:
                rules.remove(r)

        # add a trailing newline, so that the children get rendered correctly
        if len(text) < 1 or text[-1] != "\n":
            text += "\n"

        child = state.child_state(text)
        block.parse(child, rules)

        state.append_token(
            {
                "type": "fancy_block",
                "attrs": {
                    "family": family,
                    "header": header,
                    "cursor": cursor,
                },
                "children": child.tokens,
            }
        )
        return end_pos

    def render_html_fancy_block(self, text, family, header, cursor=False):
        if family in ["info", "blue"]:
            cls = "alert alert-primary"
        elif family in ["warning", "yellow"]:
            cls = "alert alert-secondary"
        elif family in ["danger", "red"]:
            cls = "alert alert-danger"
        elif family in ["success", "green"]:
            cls = "alert alert-success"
        elif family in ["none", "empty"]:
            cls = "alert"
        elif family is not None:
            cls = f"alert alert-{family}"
        else:
            cls = "alert"
        if header is not None:
            header = f'<h4 class="alert-heading">{header}</h4>'
        else:
            header = ""
        text = text.strip()
        output = (
            f'<div class="{cls} mb-20" role="alert">{header}\n{text}</div>\n'
        )
        if cursor:
            return cursormagicword + output
        return output

    def __call__(self, md):
        md.block.register(
            'fancy_block',
            self._FANCY_BLOCK_SCANNER_PATTERN,
            self.parse_fancy_block,
        )

        if md.renderer.NAME == "html":
            md.renderer.register(
                "fancy_block", _rm(self.render_html_fancy_block)
            )


class mistunePluginSpoiler:
    SPOILER_LEADING = re.compile(r'^ *\>\!', flags=re.MULTILINE)
    SPOILER_BLOCK = re.compile(r'(?: {0,3}>![^\n]*(\n|$))+')

    def parse_spoiler_block(self, block, m, state):
        text = m.group(0)

        # we are searching for the complete bock, so we have to remove
        # the syntax >!
        text = self.SPOILER_LEADING.sub('', text)

        child = state.child_state(text)
        block.parse(child)

        state.append_token(
            {
                "type": "spoiler_block",
                "children": child.tokens,
            }
        )
        return m.end()

    def render_html_spoiler_block(self, text):
        text = text.strip().replace('\n', ' ')
        if text.startswith('<p>'):
            text = text[3:]
        if text.endswith('</p>'):
            text = text[:-4]
        return f'<div class="spoiler">\n<button class="spoiler-button" onclick="otterwiki.toggle_spoiler(this)"><i class="far fa-eye"></i></button>\n<p>{text}</p>\n</div>\n'

    def __call__(self, md):
        md.block.register(
            'spoiler_block',
            self.SPOILER_BLOCK.pattern,
            self.parse_spoiler_block,
            before='block_quote',
        )

        if md.renderer.NAME == "html":
            md.renderer.register(
                "spoiler_block", _rm(self.render_html_spoiler_block)
            )


class mistunePluginFold:
    FOLD_LEADING = re.compile(r'^ *\>\|', flags=re.MULTILINE)
    FOLD_BLOCK = re.compile(r'(?: {0,3}>\|[^\n]*(\n|$))+')

    FOLD_BLOCK_HEADER = re.compile(r'^#{1,5}\s*(.*)\n+')

    def parse_fold_block(self, block, m, state):
        text = m.group(0)

        # we are searching for the complete bock, so we have to remove
        # the syntax >|
        text = self.FOLD_LEADING.sub('', text).strip()

        # find (and remove) the header from the text block
        header = self.FOLD_BLOCK_HEADER.match(text)
        if header is not None:
            header = header.group(1)
            text = self.FOLD_BLOCK_HEADER.sub('', text, 1)

        # add a trailing newline, so that the children get rendered correctly
        if len(text) < 1 or text[-1] != "\n":
            text += "\n"

        child = state.child_state(text)
        block.parse(child)

        state.append_token(
            {
                "type": "fold_block",
                "children": child.tokens,
                "attrs": {"header": header},
            }
        )
        return m.end()

    def render_html_fold_block(self, text, header=None):
        text = text.strip()
        if text.startswith('<p>'):
            text = text[3:]
        if text.endswith('</p>'):
            text = text[:-4]
        if header is None:
            header = "..."
        return f'''<details class="collapse-panel">
<summary class="collapse-header">
{header}
</summary>
<div class="collapse-content"><p>{text}</p></div></details>'''

    def __call__(self, md):
        md.block.register(
            'fold_block',
            self.FOLD_BLOCK.pattern,
            self.parse_fold_block,
            before='block_quote',
        )

        if md.renderer.NAME == "html":
            md.renderer.register(
                "fold_block", _rm(self.render_html_fold_block)
            )


class mistunePluginMath:
    MATH_BLOCK = re.compile(r'\s*(\${2})((?:\\.|.)*?)\${2}\s*', re.DOTALL)
    # Scanner pattern anchored to line start (^ with re.M) so that $$
    # inside backtick code spans mid-paragraph is not consumed as a
    # block math token.  Uses non-greedy .*? so adjacent blocks stay
    # separate, and inline (?s:...) for DOTALL since the block scanner
    # compiles with re.M only.
    _MATH_BLOCK_SCANNER_PATTERN = r'^\s*(\${2})((?s:(?:\\.|.)*?))\${2}\s*$'
    MATH_INLINE_PATTERN = (
        r'\$(?=[^\s\$])('
        r'(?:\\\$|[^\$])*'
        r'(?:' + ESCAPE_TEXT + r'|[^\s\$]))\$'
    )
    # Inline display math: $$...$$ appearing in inline context (e.g.
    # inside list items) where the block scanner cannot reach.
    MATH_DISPLAY_INLINE_PATTERN = r'\$\$((?:\\\$|[^\$])+)\$\$'
    MATH_DISPLAY_INLINE_RE = None  # type: ignore[assignment] # compiled lazily
    MATH_INLINE_RE = None  # type: ignore[assignment] # compiled lazily in __call__

    def parse_block(self, block, m, state):
        m2 = self.MATH_BLOCK.match(m.group(0))
        text = m2.group(2) if m2 else ""
        state.append_token(
            {
                "type": "math_block",
                "raw": text,
            }
        )
        return m.end()

    def render_html_block(self, text):
        return f'''\n\\[{text}\\]\n'''

    def parse_inline(self, inline, m, state):
        m2 = (
            self.MATH_INLINE_RE.match(m.group(0))
            if self.MATH_INLINE_RE
            else None
        )
        text = m2.group(1) if m2 else m.group(0)[1:-1]
        state.append_token({'type': 'math_inline', 'raw': text})
        return m.end()

    def render_html_inline(self, text):
        return '\\(' + text + '\\)'

    def parse_display_inline(self, inline, m, state):
        m2 = (
            self.MATH_DISPLAY_INLINE_RE.match(m.group(0))
            if self.MATH_DISPLAY_INLINE_RE
            else None
        )
        text = m2.group(1) if m2 else m.group(0)[2:-2]
        state.append_token(
            {
                'type': 'math_display_inline',
                'raw': text,
            }
        )
        return m.end()

    def render_html_display_inline(self, text):
        return '\\[' + text + '\\]'

    def __call__(self, md):
        self.MATH_DISPLAY_INLINE_RE = re.compile(
            self.MATH_DISPLAY_INLINE_PATTERN
        )
        self.MATH_INLINE_RE = re.compile(self.MATH_INLINE_PATTERN)
        md.block.register(
            'math_block', self._MATH_BLOCK_SCANNER_PATTERN, self.parse_block
        )
        # Register display math ($$...$$) before single-$ inline math
        # so that $$ is matched first in the inline alternation.
        md.inline.register(
            'math_display_inline',
            self.MATH_DISPLAY_INLINE_PATTERN,
            self.parse_display_inline,
        )
        md.inline.register(
            'math_inline', self.MATH_INLINE_PATTERN, self.parse_inline
        )

        if md.renderer.NAME == "html":
            md.renderer.register("math_block", _rm(self.render_html_block))
            md.renderer.register(
                'math_display_inline',
                _rm(self.render_html_display_inline),
            )
            md.renderer.register('math_inline', _rm(self.render_html_inline))


class mistunePluginAlerts:
    TYPE_ICONS = {
        'NOTE': '<i class="fas fa-info-circle"></i>',
        'TIP': '<i class="far fa-lightbulb"></i>',
        'IMPORTANT': '<i class="far fa-comment-alt"></i>',
        'WARNING': '<i class="fas fa-exclamation-triangle"></i>',
        'CAUTION': '<i class="fas fa-exclamation-circle"></i>',
    }
    TYPES_WITH_PIPES = "|".join(TYPE_ICONS.keys())
    ALERT_LEADING = re.compile(
        r'^ *\>(\s*\[!(' + TYPES_WITH_PIPES + r')\])?',
        flags=re.MULTILINE + re.I,
    )
    ALERT_BLOCK = re.compile(
        r'(?: {0,3}>\s*\[!('
        + TYPES_WITH_PIPES
        + r')\][^\n]*(?:\n|$))( {0,3}>[^\n]*(?:\n|$))+',
        flags=re.I,
    )
    # Pattern for scanner registration: uses (?i:...) inline flag (no global re.I)
    _ALERT_BLOCK_SCANNER_PATTERN = (
        r'(?: {0,3}>\s*\[!(?i:'
        + TYPES_WITH_PIPES
        + r')\][^\n]*(?:\n|$))(?P<_alert_rest> {0,3}>[^\n]*(?:\n|$))+'
    )

    def parse_alert_block(self, block, m, state):
        text = m.group(0)
        m2 = self.ALERT_BLOCK.match(text)
        type = (m2.group(1) if m2 else "NOTE").upper()

        # we are searching for the complete bock, so we have to remove
        # syntax from the beginning of each line>
        text = self.ALERT_LEADING.sub('', text)

        child = state.child_state(text)
        block.parse(child)

        state.append_token(
            {
                "type": "alert_block",
                "children": child.tokens,
                "attrs": {"type": type},
            }
        )
        return m.end()

    def render_html_alert_block(self, text, type):
        text = text.strip()
        return f'<div class="quote-alert quote-alert-{type.lower()}"><div class="quote-alert-header">{self.TYPE_ICONS[type]} {type.capitalize()}</div>{text}</div>\n'

    def __call__(self, md):
        md.block.register(
            'alert_block',
            self._ALERT_BLOCK_SCANNER_PATTERN,
            self.parse_alert_block,
            before='block_quote',
        )

        if md.renderer.NAME == "html":
            md.renderer.register(
                "alert_block", _rm(self.render_html_alert_block)
            )


class mistunePluginWikiLink:
    """This plugin preprocesses links in the [[WikiLink]] style."""

    PIPE_REPLACEMENT = "\ufeff"

    WIKI_LINK = r"\[\[(([^|\]]+)(?:#[^\]]*)?(?:(\|)([^\]]+))?)\]\]"
    WIKI_LINK_RE = re.compile(WIKI_LINK)
    WIKI_LINK_MOD = (
        r"\[\[(([^"
        + PIPE_REPLACEMENT
        + r"\]]+)(?:#[^\]]*)?(?:("
        + PIPE_REPLACEMENT
        + r")([^\]]+))?)\]\]"
    )
    WIKI_LINK_MOD_RE = re.compile(WIKI_LINK_MOD)

    def __init__(self):
        self.env = {}

    def parse_wikilink(self, inline, m, state):
        # Re-match with standalone regex to access sub-groups
        # (in the combined scanner, unnamed sub-groups shift and return None)
        m2 = self.WIKI_LINK_MOD_RE.match(m.group(0))
        if m2 and m2.group(4) and len(m2.group(4)):
            left, right = m2.group(2), m2.group(4)
        elif m2:
            left, right = m2.group(2), m2.group(1)
        else:
            # fallback: treat entire match as link
            left = right = m.group(0)[2:-2]

        WIKILINK_STYLE = inline.env.get("config", {}).get("WIKILINK_STYLE", "")
        if WIKILINK_STYLE.upper().replace("_", "").strip() in [
            "LINKTITLE",
            "PAGENAMETITLE",
        ]:
            link, title = left, right
        else:
            title, link = left, right

        if not link.startswith(("/", "#")):
            link = f"/{link}"
        # parse link
        link_p = urllib.parse.urlparse(link)
        # slugify the fragment to match the anchors generate by OtterwikiMdRenderer.heading
        if len(link_p.fragment):
            link = link_p._replace(fragment=slugify(link_p.fragment)).geturl()

        # quote link (and just in case someone encoded already: unquote)
        link = urllib.parse.quote(urllib.parse.unquote(link), safe="/#")
        # store env for later use in render
        self.env = inline.env

        new_state = state.copy()
        new_state.src = title
        children = inline.render(new_state)
        state.append_token(
            {
                'type': 'wikilink',
                'children': children,
                'attrs': {'link': link},
            }
        )
        return m.end()

    def before_parse(self, md, state):
        def replace(match):
            if match.group(3) and len(match.group(3)):
                return (
                    "[["
                    + match.group(2)
                    + self.PIPE_REPLACEMENT
                    + match.group(4)
                    + "]]"
                )
            return "[[" + match.group(1) + "]]"

        state.src = self.WIKI_LINK_RE.sub(replace, state.src)

    def after_render(self, md, s, state):
        def replace(match):
            if match.group(3) and len(match.group(3)):
                return "[[" + match.group(2) + "|" + match.group(4) + "]]"
            return "[[" + match.group(2) + "]]"

        s = self.WIKI_LINK_MOD_RE.sub(replace, s)
        return s

    def __call__(self, md):
        md.before_parse_hooks.append(self.before_parse)
        md.after_render_hooks.append(self.after_render)

        md.inline.register(
            'wikilink', self.WIKI_LINK_MOD, self.parse_wikilink, before='link'
        )

        if md.renderer.NAME == 'html':
            plugin = self

            def render_html_wikilink(_renderer, text, link):
                wikilink_html = '<a href="' + link + '">' + text + '</a>'
                processed_html = chain_hooks(
                    "renderer_process_wikilink",
                    wikilink_html,
                    link,
                    text,
                    plugin.env.get('page'),
                )
                return processed_html

            md.renderer.register('wikilink', render_html_wikilink)


class mistunePluginFrontmatter:
    FRONTMATTER_PATTERN = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
    # Pattern for registration with v3's block scanner (re.M only, no DOTALL):
    # - Use \A instead of ^ so frontmatter only matches at the TRUE start of
    #   the document (re.M makes ^ match at every line start, causing false
    #   matches on any --- ... --- separator mid-document)
    # - Use (?s:...) to embed DOTALL so . matches newlines
    _FRONTMATTER_SCANNER_PATTERN = r'\A---\n(?s:(.*?))\n---'

    def parse_frontmatter(self, block, m, state):
        m2 = self.FRONTMATTER_PATTERN.match(m.group(0))
        frontmatter = m2.group(1) if m2 else ""
        try:
            if 'frontmatter' not in state.env:
                frontmatter_data = yaml.safe_load(frontmatter)
                state.env['frontmatter'] = frontmatter_data

                # Extract title if it exists
                if (
                    isinstance(frontmatter_data, dict)
                    and 'title' in frontmatter_data
                ):
                    title = frontmatter_data['title']
                    if isinstance(title, str) and title.strip():
                        state.env['frontmatter_title'] = title.strip('"\'')
        except Exception:
            state.env['frontmatter'] = {}
        state.append_token(
            {
                'type': 'frontmatter',
                'raw': frontmatter,
            }
        )
        return m.end()

    def render_html_frontmatter(self, text):
        text = text.strip()
        return f'''
        <details class="collapse-panel" id="frontmatter">
            <summary class="collapse-header">Properties</summary>
            <div class="collapse-content">
                <pre>{text}</pre>
            </div>
        </details>
        '''

    def __call__(self, md):
        md.block.register(
            'frontmatter',
            self._FRONTMATTER_SCANNER_PATTERN,
            self.parse_frontmatter,
        )
        # Ensure frontmatter runs first
        if 'frontmatter' in md.block.rules:
            md.block.rules.remove('frontmatter')
        md.block.rules.insert(0, 'frontmatter')

        if md.renderer.NAME == 'html':
            md.renderer.register(
                'frontmatter', _rm(self.render_html_frontmatter)
            )


class mistunePluginFrontmatterTitle:
    """
    This plugin adds an H1 title based on the frontmatter title property.
    It depends on mistunePluginFrontmatter being registered first.

    The H1 will only be added if there isn't already an H1 heading in the markdown.
    This allows users to choose between using frontmatter titles automatically
    or explicitly defining their own H1 headings in the markdown content.
    """

    def before_parse(self, md, state):
        # Initialize state if needed
        if 'has_h1_heading' not in state.env:
            state.env['has_h1_heading'] = False

        # Check if the document has an H1 header
        # Look for ATX style headers (# Title) with proper regex
        # that accounts for optional spaces at start of line
        h1_pattern = re.compile(r'^\s*#\s+\S.*$', re.MULTILINE)
        if h1_pattern.search(state.src):
            state.env['has_h1_heading'] = True

    def after_render(self, md, result, state):
        # Add H1 title if we have frontmatter title and no existing H1
        if state.env.get('frontmatter_title') and not state.env.get(
            'has_h1_heading', False
        ):
            title = state.env['frontmatter_title']
            h1_element = f'<h1>{title}</h1>'

            # Insert after frontmatter if present
            if '<details class="collapse-panel" id="frontmatter">' in result:
                result = result.replace(
                    '</details>', '</details>\n' + h1_element, 1
                )
            else:
                # Insert at the beginning if no frontmatter found
                result = h1_element + '\n' + result

        return result

    def __call__(self, md):
        # Register hooks to run before parsing and after rendering
        md.before_parse_hooks.append(self.before_parse)
        md.after_render_hooks.append(self.after_render)


class mistunePluginEmbeddings:
    EMBEDDING_RE = re.compile(
        r"{{([A-Za-z ]+)(.*?)}}$", flags=re.MULTILINE | re.DOTALL
    )
    # Pattern with inline DOTALL for registration with v3's block scanner
    # (which compiles with re.M only, so re.DOTALL flag is lost)
    _EMBEDDING_SCANNER_PATTERN = r"{{(?s:([A-Za-z ]+)(.*?))}}$"

    def parse_block(self, block, m, state):
        cursor = False
        end_pos = (
            m.end()
        )  # save original scanner match end before re-assigning m
        # check if the cursor was set inside the embedding (in preview mode)
        if cursormagicword in m.group(0):
            cursor = True
            m = self.EMBEDDING_RE.match(
                m.group(0).replace(cursormagicword, "")
            )
            if not m:
                return
        else:
            # Re-match with standalone regex so sub-groups are accessible
            m = self.EMBEDDING_RE.match(m.group(0))
            if not m:
                return
        children = []
        # getting the embeddings name
        embedding_name = m.group(1)
        embedding_args = m.group(2)

        # initialize results
        args = EmbeddingArgs()
        children = []

        # check if the embedding is a one liner
        embedding_in_one_line = "\n" not in embedding_args.strip()

        # find all options
        re_option = re.compile(
            r"((?<!\\)\|((?:\\\||\\=|[^=\|\n])+)=((?:\\\||[^\|\n])+)\n?)",
            flags=re.UNICODE,
        )
        match = re_option.search(embedding_args)
        while match is not None:
            # key and value found
            key = match.group(2).replace(r'\=', '=').replace(r'\|', '|')
            value = match.group(3).replace(r'\|', '|')
            # store raw value
            args.options_raw[key.lower()] = value
            # parse options and args out of embedding_block and add them as children
            # this makes it possible to get the markdown parsed that may be used in the options
            opt_child = state.child_state(value)
            block.parse(opt_child)
            # store children
            children.append(
                {
                    "type": "embedding_option",
                    "children": opt_child.tokens,
                    "attrs": {"key": key, "raw_value": value},
                }
            )
            # remove this option from the block
            embedding_args = embedding_args.replace(match.group(0), "")
            # check for more options
            match = re_option.search(embedding_args)
        # strip syntax artefact if one-line syntax is used
        # FIXME: not completely happy with this
        if (
            embedding_in_one_line
            and len(embedding_args)
            and embedding_args[0] == "|"
        ):
            embedding_args = embedding_args[1:]

        # what is left over in embedding_block is what we consider as embedding_args
        # unescape \| in the remaining args
        embedding_args = embedding_args.replace(r'\|', '|')
        args.args_raw = [embedding_args]

        # parse the args, so that all markdown syntax can be used
        args_child = state.child_state(embedding_args)
        block.parse(args_child)

        children.append(
            {
                "type": "embedding_option",
                "children": args_child.tokens,
                "attrs": {
                    "key": None,
                    "raw_value": embedding_args,
                },
            }
        )
        state.append_token(
            {
                "type": "embedding_block",
                "attrs": {
                    "embedding_name": embedding_name,
                    "args": args,
                    "cursor": cursor,
                },
                "children": children,
            }
        )
        return end_pos

    def render_html_block(
        self,
        text: str,
        embedding_name: str,
        args: EmbeddingArgs,
        cursor: bool = False,
    ):
        for argument in text.splitlines():
            parts = argument.rsplit(":", maxsplit=1)
            value = base64.b64decode(parts[-1].encode()).decode()
            if len(parts) == 1:
                args.args.append(value)
            elif len(parts) == 2:
                args.options[parts[0]] = value

        try:
            output = call_hook(
                "embedding_render",
                embedding=embedding_name,
                args=args,
            )
        except Exception as e:
            # render exceptions in the output
            output = f"<p class=\"text-danger\"><tt>{embedding_name}</tt> Error: {e}</p>"

        if output is None:
            # no ouput means either no embedding has been found or nothing was rendered.
            output = f"<p class=\"text-danger\">Unknown Embedding:&nbsp;<tt>{embedding_name}</tt></p>"

        if cursor:
            return cursormagicword + output
        return output

    def render_embedding_option(self, value, key=None, raw_value=None):
        # strip the <p>..</p>\n from the value
        if value.startswith("<p>"):
            value = value[3:]
        if value.endswith("</p>\n"):
            value = value[:-5]
        # encode the value as base64
        value = base64.b64encode(value.encode()).decode()
        if key:
            return f"{key}:{value}\n"
        else:
            return f"{value}\n"

    def __call__(self, md):
        md.block.register(
            'embedding_block',
            self._EMBEDDING_SCANNER_PATTERN,
            self.parse_block,
        )

        md.renderer.register(
            "embedding_option", _rm(self.render_embedding_option)
        )

        if md.renderer.NAME == "html":
            md.renderer.register(
                "embedding_block", _rm(self.render_html_block)
            )


plugin_task_lists = mistunePluginTaskLists()
plugin_footnotes = mistunePluginFootnotes()
plugin_mark = mistunePluginMark()
plugin_fancy_blocks = mistunePluginFancyBlocks()
plugin_spoiler = mistunePluginSpoiler()
plugin_fold = mistunePluginFold()
plugin_math = mistunePluginMath()
plugin_alerts = mistunePluginAlerts()
plugin_wikilink = mistunePluginWikiLink()
plugin_frontmatter = mistunePluginFrontmatter()
plugin_frontmatter_title = mistunePluginFrontmatterTitle()
plugin_embeddings = mistunePluginEmbeddings()
