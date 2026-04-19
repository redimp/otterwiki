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
    support: javascript()
  }),
  LanguageDescription.of({
    name: 'TypeScript',
    alias: ['typescript', 'ts'],
    support: javascript({ typescript: true })
  }),
  LanguageDescription.of({
    name: 'Python',
    alias: ['python', 'py'],
    support: python()
  }),
  LanguageDescription.of({
    name: 'XML',
    alias: ['xml'],
    support: xml()
  }),
  LanguageDescription.of({
    name: 'HTML',
    alias: ['html'],
    support: html()
  }),
  LanguageDescription.of({
    name: 'CSS',
    alias: ['css'],
    support: css()
  }),
  LanguageDescription.of({
    name: 'JSON',
    alias: ['json'],
    support: json()
  }),
  LanguageDescription.of({
    name: 'Markdown',
    alias: ['markdown', 'md'],
    support: markdown()
  }),
  LanguageDescription.of({
    name: 'YAML',
    alias: ['yaml', 'yml'],
    support: yaml()
  }),
  LanguageDescription.of({
    name: 'PHP',
    alias: ['php'],
    support: php()
  }),
  LanguageDescription.of({
    name: 'SQL',
    alias: ['sql'],
    support: sql()
  }),
  LanguageDescription.of({
    name: 'Go',
    alias: ['go'],
    support: go()
  }),
  LanguageDescription.of({
    name: 'Rust',
    alias: ['rust'],
    support: rust()
  }),
  LanguageDescription.of({
    name: 'Shell',
    alias: ['shell', 'bash', 'sh'],
    support: StreamLanguage.define(shell)
  }),
  LanguageDescription.of({
    name: 'C',
    alias: ['c'],
    support: StreamLanguage.define(c)
  }),
  LanguageDescription.of({
    name: 'C++',
    alias: ['cpp', 'c++'],
    support: StreamLanguage.define(cpp)
  }),
  LanguageDescription.of({
    name: 'Java',
    alias: ['java'],
    support: StreamLanguage.define(java)
  }),
  LanguageDescription.of({
    name: 'C#',
    alias: ['csharp', 'cs'],
    support: StreamLanguage.define(csharp)
  }),
  LanguageDescription.of({
    name: 'Scala',
    alias: ['scala'],
    support: StreamLanguage.define(scala)
  }),
  LanguageDescription.of({
    name: 'Kotlin',
    alias: ['kotlin'],
    support: StreamLanguage.define(kotlin)
  }),
  LanguageDescription.of({
    name: 'TOML',
    alias: ['toml'],
    support: StreamLanguage.define(toml)
  }),
  LanguageDescription.of({
    name: 'CMake',
    alias: ['cmake'],
    support: StreamLanguage.define(cmake)
  }),
  LanguageDescription.of({
    name: 'Perl',
    alias: ['perl'],
    support: StreamLanguage.define(perl)
  }),
  LanguageDescription.of({
    name: 'HTTP',
    alias: ['http'],
    support: StreamLanguage.define(http)
  }),
  LanguageDescription.of({
    name: 'Dockerfile',
    alias: ['dockerfile'],
    support: StreamLanguage.define(dockerFile)
  }),
  LanguageDescription.of({
    name: 'PowerShell',
    alias: ['powershell', 'ps1'],
    support: StreamLanguage.define(powerShell)
  }),
  LanguageDescription.of({
    name: 'Properties',
    alias: ['properties'],
    support: StreamLanguage.define(properties)
  }),
  LanguageDescription.of({
    name: 'LaTeX',
    alias: ['latex', 'tex', 'stex'],
    support: StreamLanguage.define(stex)
  }),
  LanguageDescription.of({
    name: 'Nginx',
    alias: ['nginx'],
    support: StreamLanguage.define(nginx)
  }),
  LanguageDescription.of({
    name: 'Haskell',
    alias: ['haskell'],
    support: StreamLanguage.define(haskell)
  }),
  LanguageDescription.of({
    name: 'Lua',
    alias: ['lua'],
    support: StreamLanguage.define(lua)
  }),
  LanguageDescription.of({
    name: 'Jinja2',
    alias: ['jinja2', 'jinja'],
    support: StreamLanguage.define(jinja2)
  }),
  LanguageDescription.of({
    name: 'Ruby',
    alias: ['ruby', 'rb'],
    support: StreamLanguage.define(ruby)
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
