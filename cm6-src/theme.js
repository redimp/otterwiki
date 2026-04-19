import { EditorView } from '@codemirror/view';
import { HighlightStyle, syntaxHighlighting } from '@codemirror/language';
import { Compartment } from '@codemirror/state';
import { tags } from '@lezer/highlight';

export const themeCompartment = new Compartment();

const lightEditorTheme = EditorView.theme({
  '&': {
    height: 'calc(100vh - 8rem)',
    minHeight: 'calc(100vh - 8rem)',
    fontFamily: 'Consolas, Menlo, Monaco, Lucida Console, Liberation Mono, DejaVu Sans Mono, Bitstream Vera Sans Mono, Courier New, monospace, serif',
  },
  '.cm-activeLine': {
    backgroundColor: '#FFFAE3',
  },
  '&.cm-focused .cm-matchingBracket': {
    outline: '1px solid grey',
    color: 'black',
  },
  '.cm-gutters': {
    backgroundColor: 'transparent',
    borderRight: '1px solid #ddd',
  },
  '.cm-list-1': { color: '#a074c4' },
  '.cm-list-2': { color: '#b11' },
  '.cm-list-3': { color: '#000080' },
}, { dark: false });

const lightHighlightStyleDef = HighlightStyle.define([
  { tag: tags.meta, color: '#808000' },
  { tag: tags.number, color: '#0000FF' },
  { tag: tags.heading, fontWeight: 'bold', color: '#000080' },
  { tag: tags.keyword, fontWeight: 'bold', color: '#000080' },
  { tag: tags.atom, fontWeight: 'bold', color: '#000080' },
  { tag: tags.definition(tags.variableName), color: '#000000' },
  { tag: tags.variableName, color: '#730' },
  { tag: tags.special(tags.variableName), color: '#a074c4' },  // variable-2
  { tag: tags.typeName, color: '#b11' },
  { tag: tags.propertyName, color: 'black' },
  { tag: tags.operator, color: 'black' },
  { tag: tags.comment, color: '#808080' },
  { tag: tags.string, color: '#f99b15' },
  { tag: tags.special(tags.string), color: '#008000' },  // string-2
  { tag: tags.modifier, color: '#555' },
  { tag: tags.invalid, color: '#FF0000' },
  { tag: tags.attributeName, color: '#0000FF' },
  { tag: tags.tagName, color: '#000080' },
  { tag: tags.quote, color: '#2b4' },
  { tag: tags.url, color: '#f99b15' },
  { tag: tags.link, color: '#1890ff', textDecoration: 'none' },
  { tag: tags.standard(tags.variableName), color: '#30a' },  // builtin
  { tag: tags.bracket, color: '#cc7' },
]);

const darkEditorTheme = EditorView.theme({
  '&': {
    height: 'calc(100vh - 8rem)',
    minHeight: 'calc(100vh - 8rem)',
    fontFamily: 'Consolas, Menlo, Monaco, Lucida Console, Liberation Mono, DejaVu Sans Mono, Bitstream Vera Sans Mono, Courier New, monospace, serif',
    backgroundColor: '#25282c',
    color: '#d8dee9',
  },
  '.cm-content': {
    caretColor: '#f8f8f0',
  },
  '&.cm-focused .cm-cursor': {
    borderLeftColor: '#f8f8f0',
  },
  '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection': {
    backgroundColor: '#434c5e',
  },
  '.cm-activeLine': {
    backgroundColor: '#3b4252',
  },
  '.cm-gutters': {
    backgroundColor: '#25282c',
    borderRight: '1px solid #4c566a',
    color: '#4c566a',
  },
  '.cm-gutterMarker': {
    color: '#4c566a',
  },
  '.cm-gutterMarker-subtle': {
    color: '#4c566a',
  },
  '.cm-lineNumbers .cm-gutterElement': {
    color: '#4c566a',
  },
  '&.cm-focused .cm-matchingBracket': {
    textDecoration: 'underline',
    color: 'white',
  },
  '.cm-list-1': { color: '#bf616a' },
  '.cm-list-2': { color: '#b48ead' },
  '.cm-list-3': { color: '#81A1C1' },
}, { dark: true });

const darkHighlightStyleDef = HighlightStyle.define([
  { tag: tags.comment, color: '#6BBAFF' },
  { tag: tags.atom, color: '#b48ead' },
  { tag: tags.number, color: '#b48ead' },
  { tag: [tags.propertyName, tags.attributeName], color: '#8FBCBB' },
  { tag: [tags.operator, tags.keyword], color: '#81A1C1' },
  { tag: tags.standard(tags.variableName), color: '#81A1C1' },  // builtin
  { tag: tags.string, color: '#A3BE8C' },
  { tag: tags.variableName, color: '#d8dee9' },
  { tag: tags.special(tags.variableName), color: '#bf616a' },  // variable-2
  { tag: tags.typeName, color: '#d8dee9' },
  { tag: tags.definition(tags.variableName), color: '#8FBCBB' },
  { tag: tags.bracket, color: '#81A1C1' },
  { tag: tags.tagName, color: '#bf616a' },
  { tag: tags.heading, color: '#b48ead' },
  { tag: tags.url, color: '#A3BE8C' },
  { tag: tags.link, color: '#1890ff' },
  { tag: tags.invalid, color: '#f8f8f0', backgroundColor: '#bf616a' },
  { tag: tags.meta, color: '#88C0D0' },
  { tag: tags.modifier, color: '#81A1C1' },
  { tag: tags.quote, color: '#2b4' },
  { tag: tags.special(tags.string), color: '#A3BE8C' },
]);

export const lightTheme = [lightEditorTheme, syntaxHighlighting(lightHighlightStyleDef)];
export const darkTheme = [darkEditorTheme, syntaxHighlighting(darkHighlightStyleDef)];

export function getActiveTheme() {
  return document.body.classList.contains('dark-mode') ? darkTheme : lightTheme;
}
