import { syntaxTree } from '@codemirror/language';
import { getView } from './helpers.js';

export function getState(offset) {
  const view = getView();
  if (!offset && offset !== 0) {
    offset = view.state.selection.main.head;
  }

  const tree = syntaxTree(view.state);
  const result = {
    bold: false,
    italic: false,
    code: false,
    quote: false,
    strikethrough: false,
    link: false,
    image: false,
    img: false,
    url: false,
    heading: false,
    ol: false,
    ul: false,
  };

  let node = tree.resolveInner(offset, -1);
  while (node) {
    const name = node.name;
    if (name === 'StrongEmphasis') {
      result.bold = true;
    } else if (name === 'Emphasis') {
      result.italic = true;
    } else if (name === 'InlineCode' || name === 'FencedCode' || name === 'CodeBlock') {
      result.code = true;
    } else if (name === 'Blockquote') {
      result.quote = true;
    } else if (name === 'Strikethrough') {
      result.strikethrough = true;
    } else if (name === 'Link') {
      result.link = true;
    } else if (name === 'Image') {
      result.image = true;
      result.img = true;
    } else if (name === 'URL') {
      result.url = true;
    } else if (name.startsWith('ATXHeading') || name.startsWith('SetextHeading')) {
      result.heading = true;
    } else if (name === 'BulletList') {
      result.ul = true;
    } else if (name === 'OrderedList') {
      result.ol = true;
    }
    node = node.parent;
  }

  return result;
}
