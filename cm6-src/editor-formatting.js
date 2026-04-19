import {
  getView,
  getLine,
  lineCount,
  lastLine,
  getCursor,
  setCursor,
  setSelection,
  getSelection,
  replaceSelection,
  replaceRange,
  focus,
  somethingSelected,
} from './helpers.js';
import { getState } from './state-detection.js';

const maxMultiLevels = 5;

export function _setSelectedLines(lines) {
  const last = lines[lines.length - 1];
  const lineLen = getLine(last).length;
  setSelection(
    {
      line: lines[0],
      ch: 0,
    },
    {
      line: last,
      ch: lineLen,
    },
  );
}

export function _getSelectedLines() {
  const start = getCursor('start').line;
  const end = getCursor('end').line;
  const lines = [];
  for (let i = start; i <= end; i++) lines.push(i);
  return lines;
}

export function _setLine(n, text) {
  const lineLen = getLine(n).length;
  replaceRange(text, { line: n, ch: 0 }, { line: n, ch: lineLen });
}

export function _findWordAt(pos) {
  const line = getLine(pos.line);
  let start = pos.ch;
  let end = pos.ch;
  if (line) {
    const check = function(ch) {
      return !(/\s|[,\.!\?]/.test(ch));
    };
    while (start > 0 && check(line.charAt(start - 1))) { --start; }
    while (end < line.length && check(line.charAt(end))) { ++end; }
  }
  return { anchor: { line: pos.line, ch: start }, head: { line: pos.line, ch: end } };
}

export function _toggleBlock(syntax_chars, token) {
  void token;
  if (!(syntax_chars instanceof Array)) {
    syntax_chars = [syntax_chars];
  }
  let anythingSelected = true;
  let toggle_off = false;
  const cursor = getCursor();
  if (getSelection().length == 0) {
    anythingSelected = false;
    const word = _findWordAt(getCursor());
    setSelection(word.anchor, word.head);
  }
  if (getSelection().trim().length == 0) {
    replaceRange(syntax_chars[0] + syntax_chars[0], cursor, cursor);
  } else {
    const cursor_start = getCursor('start');
    const cursor_end = getCursor('end');
    let text = getSelection();
    toggle_off = false;
    for (const chars of syntax_chars) {
      if (text.startsWith(chars) && text.endsWith(chars)) {
        toggle_off = true;
        text = text.slice(chars.length, text.length - chars.length);
        replaceSelection(text);
        cursor_end.ch = cursor_end.ch - chars.length;
        if (cursor_start.line == cursor_end.line) { cursor_end.ch = cursor_end.ch - chars.length; }
        setSelection(cursor_start, cursor_end);
      }
    }
    if (!toggle_off) {
      text = syntax_chars[0] + text + syntax_chars[0];
      replaceSelection(text);
      cursor_end.ch = cursor_end.ch + syntax_chars[0].length;
      if (cursor_start.line == cursor_end.line) { cursor_end.ch = cursor_end.ch + syntax_chars[0].length; }
      setSelection(cursor_start, cursor_end);
    }
  }
  if (!anythingSelected) {
    if (toggle_off) {
      setTimeout(() => {
        cursor.ch -= syntax_chars[0].length;
        setCursor(cursor);
      }, 0);
    } else {
      setTimeout(() => {
        cursor.ch += syntax_chars[0].length;
        setCursor(cursor);
      }, 0);
    }
  }

  focus();
}

