import { tags as t } from '@lezer/highlight';

// Syntax: [[Target]] | [[Target#anchor]] | [[Target|Alias]] | [[Target#anchor|Alias]]
// Mirrors the regex in otterwiki/renderer_plugins.py (mistunePluginWikiLink).
const WIKILINK_RE = /^\[\[([^|\]\n]+?)(#[^|\]\n]*)?(?:(\|)([^\]\n]+))?\]\]/;

const OPEN_BRACKET = 91; // '['

export const WikiLink = {
  defineNodes: [
    { name: 'WikiLink', style: t.link },
    { name: 'WikiLinkMark', style: t.processingInstruction },
    { name: 'WikiLinkTarget', style: t.link },
    { name: 'WikiLinkAnchor', style: t.labelName },
    { name: 'WikiLinkPipe', style: t.punctuation },
    { name: 'WikiLinkAlias', style: t.string },
  ],
  parseInline: [
    {
      name: 'WikiLink',
      before: 'Link',
      parse(cx, next, pos) {
        if (next !== OPEN_BRACKET || cx.char(pos + 1) !== OPEN_BRACKET) {
          return -1;
        }
        const m = WIKILINK_RE.exec(cx.slice(pos, cx.end));
        if (!m) return -1;

        const start = pos;
        const end = pos + m[0].length;
        const children = [];

        children.push(cx.elt('WikiLinkMark', start, start + 2));
        let p = start + 2;

        children.push(cx.elt('WikiLinkTarget', p, p + m[1].length));
        p += m[1].length;

        if (m[2]) {
          children.push(cx.elt('WikiLinkAnchor', p, p + m[2].length));
          p += m[2].length;
        }

        if (m[3]) {
          children.push(cx.elt('WikiLinkPipe', p, p + 1));
          p += 1;
          children.push(cx.elt('WikiLinkAlias', p, p + m[4].length));
          p += m[4].length;
        }

        children.push(cx.elt('WikiLinkMark', end - 2, end));

        return cx.addElement(cx.elt('WikiLink', start, end, children));
      },
    },
  ],
};
