import {
  EditorView,
  keymap,
  lineNumbers,
  drawSelection,
  rectangularSelection,
  highlightSpecialChars,
  highlightActiveLine,
  dropCursor,
} from '@codemirror/view';
import { EditorState } from '@codemirror/state';
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands';
import {
  syntaxHighlighting,
  indentOnInput,
  bracketMatching,
  defaultHighlightStyle,
} from '@codemirror/language';
import { markdown, markdownLanguage, insertNewlineContinueMarkup } from '@codemirror/lang-markdown';
import { search, searchKeymap, openSearchPanel } from '@codemirror/search';
import { closeBrackets, closeBracketsKeymap } from '@codemirror/autocomplete';

import { codeLanguages } from './languages.js';
import { lightTheme, darkTheme, themeCompartment, inlineCodeHighlighter } from './theme.js';
import { setView, getCursor, getValue, posToOffset } from './helpers.js';
import { getState } from './state-detection.js';
import * as formatting from './editor-formatting.js';
import * as tables from './editor-tables.js';
import * as lists from './editor-lists.js';
import * as links from './editor-links.js';
import { attachInlineUpload } from './inline-attachment.js';
import { listDepthHighlighter } from './list-depth.js';

function initEditor() {
  const textarea = document.getElementById('content_editor');
  if (!textarea) {
    return;
  }

  const parent = document.getElementById('editor_block');
  if (!parent) {
    return;
  }

  const isDarkMode =
    document.body.classList.contains('dark-mode')
    || document.documentElement.classList.contains('dark-mode');

  let cleanGeneration = 0;
  let currentGeneration = 0;

  const view = new EditorView({
    doc: textarea.value,
    parent,
    extensions: [
      history(),
      keymap.of([
        { key: 'Enter', run: insertNewlineContinueMarkup },
        { key: 'Mod-s', run: () => true },
        { key: 'Ctrl-s', run: () => true },
        ...defaultKeymap,
        ...historyKeymap,
        ...searchKeymap,
        ...closeBracketsKeymap,
        indentWithTab,
      ]),
      lineNumbers(),
      drawSelection(),
      rectangularSelection(),
      highlightSpecialChars(),
      highlightActiveLine(),
      dropCursor(),
      indentOnInput(),
      bracketMatching(),
      closeBrackets(),
      markdown({ codeLanguages, base: markdownLanguage }),
      syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
      themeCompartment.of(isDarkMode ? darkTheme : lightTheme),
      inlineCodeHighlighter,
      listDepthHighlighter,
      search({ top: false }),
      EditorView.lineWrapping,
      EditorState.tabSize.of(4),
      EditorView.contentAttributes.of({ spellcheck: 'true' }),
      EditorView.updateListener.of((update) => {
        if (!update.docChanged) {
          return;
        }

        currentGeneration += 1;
        const changeEvent = new CustomEvent('cm6change', {
          bubbles: true,
          detail: {
            value: getValue(),
            cursor: getCursor(),
            generation: currentGeneration,
          },
        });
        view.dom.dispatchEvent(changeEvent);
      }),
    ],
  });

  textarea.style.display = 'none';
  setView(view);

  const bottomPanel = document.getElementById('editor-bottom-panel');
  if (bottomPanel) bottomPanel.style.display = 'block';

  const config = window.otterwikiEditorConfig || {};
  const cursorLine = config.cursorLine || 0;
  const cursorCh = config.cursorCh || 0;
  view.dispatch({ selection: { anchor: posToOffset(cursorLine, cursorCh) } });
  view.focus();

  if (config.inlineAttachmentOptions) {
    attachInlineUpload(view, config.inlineAttachmentOptions);
  }

  function markClean() {
    cleanGeneration = currentGeneration;
  }

  function isClean() {
    return cleanGeneration === currentGeneration;
  }

  window.cm_editor = view;
  window.otterwiki_editor = {
    bold: formatting.bold,
    italic: formatting.italic,
    strikethrough: formatting.strikethrough,
    header: formatting.header,
    code: formatting.code,
    codeBlock: formatting.codeBlock,
    hr: formatting.hr,

    table: tables.table,
    table_add_row: tables.table_add_row,
    table_remove_row: tables.table_remove_row,
    table_move_row_up: tables.table_move_row_up,
    table_move_row_down: tables.table_move_row_down,
    table_add_column: tables.table_add_column,
    table_remove_column: tables.table_remove_column,
    table_move_column: tables.table_move_column,
    table_align_col: tables.table_align_col,

    quote: lists.quote,
    ul: lists.ul,
    ol: lists.ol,
    cl: lists.cl,
    spoiler: lists.spoiler,
    expand: lists.expand,
    panelNotice: lists.panelNotice,
    panelWarning: lists.panelWarning,
    panelDanger: lists.panelDanger,
    alertNote: lists.alertNote,
    alertTip: lists.alertTip,
    alertImportant: lists.alertImportant,
    alertWarning: lists.alertWarning,
    alertCaution: lists.alertCaution,
    diagram: lists.diagram,

    link: links.link,
    img: links.img,
    footnote: links.footnote,
    insert_attachment: links.insert_attachment,
    update_attachment_preview: links.update_attachment_preview,
    insert_wikilink: links.insert_wikilink,
    paste_url: links.paste_url,
    on_paste: links.on_paste,
    undo: links.undo,
    redo: links.redo,

    _getState: getState,
    _findWordAt: formatting._findWordAt,
  };

  window.cmOpenSearch = () => openSearchPanel(view);
  window.cmOpenReplace = () => {
    openSearchPanel(view);
    setTimeout(() => {
      const replaceToggle =
        view.dom.querySelector('.cm-search [name="replace"]')
        || view.dom.querySelector('.cm-search button[name="replace"]');
      if (replaceToggle) {
        replaceToggle.click();
      }
    }, 50);
  };
  window.cmMarkClean = markClean;
  window.cmIsClean = isClean;
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initEditor);
} else {
  initEditor();
}
