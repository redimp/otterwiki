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
    const currentVal = this.view.state.doc.toString();
    const from = this.lastValue ? currentVal.indexOf(this.lastValue) : -1;

    if (from !== -1 && this.lastValue) {
      this.view.dispatch({
        changes: {
          from,
          to: from + this.lastValue.length,
          insert: val,
        },
      });
      return;
    }

    this.view.dispatch({
      changes: {
        from: 0,
        to: this.view.state.doc.length,
        insert: val,
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
