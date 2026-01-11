#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import re
import yaml

from mistune.inline_parser import LINK_LABEL
from mistune.util import unikey, ESCAPE_TEXT
import urllib.parse
from otterwiki.util import slugify

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
        key = unikey(m.group(1))
        def_footnotes = state.get('def_footnotes')
        if not def_footnotes or key not in def_footnotes:
            return 'text', m.group(0)

        index = state.get('footnote_index', 0)
        index += 1
        state['footnote_index'] = index
        state['footnotes'].append(key)
        # footnote number
        fn = list(state['def_footnotes'].keys()).index(key) + 1
        return 'footnote_ref', key, fn, index

    def parse_def_footnote(self, block, m, state):
        key = unikey(m.group(2))
        if key not in state['def_footnotes']:
            state['def_footnotes'][key] = m.group(3)

    def parse_footnote_item(self, block, k, refs, state):
        def_footnotes = state['def_footnotes']
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
            children = block.parse_text(text, state)
            if not isinstance(children, list):
                children = [children]

        return {
            'type': 'footnote_item',
            'children': children,
            'params': (k, idx, refs),
        }

    def md_footnotes_hook(self, md, result, state):
        footnotes = state.get('footnotes')
        if not footnotes:
            return result

        children = []
        for k in state.get('def_footnotes'):
            refs = [i + 1 for i, j in enumerate(footnotes) if j == k]
            children.append(self.parse_footnote_item(md.block, k, refs, state))

        tokens = [{'type': 'footnotes', 'children': children}]
        output = md.block.render(tokens, md.inline, state)
        return result + output

    def render_html_footnote_ref(self, key, index, fn):
        return f'<sup class="footnote-ref" id="fnref-{fn}"><a href="#fn-{index}">{index}</a></sup>'

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
        r'==(?=[^\s=])(' r'(?:\\=|[^=])*' r'(?:' + ESCAPE_TEXT + r'|[^\s=]))=='
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

    def parse_fancy_block(self, block, m, state):
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
        rules.remove('axt_heading')
        rules.remove('setex_heading')

        # add a trailing newline, so that the children get rendered correctly
        if len(text) < 1 or text[-1] != "\n":
            text += "\n"

        children = block.parse(text, state, rules)
        if not isinstance(children, list):
            children = [children]

        return {
            "type": "fancy_block",
            "params": (family, header),
            "text": text,
            "children": children,
        }

    def render_html_fancy_block(self, text, family, header):
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
        return (
            f'<div class="{cls} mb-20" role="alert">{header}\n{text}</div>\n'
        )

    def __call__(self, md):
        md.block.register_rule(
            'fancy_block', self.FANCY_BLOCK, self.parse_fancy_block
        )

        md.block.rules.append('fancy_block')

        if md.renderer.NAME == "html":
            md.renderer.register("fancy_block", self.render_html_fancy_block)


