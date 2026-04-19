import {
  getView,
  getLine,
  lineCount,
  getCursor,
  setCursor,
  setSelection,
  getSelection,
  replaceSelection,
  focus,
  somethingSelected,
  undo,
  redo,
} from './helpers.js';
import { getState } from './state-detection.js';
import {
  _findWordAt,
  _setLine,
  _getSelectedLines,
  _setSelectedLines,
} from './editor-formatting.js';

export function img(img = '![]()') {
  if (!getView()) { return; }
  const state = getState();
  if (state.image || state.link) { return; }

  const link = img;
  const text = getSelection();
  replaceSelection(text + link);

  const cursor = getCursor();
  cursor.ch -= 1;
  setCursor(cursor);

  focus();
}

export function link(text = 'description', url = 'https://') {
  if (!getView()) { return; }
  const state = getState();
  if (state.img || state.link || state.url) { return; }

  if (getSelection().length === 0) {
    const word = _findWordAt(getCursor());
    setSelection(word.anchor, word.head);
  }

  if (getSelection().trim().length === 0) {
    replaceSelection('[description](https://)');
  } else {
    const selectedText = getSelection();
    replaceSelection(`[${selectedText}](https://)`);
  }

  const cursor = getCursor();
  cursor.ch -= 1;
  setCursor(cursor);

  focus();

  void text;
  void url;
}

export function footnote() {
  if (!getView()) { return; }

  const startChar = '[^';
  const endChar = ']';

  let selectedLines = _getSelectedLines();
  if (selectedLines.length > 1) {
    _setSelectedLines(selectedLines.slice(selectedLines.length - 1));
    selectedLines = _getSelectedLines();
  }

  let footNoteValue = 'footnote_identifier';
  const selectedText = getSelection();
  const lineContent = getLine(selectedLines[0]);

  let newLine = startChar + footNoteValue + endChar;
  let fnIdentifierStart = startChar.length;
  let fnIdentifierEnd = fnIdentifierStart + footNoteValue.length;

  if (selectedText) {
    const selectedTextStart = lineContent.indexOf(selectedText);
    const selectedTextEnd = selectedTextStart + selectedText.length;

    footNoteValue = selectedText;
    newLine = lineContent.slice(0, selectedTextStart)
      + startChar
      + footNoteValue
      + endChar
      + lineContent.slice(selectedTextEnd);

    fnIdentifierStart = selectedTextStart + startChar.length;
    fnIdentifierEnd = selectedTextEnd + startChar.length;
  } else if (lineContent.length) {
    const cursorPos = getCursor('start');
    newLine = lineContent.slice(0, cursorPos.ch) + newLine + lineContent.slice(cursorPos.ch);

    fnIdentifierStart = cursorPos.ch + startChar.length;
    fnIdentifierEnd = fnIdentifierStart + footNoteValue.length;
  }

  _setLine(selectedLines[0], newLine);

  const lastLine = lineCount() - 1;
  const lastLineContent = getLine(lastLine);
  if (lastLineContent.length === 0) {
    _setLine(lastLine, `${startChar}${footNoteValue}${endChar}: footnote_description`);
  } else {
    const separator = lastLineContent.startsWith(startChar) && lastLineContent.includes(`${endChar}: `)
      ? ''
      : '\n';
    _setLine(lastLine, `${lastLineContent}${separator}\n${startChar}${footNoteValue}${endChar}: footnote_description`);
  }

  setSelection(
    { line: selectedLines[0], ch: fnIdentifierStart },
    { line: selectedLines[0], ch: fnIdentifierEnd },
  );

  focus();
}

