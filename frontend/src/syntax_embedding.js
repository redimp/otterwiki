import { Decoration, ViewPlugin } from '@codemirror/view';
import { syntaxTree } from '@codemirror/language';

// Syntax: {{Name args...}}
// Name is one or more letters/spaces ([A-Za-z ]+). Embeddings may span
// multiple lines; the closing }} must appear at the end of a line.
// Mirrors EMBEDDING_RE in otterwiki/renderer_plugins.py (mistunePluginEmbeddings).
//
// Implemented as a ViewPlugin (rather than a Lezer block parser) so we can
// require a matching closing }} before applying any decorations. The
// lines inside the embedding are left untouched, so normal markdown
// parsing (lists, links, wikilinks, ...) still highlights their content.
const EMBEDDING_RE = /^[ \t]*\{\{([A-Za-z ]+)[\s\S]*?\}\}[ \t]*$/gm;

const markDeco = Decoration.mark({ class: 'cm-embedding-mark' });
const nameDeco = Decoration.mark({ class: 'cm-embedding-name' });

function collectCodeRanges(view) {
  const ranges = [];
  syntaxTree(view.state).iterate({
    enter(node) {
      if (node.name === 'InlineCode' || node.name === 'FencedCode') {
        ranges.push([node.from, node.to]);
        return false;
      }
    },
  });
  return ranges;
}

function posInRanges(pos, ranges) {
  for (let i = 0; i < ranges.length; i += 1) {
    if (pos >= ranges[i][0] && pos < ranges[i][1]) return true;
  }
  return false;
}

export const embeddingHighlighter = ViewPlugin.fromClass(class {
  constructor(view) {
    this.decorations = this.buildDecorations(view);
  }

  update(update) {
    if (update.docChanged || update.viewportChanged) {
      this.decorations = this.buildDecorations(update.view);
    }
  }

  buildDecorations(view) {
    const marks = [];
    const text = view.state.doc.toString();
    const codeRanges = collectCodeRanges(view);

    EMBEDDING_RE.lastIndex = 0;
    let m;
    while ((m = EMBEDDING_RE.exec(text)) !== null) {
      const matched = m[0];
      const name = m[1];
      const openOffset = matched.indexOf('{{');
      const openFrom = m.index + openOffset;
      const openTo = openFrom + 2;
      const nameFrom = openTo;
      const nameTo = nameFrom + name.length;
      const closeFrom = m.index + matched.lastIndexOf('}}');
      const closeTo = closeFrom + 2;

      if (posInRanges(openFrom, codeRanges)) continue;

      marks.push(markDeco.range(openFrom, openTo));
      marks.push(nameDeco.range(nameFrom, nameTo));
      marks.push(markDeco.range(closeFrom, closeTo));
    }

    return Decoration.set(marks, true);
  }
}, { decorations: v => v.decorations });
