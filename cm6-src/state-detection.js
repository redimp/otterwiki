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
    linkHref: null,
    linkText: null,
    linkTitle: null,
  };

  let node = tree.resolveInner(offset, -1);
  let linkNode = null;
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
      linkNode = node;
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

  // Extract link properties if cursor is in a link
  if (linkNode) {
    let child = linkNode.firstChild;
    while (child) {
      if (child.name === 'LinkText') {
        const linkTextStart = child.from;
        const linkTextEnd = child.to;
        result.linkText = view.state.doc.sliceString(linkTextStart, linkTextEnd);
      } else if (child.name === 'URL') {
        const urlStart = child.from;
        const urlEnd = child.to;
        result.linkHref = view.state.doc.sliceString(urlStart, urlEnd);
      }
      child = child.nextSibling;
    }
  }

  return result;
}