class mistunePluginSpoiler:
    SPOILER_LEADING = re.compile(r'^ *\>\!', flags=re.MULTILINE)
    SPOILER_BLOCK = re.compile(r'(?: {0,3}>![^\n]*(\n|$))+')

    def parse_spoiler_block(self, block, m, state):
        text = m.group(0)

        # we are searching for the complete bock, so we have to remove
        # the syntax >!
        text = self.SPOILER_LEADING.sub('', text)

        children = block.parse(text, state)
        if not isinstance(children, list):
            children = [children]

        return {
            "type": "spoiler_block",
            "text": text,
            "children": children,
        }

    def render_html_spoiler_block(self, text):
        text = text.strip()
        if text.startswith('<p>'):
            text = text[3:]
        if text.endswith('</p>'):
            text = text[:-4]
        return f'<div class="spoiler">\n  <button class="spoiler-button" onclick="otterwiki.toggle_spoiler(this)"><i class="far fa-eye"></i></button>\n  <p>{text}</p>\n</div>\n\n'

    def __call__(self, md):
        md.block.register_rule(
            'spoiler_block', self.SPOILER_BLOCK, self.parse_spoiler_block
        )

        index = md.block.rules.index('block_quote')
        if index != -1:
            md.block.rules.insert(index, 'spoiler_block')
        else:
            md.block.rules.append('spoiler_block')

        if md.renderer.NAME == "html":
            md.renderer.register(
                "spoiler_block", self.render_html_spoiler_block
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

        children = block.parse(text, state)
        if not isinstance(children, list):
            children = [children]

        return {
            "type": "fold_block",
            "text": text,
            "children": children,
            "params": (header,),
        }

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
        md.block.register_rule(
            'fold_block', self.FOLD_BLOCK, self.parse_fold_block
        )

        index = md.block.rules.index('block_quote')
        if index != -1:
            md.block.rules.insert(index, 'fold_block')
        else:
            md.block.rules.append('fold_block')

        if md.renderer.NAME == "html":
            md.renderer.register("fold_block", self.render_html_fold_block)


class mistunePluginMath:
    MATH_BLOCK = re.compile(r'(\${2})((?:\\.|.)*)\${2}')
    MATH_INLINE_PATTERN = (
        r'\$(?=[^\s\$])('
        r'(?:\\\$|[^\$])*'
        r'(?:' + ESCAPE_TEXT + r'|[^\s\$]))\$'
    )

    def parse_block(self, block, m, state):
        text = m.group(2)
        return {
            "type": "math_block",
            "text": text,
        }

    def render_html_block(self, text):
        return f'''\n\\[{text}\\]\n'''

    def parse_inline(self, inline, m, state):
        text = m.group(1)
        return 'math_inline', text

    def render_html_inline(self, text):
        return '\\(' + text + '\\)'

    def __call__(self, md):
        md.block.register_rule('math_block', self.MATH_BLOCK, self.parse_block)
        md.inline.register_rule(
            'math_inline', self.MATH_INLINE_PATTERN, self.parse_inline
        )

        md.block.rules.append('math_block')
        md.inline.rules.append('math_inline')

        if md.renderer.NAME == "html":
            md.renderer.register("math_block", self.render_html_block)
            md.renderer.register('math_inline', self.render_html_inline)


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
        r'^ *\>(\s*\[!(' + TYPES_WITH_PIPES + r')\])?', flags=re.MULTILINE
    )
    ALERT_BLOCK = re.compile(
        r'(?: {0,3}>\s*\[!('
        + TYPES_WITH_PIPES
        + r')\][^\n]*(?:\n|$))( {0,3}>[^\n]*(?:\n|$))+',
        flags=re.I,
    )

    def parse_alert_block(self, block, m, state):
        text = m.group(0)
        type = m.group(1).upper()

        # we are searching for the complete bock, so we have to remove
        # syntax from the beginning of each line>
        text = self.ALERT_LEADING.sub('', text)

        children = block.parse(text, state)
        if not isinstance(children, list):
            children = [children]

        return {
            "type": "alert_block",
            "text": text,
            "params": (type,),
            "children": children,
        }

    def render_html_alert_block(self, text, type):
        text = text.strip()
        return f'<div class="quote-alert quote-alert-{type.lower()}"><div class="quote-alert-header">{self.TYPE_ICONS[type]} {type.capitalize()}</div><p>{text}</p></div>\n'

    def __call__(self, md):
        md.block.register_rule(
            'alert_block', self.ALERT_BLOCK, self.parse_alert_block
        )

        index = md.block.rules.index('block_quote')
        if index != -1:
            md.block.rules.insert(index, 'alert_block')
        else:
            md.block.rules.append('alert_block')

        if md.renderer.NAME == "html":
            md.renderer.register("alert_block", self.render_html_alert_block)


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

    def parse_wikilink(self, inline, m, state):
        if m.group(4) and len(m.group(4)):
            left, right = m.group(2), m.group(4)
        else:
            left, right = m.group(2), m.group(1)

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
        return "wikilink", inline.render(title, state), link

    def render_html_wikilink(self, text, link):
        return '<a href="' + link + '">' + text + '</a>'

    def before_parse(self, md, s, state):
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

        s = self.WIKI_LINK_RE.sub(replace, s)
        return s, state

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

        md.inline.register_rule(
            'wikilink', self.WIKI_LINK_MOD, self.parse_wikilink
        )

        md.inline.rules.append('wikilink')

        if md.renderer.NAME == 'html':
            md.renderer.register('wikilink', self.render_html_wikilink)


class mistunePluginFrontmatter:
    FRONTMATTER_PATTERN = re.compile(r'^---\n(.*?)\n---', re.DOTALL)

    def parse_frontmatter(self, block, m, state):
        frontmatter = m.group(1)
        try:
            if 'env' not in state:
                state['env'] = {}
            frontmatter_data = yaml.safe_load(frontmatter)
            state['env']['frontmatter'] = frontmatter_data

            # Extract title if it exists
            if (
                isinstance(frontmatter_data, dict)
                and 'title' in frontmatter_data
            ):
                title = frontmatter_data['title']
                if isinstance(title, str) and title.strip():
                    state['env']['frontmatter_title'] = title.strip('"\'')
        except Exception as e:
            if 'env' not in state:
                state['env'] = {}
            state['env']['frontmatter'] = {}
        return {
            'type': 'frontmatter',
            'text': frontmatter,
        }

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
        md.block.register_rule(
            'frontmatter', self.FRONTMATTER_PATTERN, self.parse_frontmatter
        )
        md.block.rules.insert(0, 'frontmatter')  # Ensure it runs early

        if md.renderer.NAME == 'html':
            md.renderer.register('frontmatter', self.render_html_frontmatter)


class mistunePluginFrontmatterTitle:
    """
    This plugin adds an H1 title based on the frontmatter title property.
    It depends on mistunePluginFrontmatter being registered first.

    The H1 will only be added if there isn't already an H1 heading in the markdown.
    This allows users to choose between using frontmatter titles automatically
    or explicitly defining their own H1 headings in the markdown content.
    """

    def before_parse(self, md, s, state):
        # Initialize state if needed
        if 'env' not in state:
            state['env'] = {}
        if 'has_h1_heading' not in state['env']:
            state['env']['has_h1_heading'] = False

        # Check if the document has an H1 header
        # Look for ATX style headers (# Title) with proper regex
        # that accounts for optional spaces at start of line
        h1_pattern = re.compile(r'^\s*#\s+\S.*$', re.MULTILINE)
        if h1_pattern.search(s):
            state['env']['has_h1_heading'] = True

        return s, state

    def after_render(self, md, result, state):
        # Add H1 title if we have frontmatter title and no existing H1
        if state.get('env', {}).get('frontmatter_title') and not state.get(
            'env', {}
        ).get('has_h1_heading', False):
            title = state['env']['frontmatter_title']
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
