import { undo as cmUndo, redo as cmRedo } from '@codemirror/commands';

let _view = null;

export function setView(v) {
  _view = v;
}

export function getView() {
  return _view;
}

export function getLine(n) {
  return _view.state.doc.line(n + 1).text;
}

export function lineCount() {
  return _view.state.doc.lines;
}

export function lastLine() {
  return _view.state.doc.lines - 1;
}

export function getCursor(which = 'head') {
  const sel = _view.state.selection.main;
  let offset = sel.head;

  if (which === 'start') {
    offset = sel.from;
  } else if (which === 'end') {
    offset = sel.to;
  }

  const lineAt = _view.state.doc.lineAt(offset);
  return {
    line: lineAt.number - 1,
    ch: offset - lineAt.from,
  };
}

export function posToOffset(line, ch) {
  return _view.state.doc.line(line + 1).from + ch;
}

export function setCursor(pos) {
  _view.dispatch({ selection: { anchor: posToOffset(pos.line, pos.ch) } });
}

export function setSelection(anchor, head) {
  _view.dispatch({
    selection: {
      anchor: posToOffset(anchor.line, anchor.ch),
      head: posToOffset(head.line, head.ch),
    },
  });
}

export function getSelection() {
  const sel = _view.state.selection.main;
  return _view.state.sliceDoc(sel.from, sel.to);
}

export function replaceSelection(text, select) {
  if (select === 'around') {
    const { from } = _view.state.selection.main;
    _view.dispatch(_view.state.replaceSelection(text));
    _view.dispatch({ selection: { anchor: from, head: from + text.length } });
    return;
  }

  _view.dispatch(_view.state.replaceSelection(text));
}

export function replaceRange(text, from, to) {
  _view.dispatch({
    changes: {
      from: posToOffset(from.line, from.ch),
      to: posToOffset(to.line, to.ch),
      insert: text,
    },
  });
}

export function getValue() {
  return _view.state.doc.toString();
}

export function setValue(text) {
  _view.dispatch({
    changes: {
      from: 0,
      to: _view.state.doc.length,
      insert: text,
    },
  });
}

export function focus() {
  _view.focus();
}

export function somethingSelected() {
  return !_view.state.selection.main.empty;
}

export function hasFocus() {
  return _view.hasFocus;
}

export function getDom() {
  return _view.dom;
}

export function undo() {
  cmUndo(_view);
}

export function redo() {
  cmRedo(_view);
}
