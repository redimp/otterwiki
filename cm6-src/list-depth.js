import { ViewPlugin, Decoration } from '@codemirror/view';
import { syntaxTree } from '@codemirror/language';
import { RangeSetBuilder } from '@codemirror/state';

const listMarkDecos = [
  Decoration.mark({ class: 'cm-list-1' }),
  Decoration.mark({ class: 'cm-list-2' }),
  Decoration.mark({ class: 'cm-list-3' }),
];

function buildListDecorations(view) {
  const builder = new RangeSetBuilder();
  const tree = syntaxTree(view.state);

  for (const { from, to } of view.visibleRanges) {
    tree.iterate({
      from,
      to,
      enter(node) {
        if (node.name === 'ListItem') {
          let depth = 0;
          let cur = node.node.parent;
          while (cur) {
            if (cur.name === 'BulletList' || cur.name === 'OrderedList') {
              depth++;
            }
            cur = cur.parent;
          }

          // Mark from ListItem start to the first nested list (or end of item)
          let ownEnd = node.to;
          let child = node.node.firstChild;
          while (child) {
            if (child.name === 'BulletList' || child.name === 'OrderedList') {
              ownEnd = child.from;
              break;
            }
            child = child.nextSibling;
          }

          if (depth > 0 && node.from < ownEnd) {
            builder.add(node.from, ownEnd, listMarkDecos[(depth - 1) % 3]);
          }
        }
      },
    });
  }

  return builder.finish();
}

export const listDepthHighlighter = ViewPlugin.fromClass(
  class {
    constructor(view) {
      this.decorations = buildListDecorations(view);
    }

    update(update) {
      if (
        update.docChanged ||
        update.viewportChanged ||
        syntaxTree(update.state) !== syntaxTree(update.startState)
      ) {
        this.decorations = buildListDecorations(update.view);
      }
    }
  },
  { decorations: (v) => v.decorations }
);
