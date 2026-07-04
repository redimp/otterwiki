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
} from './helpers.js';
import { _getSelectedLines } from './editor-formatting.js';

export function _findBlock(selectBlock = false) {
  let block_start = Number.MAX_SAFE_INTEGER;
  let block_end = Number.MIN_SAFE_INTEGER;
  let block_end_len = 0;

  for (const i of _getSelectedLines()) {
    const line = getLine(i);
    if (line.trim().length > 0) {
      if (block_start > i) block_start = i;
      if (block_end < i) {
        block_end = i;
        block_end_len = line.length;
      }
    } else {
      break;
    }
  }

  if (block_end_len === 0) return false;

  for (let i = block_start; i > 0; i--) {
    const line = getLine(i);
    if (line.trim().length > 0) {
      block_start = i;
    } else {
      break;
    }
  }

  for (let i = block_end; i < lineCount(); i++) {
    const line = getLine(i);
    if (line.trim().length > 0) {
      block_end = i;
      block_end_len = line.length;
    } else {
      break;
    }
  }

  if (selectBlock) {
    setSelection({ line: block_start, ch: 0 }, { line: block_end, ch: block_end_len });
  }

  return [{ line: block_start, ch: 0 }, { line: block_end, ch: block_end_len }];
}

export function _findCursorCell(row, ch) {
  const cells = row.split(/(?<!\\)\|/);
  let c = 0;
  for (const x in cells) {
    c += cells[x].length + 1;
    if (ch < c) return x;
  }
  return cells.length - 1;
}

export function _findTable() {
  const orig_cursor = getCursor('start');
  const orig_cursor_end = getCursor('end');
  const block = _findBlock(true);
  if (!block) return undefined;

  const [block_start] = block;
  let relative_cursor = { line: orig_cursor.line - block_start.line, ch: orig_cursor.ch };
  let text = getSelection();
  const TABLE_RE = /\|(.+)\n *\|( *[-:]+[-| :]*)\n((?: *\|.*(?:\n|$))*)\n{0,1}/;
  const match = text.match(TABLE_RE);

  if (match !== null && (match.index > 0 || match[0].trimEnd().length < text.trimEnd().length)) {
    const text_before = text.substring(0, match.index);
    const line_offset = (text_before.match(/\n/g) || []).length;
    const table_start_line = block_start.line + line_offset;
    const table_lines = match[0].split('\n');
    if (match[0].endsWith('\n')) table_lines.pop();
    const table_end_line = table_start_line + table_lines.length - 1;
    const table_end_ch = table_lines[table_lines.length - 1].length;

    setSelection({ line: table_start_line, ch: 0 }, { line: table_end_line, ch: table_end_ch });
    relative_cursor = { line: orig_cursor.line - table_start_line, ch: orig_cursor.ch };
    text = getSelection();
  }

  if (match == null) {
    setSelection(orig_cursor, orig_cursor_end);
    return undefined;
  }

  let header = match[1].replace(/\| *$/, '');
  let align = match[2].replace(/\| *$/, '');
  let celltext = match[3].replace(/(?: *\| *)?\n$/, '');

  if (relative_cursor.line === 0) relative_cursor.col = _findCursorCell(header, relative_cursor.ch);
  if (relative_cursor.line === 1) relative_cursor.col = _findCursorCell(align, relative_cursor.ch);

  header = header.split(/ *\| */);
  align = align.split(/ *\| */);
  celltext = celltext.split(/\n/);

  const cells = [];
  let n_columns = Math.max(header.length, align.length);

  for (const i in header) {
    header[i] = header[i].trim();
  }

  for (const i in celltext) {
    const row = [];
    let line = celltext[i];

    if (relative_cursor.line - 2 == i) relative_cursor.col = _findCursorCell(line, relative_cursor.ch) - 1;

    line = line.replace(/^ *\| */, '');
    line = line.replace(/ *\|$/, '');
    line = line.split(/(?<!\\)\|/);
    n_columns = Math.max(n_columns, line.length);

    for (const j in line) {
      row.push(line[j].trim());
    }
    cells.push(row);
  }

  for (const i in align) {
    if (align[i].startsWith(':')) {
      if (align[i].endsWith(':')) {
        align[i] = 'center';
      } else {
        align[i] = 'left';
      }
    } else if (align[i].endsWith(':')) {
      align[i] = 'right';
    } else {
      align[i] = 'undef';
    }
  }

  const colum_width = new Array(n_columns).fill(1);
  while (header.length < n_columns) header.push('');
  for (const j in header) colum_width[j] = Math.max(colum_width[j], header[j].length);
  while (align.length < n_columns) align.push('undef');
  for (const i in cells) {
    while (cells[i].length < n_columns) cells[i].push('');
    for (const j in cells[i]) colum_width[j] = Math.max(colum_width[j], cells[i][j].length);
  }

  return {
    header,
    align,
    cells,
    colum_width,
    row: parseInt(relative_cursor.line),
    col: parseInt(relative_cursor.col),
  };
}

export function _alignStr(s = '', l = 0, a = '') {
  if (a === 'right') return s.padStart(l, ' ');
  if (a === 'center') {
    let flip = false;
    while (s.length < l) {
      if (flip) s += ' ';
      else s = ` ${s}`;
      flip = !flip;
    }
    return s;
  }
  return s.padEnd(l, ' ');
}