export function update_attachment_preview() {
  const element = document.getElementById('attachment-filename');
  if (typeof element === 'undefined' || element == null) { return; }

  const filename = element.value.split('/--/')[0];
  const url = element.value.split('/--/')[1];
  const thumbnail_url = element.value.split('/--/')[2];

  document.getElementById('extranav-preview').innerHTML = '';

  if (thumbnail_url === '') {
    if (document.getElementById('attachment-link').checked !== true) {
      document.getElementById('attachment-link').checked = true;
    }
    document.getElementById('attachment-image').disabled = true;
    document.getElementById('attachment-thumbnail').disabled = true;
  } else {
    const preview_img = document.createElement('img');
    preview_img.setAttribute('src', thumbnail_url);
    preview_img.setAttribute('alt', filename);
    document.getElementById('extranav-preview').appendChild(preview_img);

    document.getElementById('attachment-image').disabled = false;
    document.getElementById('attachment-thumbnail').disabled = false;
  }

  if (typeof toggleThumbnailSizeField === 'function') {
    toggleThumbnailSizeField();
  }

  void url;
}

export function insert_attachment() {
  const element = document.getElementById('attachment-filename');
  if (typeof element === 'undefined' || element == null) { return; }

  const filename = element.value.split('/--/')[0];
  let url = element.value.split('/--/')[1];
  let thumbnail_url = element.value.split('/--/')[2];
  let attachment_type = document.querySelector("input[type='radio'][name=attachment-type]:checked").value;
  if (typeof attachment_type === 'undefined' || attachment_type == null || attachment_type === '') {
    attachment_type = 'link';
  }

  let attachment_absolute = document.getElementById('attachment-absolute').checked;
  if (typeof attachment_absolute === 'undefined' || attachment_absolute == null || attachment_absolute === '') {
    attachment_absolute = false;
  }
  if (!attachment_absolute) {
    url = `./${url.split('/').slice(-1)[0]}`;
    thumbnail_url = `./${thumbnail_url.split('/').slice(-1)[0]}`;
  }

  if (attachment_type === 'thumbnail') {
    const thumbnail_size_element = document.getElementById('thumbnail-size');
    const thumbnail_size = thumbnail_size_element ? thumbnail_size_element.value.trim() : '';
    if (thumbnail_size && thumbnail_size.match(/^\d+$/)) {
      thumbnail_url += `=${thumbnail_size}`;
    }
  }

  if (attachment_type === 'image') {
    img(`![](${url})\n`);
  } else if (attachment_type === 'thumbnail') {
    img(`[![](${thumbnail_url})](${url})\n`);
  } else {
    img(`[${filename}](${url})\n`);
  }
}

export function insert_wikilink(absolute = true) {
  if (!getView()) { return; }
  const state = getState();
  if (state.img || state.link || state.url) { return; }

  const element = document.getElementById('wikilink');
  if (typeof element === 'undefined' || element == null) { return; }

  const page = element.value.split('//')[0];
  if (typeof page === 'undefined' || page == null || page === '') { return; }

  if (getSelection().length === 0) {
    const word = _findWordAt(getCursor());
    setSelection(word.anchor, word.head);
  }

  if (getSelection().trim().length === 0) {
    if (!absolute) {
      const title = page.split('/').at(-1);
      replaceSelection(`[[${title}|${page}]]\n`);
    } else {
      replaceSelection(`[[${page}]]\n`);
    }
  } else {
    const text = getSelection();
    replaceSelection(`[[${text}|${page}]]\n`);
  }

  const cursor = getCursor();
  cursor.ch -= 1;
  setCursor(cursor);

  focus();
}

export function paste_url(url) {
  if (!getView()) { return false; }

  const selected_text = getSelection();
  if (/^https?:\/\//.test(selected_text)) { return false; }

  if (getSelection().length > 0) {
    if (selected_text.includes('\n')) { return false; }

    const state = getState();
    if (state.image || state.link || state.code || state.url) { return false; }

    const link = `[${selected_text}](${url})`;
    replaceSelection(link);
    return true;
  }

  return false;
}

export function on_paste(e) {
  const clipboardData = e.clipboardData;
  let result = false;

  if (typeof clipboardData === 'object') {
    const pastedText = clipboardData.getData('text/plain');
    const trimmedText = pastedText.trimEnd();
    const matched = /^https?:\/\/\S+$/.test(trimmedText);
    if (matched) {
      result = paste_url(trimmedText);
    }
  }

  if (result) {
    e.preventDefault();
  }

  return result;
}

export { undo, redo };

void somethingSelected;
