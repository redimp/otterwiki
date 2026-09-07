import { EditorSelection } from '@codemirror/state';
import { indentUnit } from '@codemirror/language';
import { indentMore, indentLess } from '@codemirror/commands';

// Custom Tab behaviour for the editor.
//
// CodeMirror's default `indentMore` (bound via `indentWithTab`) inserts the
// indent unit at the start of *every* line touched by the selection, including
// completely empty lines. Indenting a multi-line block therefore fills blank
// lines with trailing whitespace (4 spaces), which is both undesirable and, for
// indented code blocks, semantically meaningful (see #566).
//
// `indentBlock` keeps the default behaviour for bare cursors (so pressing Tab
// on an empty line still indents it to start typing), but when a non-empty
// selection is indented it skips empty lines, mirroring how most editors handle
// block indentation.
export function indentBlock({ state, dispatch }) {
  if (state.readOnly) {
    return false;
  }
  // Only bare cursors: fall back to the default, which indents the current
  // line(s) and allows indenting an empty line to start typing.
  if (state.selection.ranges.every((range) => range.empty)) {
    return indentMore({ state, dispatch });
  }
  const indent = state.facet(indentUnit);
  let lastLine = -1;
  const transaction = state.changeByRange((range) => {
    const changes = [];
    for (let pos = range.from; pos <= range.to; ) {
      const line = state.doc.lineAt(pos);
      // `range.to > line.from` excludes a line the selection only touches at
      // its very start, matching CodeMirror's changeBySelectedLine.
      if (line.number > lastLine && range.to > line.from) {
        lastLine = line.number;
        if (line.length > 0) {
          changes.push({ from: line.from, insert: indent });
        }
      }
      pos = line.to + 1;
    }
    const changeSet = state.changes(changes);
    return {
      changes,
      range: EditorSelection.range(
        changeSet.mapPos(range.anchor, 1),
        changeSet.mapPos(range.head, 1),
      ),
    };
  });
  dispatch(state.update(transaction, { userEvent: 'input.indent' }));
  return true;
}

// Shift-Tab keeps CodeMirror's default outdent behaviour.
export const indentBlockKeymap = {
  key: 'Tab',
  run: indentBlock,
  shift: indentLess,
};