export function _tableArray(t) {
  const arr = [];
  let row = [];

  for (const j in t.header) {
    row.push(` ${_alignStr(t.header[j], t.colum_width[j], t.align[j])} `);
  }
  arr.push(row);

  row = [];
  for (const j in t.align) {
    if (t.align[j] === 'left') row.push(`:${'-'.repeat(t.colum_width[j])} `);
    else if (t.align[j] === 'right') row.push(` ${'-'.repeat(t.colum_width[j])}:`);
    else if (t.align[j] === 'center') row.push(`:${'-'.repeat(t.colum_width[j])}:`);
    else row.push(` ${'-'.repeat(t.colum_width[j])} `);
  }
  arr.push(row);

  for (const i in t.cells) {
    row = [];
    for (const j in t.cells[i]) {
      row.push(` ${_alignStr(t.cells[i][j], t.colum_width[j], t.align[j])} `);
    }
    arr.push(row);
  }

  return arr;
}

export function table_arr_replace(arr, row = null, col = 0) {
  let text = '';
  for (const i in arr) {
    text += `|${arr[i].join('|')}|\n`;
  }

  replaceSelection(text.trim(), 'around');

  if (row != null) {
    const cursor = getCursor('start');
    cursor.line += row;
    cursor.ch = 2;
    for (let j = 1; j <= col; j++) {
      cursor.ch += arr[0][j - 1].length + 1;
    }
    setCursor(cursor);
  }
}

export function table() {
  if (!getView()) return;

  const t = _findTable();
  if (!t) {
    const text = getSelection();
    const tableText =
      '\n\n| Column 1 | Column 2 | Column 3 |\n| -------- | -------- | -------- |\n| Text     | Text     | Text     |\n\n';
    replaceSelection(text + tableText);
  } else {
    const arr = _tableArray(t);
    table_arr_replace(arr);
  }

  focus();
}

export function table_add_row() {
  if (!getView()) return;
  const t = _findTable();
  if (!t) return;

  const arr = _tableArray(t);
  const empty_row = [];
  for (const j in t.colum_width) {
    empty_row.push(_alignStr('', t.colum_width[j] + 2, t.align[j]));
  }

  const row = Math.max(2, t.row);
  if (row >= arr.length) {
    arr.push(empty_row);
  } else {
    arr.splice(row, 0, empty_row);
  }

  table_arr_replace(arr, Math.max(2, row));
  focus();
}

export function table_remove_row() {
  if (!getView()) return;
  const t = _findTable();
  if (!t) return;
  if (t.row < 2) return;

  const arr = _tableArray(t);
  const row = Math.min(arr.length - 1, Math.max(2, t.row));
  arr.splice(row, 1);

  table_arr_replace(arr, row, t.col);
  focus();
}

export function table_move_row_up() {
  if (!getView()) return;
  const c = getCursor('start');
  const t = _findTable();
  if (!t) return;

  if (t.row < 3) {
    setCursor(c);
  } else {
    const arr = _tableArray(t);
    arr[t.row] = arr.splice(t.row - 1, 1, arr[t.row])[0];
    table_arr_replace(arr, t.row - 1, t.col);
  }

  focus();
}

export function table_move_row_down() {
  if (!getView()) return;
  const t = _findTable();
  if (!t) return;
  if (t.row >= t.cells.length + 1) return;

  const arr = _tableArray(t);
  arr[t.row] = arr.splice(t.row + 1, 1, arr[t.row])[0];
  table_arr_replace(arr, t.row + 1, t.col);
  focus();
}

export function table_add_column() {
  if (!getView()) return;
  const t = _findTable();
  if (!t) return;

  const arr = _tableArray(t);
  for (const i in arr) {
    let cell = '   ';
    if (i == 1) cell = ' - ';
    arr[i].splice(t.col, 0, cell);
  }

  table_arr_replace(arr, t.row, t.col);
  focus();
}

export function table_remove_column() {
  if (!getView()) return;
  const t = _findTable();
  if (!t) return;

  const arr = _tableArray(t);
  for (const i in arr) {
    arr[i].splice(t.col, 1);
  }

  table_arr_replace(arr, t.row, Math.min(arr[0].length - 1, t.col));
  focus();
}

export function table_move_column(offset = 1) {
  if (!getView()) return;
  const c = getCursor('start');
  const t = _findTable();
  if (!t) return;

  const arr = _tableArray(t);
  offset = parseInt(offset);
  if (t.col + offset >= arr[0].length || t.col + offset < 0) {
    setCursor(c);
  } else {
    for (const i in arr) {
      arr[i][t.col] = arr[i].splice(t.col + offset, 1, arr[i][t.col])[0];
    }
    table_arr_replace(arr, t.row, t.col + offset);
  }

  focus();
}

export function table_align_col(align = 'undef') {
  if (!getView()) return;
  const t = _findTable();
  if (!t) return;

  if (t.align[t.col] !== align) t.align[t.col] = align;
  else t.align[t.col] = 'undef';

  const arr = _tableArray(t);
  table_arr_replace(arr, t.row, t.col);
  focus();
}
