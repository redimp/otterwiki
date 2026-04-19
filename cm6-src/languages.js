// CodeMirror 6 Language Modes Registry
// Supports all languages from CM5 Makefile (lines 84-86)

import { LanguageDescription, StreamLanguage } from '@codemirror/language';

// Dedicated language packages
import { javascript } from '@codemirror/lang-javascript';
import { python } from '@codemirror/lang-python';
import { xml } from '@codemirror/lang-xml';
import { markdown } from '@codemirror/lang-markdown';
import { php } from '@codemirror/lang-php';
import { sql } from '@codemirror/lang-sql';
import { go } from '@codemirror/lang-go';
import { rust } from '@codemirror/lang-rust';
import { yaml } from '@codemirror/lang-yaml';
import { html } from '@codemirror/lang-html';
import { css } from '@codemirror/lang-css';
import { json } from '@codemirror/lang-json';

// Legacy StreamLanguage modes
import { shell } from '@codemirror/legacy-modes/mode/shell';
import { c, cpp, java, csharp, scala, kotlin } from '@codemirror/legacy-modes/mode/clike';
import { toml } from '@codemirror/legacy-modes/mode/toml';
import { cmake } from '@codemirror/legacy-modes/mode/cmake';
import { perl } from '@codemirror/legacy-modes/mode/perl';
import { http } from '@codemirror/legacy-modes/mode/http';
import { dockerFile } from '@codemirror/legacy-modes/mode/dockerfile';
import { powerShell } from '@codemirror/legacy-modes/mode/powershell';
import { properties } from '@codemirror/legacy-modes/mode/properties';
import { stex } from '@codemirror/legacy-modes/mode/stex';
import { nginx } from '@codemirror/legacy-modes/mode/nginx';
import { haskell } from '@codemirror/legacy-modes/mode/haskell';
import { lua } from '@codemirror/legacy-modes/mode/lua';
import { jinja2 } from '@codemirror/legacy-modes/mode/jinja2';
import { ruby } from '@codemirror/legacy-modes/mode/ruby';

/**
 * Language registry for CodeMirror 6
 * Covers all languages from CM5 Makefile: shell, clike, xml, python, javascript, markdown, yaml, php, sql, toml, cmake, perl, http, go, rust, dockerfile, powershell, properties, stex, nginx, haskell, lua, jinja2, ruby
 */
