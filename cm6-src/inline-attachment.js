import { EditorView } from '@codemirror/view';

class CodeMirror6Editor {
  constructor(view) {
    this.view = view;
    this.lastValue = '';
  }

  getValue() {
    return this.view.state.doc.toString();
  }

  insertValue(val) {
    this.lastValue = val;
    this.view.dispatch(this.view.state.replaceSelection(val));
  }

  setValue(val) {
    const oldVal = this.view.state.doc.toString();
    if (oldVal === val) return;

    // Compute the minimal diff range so CodeMirror can map the cursor
    // through the transaction naturally — a full-document replace would
    // discard the user's caret position (and any text they typed while
    // the upload was in flight).
    let start = 0;
    const minLen = Math.min(oldVal.length, val.length);
    while (start < minLen && oldVal.charCodeAt(start) === val.charCodeAt(start)) {
      start++;
    }
    let oldEnd = oldVal.length;
    let newEnd = val.length;
    while (
      oldEnd > start &&
      newEnd > start &&
      oldVal.charCodeAt(oldEnd - 1) === val.charCodeAt(newEnd - 1)
    ) {
      oldEnd--;
      newEnd--;
    }

    this.view.dispatch({
      changes: {
        from: start,
        to: oldEnd,
        insert: val.slice(start, newEnd),
      },
    });
  }
}

export function inlineAttachmentExtension(options = {}) {
  return EditorView.domEventHandlers({
    paste(event, view) {
      const InlineAttachmentCtor = globalThis.inlineAttachment;
      if (typeof InlineAttachmentCtor === 'undefined') {
        return false;
      }

      const editor = new CodeMirror6Editor(view);
      const inlineattach = new InlineAttachmentCtor(options, editor);
      inlineattach.onPaste(event);
      return false;
    },
    drop(event, view) {
      const InlineAttachmentCtor = globalThis.inlineAttachment;
      if (typeof InlineAttachmentCtor === 'undefined') {
        return false;
      }

      const editor = new CodeMirror6Editor(view);
      const inlineattach = new InlineAttachmentCtor(options, editor);
      if (inlineattach.onDrop(event)) {
        event.stopPropagation();
        event.preventDefault();
        return true;
      }
      return false;
    },
  });
}

export function attachInlineUpload(view, options = {}) {
  const InlineAttachmentCtor = globalThis.inlineAttachment;
  if (typeof InlineAttachmentCtor === 'undefined') {
    return;
  }

  const editor = new CodeMirror6Editor(view);
  const inlineattach = new InlineAttachmentCtor(options, editor);

  view.contentDOM.addEventListener('paste', (e) => {
    inlineattach.onPaste(e);
  }, false);

  view.contentDOM.addEventListener('drop', (e) => {
    if (inlineattach.onDrop(e)) {
      e.stopPropagation();
      e.preventDefault();
    }
  }, false);
}
