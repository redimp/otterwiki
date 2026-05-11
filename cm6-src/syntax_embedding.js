import { tags as t } from '@lezer/highlight';

// Syntax: {{Name args...}}
// The closing }} must appear at the end of a line. The name is one or more
// letters/spaces ([A-Za-z ]+). Embeddings may span multiple lines.
// Mirrors EMBEDDING_RE in otterwiki/renderer_plugins.py (mistunePluginEmbeddings).
const OPEN_RE = /^([ \t]*)\{\{([A-Za-z ]+)(.*)$/;

function lineEndsWithClose(text) {
  const trimmed = text.replace(/\s+$/, '');
  return trimmed.length >= 2 && trimmed.endsWith('}}');
}

export const Embedding = {
  defineNodes: [
    { name: 'EmbeddingBlock', block: true },
    { name: 'EmbeddingMark', style: t.processingInstruction },
    { name: 'EmbeddingName', style: t.keyword },
  ],
  parseBlock: [
    {
      name: 'EmbeddingBlock',
      before: 'LinkReference',
      parse(cx, line) {
        const m = OPEN_RE.exec(line.text);
        if (!m) return false;

        const indent = m[1].length;
        const name = m[2];
        const rest = m[3];
        const startLineStart = cx.lineStart;
        const openFrom = startLineStart + indent;
        const openTo = openFrom + 2;
        const nameFrom = openTo;
        const nameTo = nameFrom + name.length;

        const children = [
          cx.elt('EmbeddingMark', openFrom, openTo),
          cx.elt('EmbeddingName', nameFrom, nameTo),
        ];

        // Single-line: closing }} on the same line.
        if (lineEndsWithClose(rest)) {
          const closeIdx = line.text.lastIndexOf('}}');
          const closeFrom = startLineStart + closeIdx;
          const closeTo = closeFrom + 2;
          const blockEnd = startLineStart + line.text.length;
          children.push(cx.elt('EmbeddingMark', closeFrom, closeTo));
          cx.addElement(
            cx.elt('EmbeddingBlock', openFrom, blockEnd, children),
          );
          cx.nextLine();
          return true;
        }

        // Multi-line: scan forward until a line ends with }}.
        while (cx.nextLine()) {
          if (lineEndsWithClose(line.text)) {
            const closeIdx = line.text.lastIndexOf('}}');
            const closeFrom = cx.lineStart + closeIdx;
            const closeTo = closeFrom + 2;
            const blockEnd = cx.lineStart + line.text.length;
            children.push(cx.elt('EmbeddingMark', closeFrom, closeTo));
            cx.addElement(
              cx.elt('EmbeddingBlock', openFrom, blockEnd, children),
            );
            cx.nextLine();
            return true;
          }
        }

        // EOF reached without a closing marker. Emit what we have so the
        // opening {{ and name still get highlighted while typing.
        const blockEnd = cx.lineStart + line.text.length;
        cx.addElement(
          cx.elt('EmbeddingBlock', openFrom, blockEnd, children),
        );
        return true;
      },
    },
  ],
};
