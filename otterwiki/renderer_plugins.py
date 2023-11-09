#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai:

import re
from pprint import pprint

from mistune.inline_parser import LINK_LABEL
from mistune.util import unikey, escape_url, ESCAPE_TEXT

__all__ = ['plugin_task_lists', 'plugin_footnotes']


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

    #: define a footnote item like::
    #:
    #:    [^key]: paragraph text to describe the note
    DEF_FOOTNOTE = re.compile(
        r'( {0,3})\[\^(' + LINK_LABEL + r')\]:[ \t]*('
        r'[^\n]*\n+'
        r'(?:\1 {1,4}(?! )[^\n]*\n*)*'
        r')'
    )

    def parse_inline_footnote(self, inline, m, state):
        key = unikey(m.group(1))
        print(f"{inline=} {m=}")
        pprint(state)
        def_footnotes = state.get('def_footnotes')
        if not def_footnotes or key not in def_footnotes:
            return 'text', m.group(0)

        index = state.get('footnote_index', 0)
        index += 1
        state['footnote_index'] = index
        state['footnotes'].append(key)
        return 'footnote_ref', key, index

    def parse_def_footnote(self, block, m, state):
        key = unikey(m.group(2))
        if key not in state['def_footnotes']:
            state['def_footnotes'][key] = m.group(3)

    def parse_footnote_item(self, block, k, i, state):
        def_footnotes = state['def_footnotes']
        text = def_footnotes[k]

        stripped_text = text.strip()
        if '\n' not in stripped_text:
            children = [{'type': 'paragraph', 'text': stripped_text}]
        else:
            lines = text.splitlines()
            for second_line in lines[1:]:
                if second_line:
                    break

            spaces = len(second_line) - len(second_line.lstrip())
            pattern = re.compile(r'^ {' + str(spaces) + r',}', flags=re.M)
            text = pattern.sub('', text)
            children = block.parse_text(text, state)
            if not isinstance(children, list):
                children = [children]

        return {
            'type': 'footnote_item',
            'children': children,
            'params': (k, i),
        }

    def md_footnotes_hook(self, md, result, state):
        footnotes = state.get('footnotes')
        pprint(footnotes)
        if not footnotes:
            return result

        children = [
            self.parse_footnote_item(md.block, k, i + 1, state)
            for i, k in enumerate(footnotes)
        ]
        tokens = [{'type': 'footnotes', 'children': children}]
        output = md.block.render(tokens, md.inline, state)
        return result + output

    def render_html_footnote_ref(self, key, index):
        i = str(index)
        html = '<sup class="footnote-ref" id="fnref-' + i + '">'
        return html + '<a href="#fn-' + i + '">' + i + '</a></sup>'

    def render_html_footnotes(self, text):
        return (
            '<hr/><section class="footnotes">\n<ol>\n'
            + text
            + '</ol>\n</section>\n'
        )

    def render_html_footnote_item(self, text, key, index):
        i = str(index)
        back = (
            '<a href="#fnref-'
            + i
            + '" class="footnote"><i class="fas fa-long-arrow-alt-up"></i></a> '
        )

        text = text.rstrip()
        if text.startswith('<p>'):
            text = '<p>' + back + text[3:]
        else:
            text = back + text
        return '<li id="fn-' + i + '">' + text + '</li>\n'

    def __call__(self, md):
        md.inline.register_rule(
            'footnote',
            self.INLINE_FOOTNOTE_PATTERN,
            self.parse_inline_footnote,
        )
        index = md.inline.rules.index('std_link')
        if index != -1:
            md.inline.rules.insert(index, 'footnote')
        else:
            md.inline.rules.append('footnote')

        md.block.register_rule(
            'def_footnote', self.DEF_FOOTNOTE, self.parse_def_footnote
        )
        index = md.block.rules.index('def_link')
        if index != -1:
            md.block.rules.insert(index, 'def_footnote')
        else:
            md.block.rules.append('def_footnote')

        if md.renderer.NAME == 'html':
            md.renderer.register('footnote_ref', self.render_html_footnote_ref)
            md.renderer.register(
                'footnote_item', self.render_html_footnote_item
            )
            md.renderer.register('footnotes', self.render_html_footnotes)

        md.after_render_hooks.append(self.md_footnotes_hook)


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
                'task_list_item', self.render_html_task_list_item
            )
        elif md.renderer.NAME == 'ast':
            md.renderer.register(
                'task_list_item', self.render_ast_task_list_item
            )

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
                first_child['text'] = text[m.end() :]

                params = item['params']
                if mark == '[ ]':
                    params = (params[0], False)
                else:
                    params = (params[0], True)

                item['type'] = 'task_list_item'
                item['params'] = params


class mistunePluginMark:
    #: mark syntax looks like: ``==word==``
    MARK_PATTERN = (
        r'==(?=[^\s~])(' r'(?:\\~|[^~])*' r'(?:' + ESCAPE_TEXT + r'|[^\s~]))=='
    )

    def parse_mark(self, inline, m, state):
        text = m.group(1)
        return 'mark', inline.render(text, state)

    def render_html_mark(self, text):
        return '<mark>' + text + '</mark>'

    def __call__(self, md):
        md.inline.register_rule('mark', self.MARK_PATTERN, self.parse_mark)

        index = md.inline.rules.index('codespan')
        if index != -1:
            md.inline.rules.insert(index + 1, 'mark')
        else:  # pragma: no cover
            md.inline.rules.append('mark')

        if md.renderer.NAME == 'html':
            md.renderer.register('mark', self.render_html_mark)



plugin_task_lists = mistunePluginTaskLists()
plugin_footnotes = mistunePluginFootnotes()
plugin_mark = mistunePluginMark()