export const codeLanguages = [
  LanguageDescription.of({
    name: 'JavaScript',
    alias: ['javascript', 'js'],
    load() { return Promise.resolve(javascript()); }
  }),
  LanguageDescription.of({
    name: 'TypeScript',
    alias: ['typescript', 'ts'],
    load() { return Promise.resolve(javascript({ typescript: true })); }
  }),
  LanguageDescription.of({
    name: 'Python',
    alias: ['python', 'py'],
    load() { return Promise.resolve(python()); }
  }),
  LanguageDescription.of({
    name: 'XML',
    alias: ['xml'],
    load() { return Promise.resolve(xml()); }
  }),
  LanguageDescription.of({
    name: 'HTML',
    alias: ['html'],
    load() { return Promise.resolve(html()); }
  }),
  LanguageDescription.of({
    name: 'CSS',
    alias: ['css'],
    load() { return Promise.resolve(css()); }
  }),
  LanguageDescription.of({
    name: 'JSON',
    alias: ['json'],
    load() { return Promise.resolve(json()); }
  }),
  LanguageDescription.of({
    name: 'Markdown',
    alias: ['markdown', 'md'],
    load() { return Promise.resolve(markdown()); }
  }),
  LanguageDescription.of({
    name: 'YAML',
    alias: ['yaml', 'yml'],
    load() { return Promise.resolve(yaml()); }
  }),
  LanguageDescription.of({
    name: 'PHP',
    alias: ['php'],
    load() { return Promise.resolve(php()); }
  }),
  LanguageDescription.of({
    name: 'SQL',
    alias: ['sql'],
    load() { return Promise.resolve(sql()); }
  }),
  LanguageDescription.of({
    name: 'Go',
    alias: ['go'],
    load() { return Promise.resolve(go()); }
  }),
  LanguageDescription.of({
    name: 'Rust',
    alias: ['rust'],
    load() { return Promise.resolve(rust()); }
  }),
  LanguageDescription.of({
    name: 'Shell',
    alias: ['shell', 'bash', 'sh'],
    load() { return Promise.resolve(StreamLanguage.define(shell)); }
  }),
  LanguageDescription.of({
    name: 'C',
    alias: ['c'],
    load() { return Promise.resolve(StreamLanguage.define(c)); }
  }),
  LanguageDescription.of({
    name: 'C++',
    alias: ['cpp', 'c++'],
    load() { return Promise.resolve(StreamLanguage.define(cpp)); }
  }),
  LanguageDescription.of({
    name: 'Java',
    alias: ['java'],
    load() { return Promise.resolve(StreamLanguage.define(java)); }
  }),
  LanguageDescription.of({
    name: 'C#',
    alias: ['csharp', 'cs'],
    load() { return Promise.resolve(StreamLanguage.define(csharp)); }
  }),
  LanguageDescription.of({
    name: 'Scala',
    alias: ['scala'],
    load() { return Promise.resolve(StreamLanguage.define(scala)); }
  }),
  LanguageDescription.of({
    name: 'Kotlin',
    alias: ['kotlin'],
    load() { return Promise.resolve(StreamLanguage.define(kotlin)); }
  }),
  LanguageDescription.of({
    name: 'TOML',
    alias: ['toml'],
    load() { return Promise.resolve(StreamLanguage.define(toml)); }
  }),
  LanguageDescription.of({
    name: 'CMake',
    alias: ['cmake'],
    load() { return Promise.resolve(StreamLanguage.define(cmake)); }
  }),
  LanguageDescription.of({
    name: 'Perl',
    alias: ['perl'],
    load() { return Promise.resolve(StreamLanguage.define(perl)); }
  }),
  LanguageDescription.of({
    name: 'HTTP',
    alias: ['http'],
    load() { return Promise.resolve(StreamLanguage.define(http)); }
  }),
  LanguageDescription.of({
    name: 'Dockerfile',
    alias: ['dockerfile'],
    load() { return Promise.resolve(StreamLanguage.define(dockerFile)); }
  }),
  LanguageDescription.of({
    name: 'PowerShell',
    alias: ['powershell', 'ps1'],
    load() { return Promise.resolve(StreamLanguage.define(powerShell)); }
  }),
  LanguageDescription.of({
    name: 'Properties',
    alias: ['properties'],
    load() { return Promise.resolve(StreamLanguage.define(properties)); }
  }),
  LanguageDescription.of({
    name: 'LaTeX',
    alias: ['latex', 'tex', 'stex'],
    load() { return Promise.resolve(StreamLanguage.define(stex)); }
  }),
  LanguageDescription.of({
    name: 'Nginx',
    alias: ['nginx'],
    load() { return Promise.resolve(StreamLanguage.define(nginx)); }
  }),
  LanguageDescription.of({
    name: 'Haskell',
    alias: ['haskell'],
    load() { return Promise.resolve(StreamLanguage.define(haskell)); }
  }),
  LanguageDescription.of({
    name: 'Lua',
    alias: ['lua'],
    load() { return Promise.resolve(StreamLanguage.define(lua)); }
  }),
  LanguageDescription.of({
    name: 'Jinja2',
    alias: ['jinja2', 'jinja'],
    load() { return Promise.resolve(StreamLanguage.define(jinja2)); }
  }),
  LanguageDescription.of({
    name: 'Ruby',
    alias: ['ruby', 'rb'],
    load() { return Promise.resolve(StreamLanguage.define(ruby)); }
  })
];

/**
 * Get language support by name (case-insensitive)
 * Supports all aliases defined in codeLanguages
 * @param {string} name - Language name or alias
 * @returns {LanguageSupport|null} Language support or null if not found
 */
export function getLanguage(name) {
  if (!name) return null;

  const lower = name.toLowerCase();

  // Find language by alias
  const desc = codeLanguages.find(d => d.alias.includes(lower));
  return desc ? desc.support : null;
}