export function _toggleMultilineBlock(syntaxStartChars, headerRegex = null, syntaxEndChars = null, placeholderContent = null) {
  if (!(syntaxStartChars instanceof Array)) {
    syntaxStartChars = [syntaxStartChars];
  }
  if (syntaxEndChars !== null && !(syntaxEndChars instanceof Array)) {
    syntaxEndChars = [syntaxEndChars];
  } else {
    syntaxEndChars = syntaxStartChars;
  }

  if (placeholderContent !== null && !(placeholderContent instanceof Array)) {
    placeholderContent = [placeholderContent];
  } else if (placeholderContent === null) {
    placeholderContent = [];
  }

  let selectedLines = _getSelectedLines();
  if (selectedLines.length == 0) return;

  const headerValue = syntaxStartChars[0];
  const tailValue = syntaxEndChars[0];
  let removeBlock = false;
  const firstLine = getLine(selectedLines[0]);

  if (selectedLines.length == 1 && firstLine.match(/^$/)) {
    const placeholderBlock = headerValue + '\n' + placeholderContent.join('\n') + '\n' + tailValue;
    _setLine(selectedLines[0], placeholderBlock);

    const firstLineNum = selectedLines[0];
    selectedLines = [];

    for (let i = 1; i <= placeholderContent.length; i++) {
      selectedLines.push(firstLineNum + i);
    }
    _setSelectedLines(selectedLines);

    focus();
    return;
  }

  if (headerRegex !== null && firstLine.match(headerRegex)) {
    let isHeader = false;
    for (const startChar of syntaxStartChars) {
      if (firstLine.trim() == startChar) {
        isHeader = true;
        break;
      }
    }

    if (isHeader) {
      _setLine(selectedLines[0], '');
      removeBlock = true;
    } else {
      _setLine(selectedLines[0], headerValue);
      focus();
      return;
    }
  } else if (!firstLine.trim().match('^$')) {
    _setLine(selectedLines[0], headerValue + '\n' + firstLine);

    selectedLines.push(selectedLines[selectedLines.length - 1] + 1);
    _setSelectedLines(selectedLines);

    selectedLines = _getSelectedLines();
  } else {
    _setLine(selectedLines[0], headerValue);
  }

  if (removeBlock) {
    let endFound = false;
    for (const ln of selectedLines.splice(1)) {
      const lineValue = getLine(ln);

      for (const endChar of syntaxEndChars) {
        if (lineValue.trim() == endChar) {
          _setLine(ln, '');
          endFound = true;
          break;
        }
      }

      if (endFound) break;
    }

    if (!endFound) {
      let blockEndLine = -1;
      for (const endChar of syntaxEndChars) {
        blockEndLine = _findNextOccurenceLine(endChar);

        if (blockEndLine !== -1) {
          break;
        }
      }

      if (blockEndLine !== -1) {
        _setLine(blockEndLine, '');
      } else {
        console.log('ERROR: No block end found! Remove manually.');
      }
    }
  } else {
    const lastLineNum = selectedLines[selectedLines.length - 1];
    const lastLineValue = getLine(lastLineNum);
    let prefix = '';
    if (!lastLineValue.trim().match(/^$/)) {
      prefix = lastLineValue + '\n';

      selectedLines.push(selectedLines[selectedLines.length - 1] + 1);
    }
    _setLine(lastLineNum, prefix + tailValue);

    _setSelectedLines(selectedLines);
  }

  focus();
}

export function _toggleLines(line_prefix, line_re, token) {
  void token;
  if (!(line_re instanceof Array)) {
    line_re = [line_re];
  }
  const linenumbers = _getSelectedLines();
  let count = 1;
  for (const ln of linenumbers) {
    const line = getLine(ln);
    for (const re of line_re) {
      let updated_line = line.replace(re, '');
      if (updated_line == line) {
        if (line_prefix == '\\d') {
          updated_line = count + '. ' + line;
        } else {
          updated_line = line_prefix + line;
        }
      }
      _setLine(ln, updated_line);
    }
    count += 1;
  }
  focus();
}

export function _toggleLinesMultiLevel(indentChar, maxLevel = maxMultiLevels) {
  if (!getView()) { return; }
  for (const i of _getSelectedLines()) {
    const line = getLine(i);
    let lineHLevel = line.search('[^' + indentChar + ']');
    if (lineHLevel < 0) { lineHLevel = line.length; }
    if (lineHLevel == 0) {
      _setLine(i, indentChar + ' ' + line);
    } else if (lineHLevel / indentChar.length < maxLevel) {
      _setLine(i, indentChar + line);
    } else {
      _setLine(i, line.replace(new RegExp('^(?:' + indentChar + ')+\\s*'), ''));
    }
  }
  focus();
}

export function header() {
  _toggleLinesMultiLevel('#');
}

export function bold() {
  _toggleBlock(['**', '__'], 'bold');
}

export function italic() {
  _toggleBlock(['_', '*'], 'italic');
}

export function strikethrough() {
  _toggleBlock('~~', 'strikethrough');
}

export function code() {
  _toggleBlock(['`', '```'], 'code');
}

export function codeBlock() {
  _toggleMultilineBlock('```', /^```\w*/, null, 'code');
}

export function hr() {
  const linenumbers = _getSelectedLines();
  let changed = false;
  let line = '';
  let ln = 0;
  for (ln of linenumbers) {
    line = getLine(ln);
    const updated_line = line.replace(/^---\w*/, '');
    if (updated_line != line) {
      changed = true;
      _setLine(ln, updated_line);
    }
  }
  if (!changed) {
    const cursor = getCursor('start');
    let line_insert = '---';
    let hr_ln = ln;
    if (getLine(ln) != '') {
      hr_ln += 2;
      line_insert = line + '\n\n' + line_insert;
    }
    if (lastLine() < ln + 1 || getLine(ln + 1) != '') {
      line_insert = line_insert + '\n';
    }
    _setLine(ln, line_insert);
    cursor.line = Math.min(hr_ln, lastLine());
    cursor.ch = 3;
    setCursor(cursor);
  }
  focus();
}

export function _findNextOccurenceLine(lineContent) {
  const selectedLines = _getSelectedLines();
  const lineAfterSelection = selectedLines[selectedLines.length - 1];
  const editorLastLine = lineCount();

  for (let l = lineAfterSelection; l < editorLastLine; l++) {
    if (getLine(l) == lineContent) {
      return l;
    }
  }
  return -1;
}

void getState;
void somethingSelected;
