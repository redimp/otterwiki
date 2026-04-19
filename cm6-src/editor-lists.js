import { getLine, lineCount, getCursor, setSelection, focus } from './helpers.js';
import {
  _toggleLines,
  _toggleMultilineBlock,
  _toggleLinesMultiLevel,
  _getSelectedLines,
  _setSelectedLines,
  _setLine,
} from './editor-formatting.js';

const MAX_MULTI_LEVELS = 5;

export function _toggleAlert(header, placeholderContent = null) {
  const headerValue = `[!${header.toUpperCase()}]`;
  const headerRegex = /^> \[!(?:NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$/;

  if (placeholderContent !== null && !(placeholderContent instanceof Array)) {
    placeholderContent = [placeholderContent];
  } else if (placeholderContent === null) {
    placeholderContent = [];
  }

  let selectedLines = _getSelectedLines();
  if (selectedLines.length === 0) {
    return;
  }

  const firstLine = getLine(selectedLines[0]);
  let placeholderUsed = false;

  if (selectedLines.length === 1 && firstLine.match(/^$/)) {
    placeholderUsed = true;

    const firstLineNum = selectedLines[0];
    _setLine(firstLineNum, `\n${placeholderContent.join('\n')}`);

    selectedLines = [];
    for (let i = 0; i <= placeholderContent.length; i += 1) {
      selectedLines.push(firstLineNum + i);
    }
    _setSelectedLines(selectedLines);
  }

  if (firstLine.match(headerRegex)) {
    if (firstLine.includes(headerValue)) {
      _setLine(selectedLines[0], '> ');
    } else {
      _setLine(selectedLines[0], firstLine.replace(/\[![A-Z]+]/, headerValue));
      return;
    }
  } else if (!firstLine.match(/^$/)) {
    _setLine(selectedLines[0], `${headerValue}\n${firstLine}`);

    selectedLines.push(selectedLines[selectedLines.length - 1] + 1);
    _setSelectedLines(selectedLines);
  } else {
    _setLine(selectedLines[0], headerValue);
  }

  quote(false);

  if (placeholderUsed) {
    const lastLine = selectedLines[selectedLines.length - 1];
    setSelection(
      { line: lastLine, ch: 2 },
      { line: lastLine, ch: getLine(lastLine).length },
    );
  }
}

export function spoiler() {
  const placeholder = 'Hidden content';
  const selectedLines = _getSelectedLines();
  const firstLine = getLine(selectedLines[0]);
  let placeholderUsed = false;

  if (selectedLines.length === 1 && firstLine.match(/^\s*$/)) {
    _setLine(selectedLines[0], placeholder);
    placeholderUsed = true;
  }

  _toggleLinesMultiLevel('>!');

  if (placeholderUsed) {
    setSelection(
      { line: selectedLines[0], ch: 3 },
      { line: selectedLines[0], ch: 3 + placeholder.length },
    );
  }
}

export function expand() {
  let selectedLines = _getSelectedLines();
  const firstLineNum = selectedLines[0];
  const firstLine = getLine(firstLineNum);

  const headerPlaceholder = 'Summary';
  const contentPlaceholder = 'Folded content';
  let extendSelection = false;
  let placeholderUsed = false;

  let updatedLine = firstLine.replace(/(\s*>\|\s+)?#\s+/, '$1');

  if (updatedLine.length > 0 && updatedLine === firstLine) {
    updatedLine = `# ${firstLine}`;
  } else if (updatedLine.length === 0) {
    placeholderUsed = true;
    updatedLine = `# ${headerPlaceholder}`;

    if (selectedLines.length === 1) {
      updatedLine += `\n${contentPlaceholder}`;
      extendSelection = true;
    }
  }
  _setLine(firstLineNum, updatedLine);

  if (extendSelection) {
    _setSelectedLines([firstLineNum, firstLineNum + 1]);
    selectedLines = _getSelectedLines();
  }

  _toggleLines('>| ', [/\s*>\|\s+/], 'expand');

  if (placeholderUsed && !extendSelection) {
    setSelection(
      { line: firstLineNum, ch: 5 },
      { line: firstLineNum, ch: 5 + headerPlaceholder.length },
    );
  } else if (placeholderUsed && extendSelection) {
    const lastLine = selectedLines[selectedLines.length - 1];
    setSelection(
      { line: lastLine, ch: 3 },
      { line: lastLine, ch: 3 + contentPlaceholder.length },
    );
  }
}

export function quote(multilevel = true) {
  _toggleLinesMultiLevel('>', multilevel ? MAX_MULTI_LEVELS : 1);
}

export function ul() {
  _toggleLines('- ', [/\s*[-+*]\s+/], 'ul');
}

export function ol() {
  _toggleLines('\\d', [/\s*\d+\.\s+/], 'ol');
}

export function cl() {
  _toggleLines('- [ ] ', [/\s*[-+*] \[ \]\s+/], 'ul');
}

export function panelNotice() {
  _toggleMultilineBlock(':::info', /^:::(info|warning|danger)/, ':::', ['# Header', 'Content']);
}

export function panelWarning() {
  _toggleMultilineBlock(':::warning', /^:::(info|warning|danger)/, ':::', ['# Header', 'Content']);
}

export function panelDanger() {
  _toggleMultilineBlock(':::danger', /^:::(info|warning|danger)/, ':::', ['# Header', 'Content']);
}

export function diagram() {
  _toggleMultilineBlock('```mermaid', /^```mermaid/, '```', 'See https://mermaid.js.org/intro/');
}

export function alertNote() {
  _toggleAlert('note', ['Content']);
}

export function alertTip() {
  _toggleAlert('tip', ['Content']);
}

export function alertImportant() {
  _toggleAlert('important', ['Content']);
}

export function alertWarning() {
  _toggleAlert('warning', ['Content']);
}

export function alertCaution() {
  _toggleAlert('caution', ['Content']);
}

void lineCount;
void getCursor;
void focus;
