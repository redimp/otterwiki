// CodeMirror 6 Language Modes Registry
// All languages use legacy StreamLanguage modes for CM5-consistent token mapping.
// Only PHP and Markdown use dedicated packages (no legacy mode available / needed for main editor).

import { LanguageDescription, LanguageSupport, StreamLanguage } from '@codemirror/language';

// Dedicated packages (no legacy mode available)
import { php } from '@codemirror/lang-php';
import { markdown } from '@codemirror/lang-markdown';

// Legacy StreamLanguage modes
import { javascript as jsMode, json as jsonMode, typescript as tsMode } from '@codemirror/legacy-modes/mode/javascript';
import { python as pyMode } from '@codemirror/legacy-modes/mode/python';
import { xml as xmlMode, html as htmlMode } from '@codemirror/legacy-modes/mode/xml';
import { css as cssMode } from '@codemirror/legacy-modes/mode/css';
import { standardSQL } from '@codemirror/legacy-modes/mode/sql';
import { go as goMode } from '@codemirror/legacy-modes/mode/go';
import { rust as rustMode } from '@codemirror/legacy-modes/mode/rust';
import { yaml } from '@codemirror/legacy-modes/mode/yaml';
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

// Pre-build LanguageSupport instances for all legacy StreamLanguage modes
const jsSupport = new LanguageSupport(StreamLanguage.define(jsMode));
const tsSupport = new LanguageSupport(StreamLanguage.define(tsMode));
const pySupport = new LanguageSupport(StreamLanguage.define(pyMode));
const xmlSupport = new LanguageSupport(StreamLanguage.define(xmlMode));
const htmlSupport = new LanguageSupport(StreamLanguage.define(htmlMode));
const cssSupport = new LanguageSupport(StreamLanguage.define(cssMode));
const jsonSupport = new LanguageSupport(StreamLanguage.define(jsonMode));
const sqlSupport = new LanguageSupport(StreamLanguage.define(standardSQL));
const goSupport = new LanguageSupport(StreamLanguage.define(goMode));
const rustSupport = new LanguageSupport(StreamLanguage.define(rustMode));
const shellSupport = new LanguageSupport(StreamLanguage.define(shell));
const yamlSupport = new LanguageSupport(StreamLanguage.define(yaml));
const cSupport = new LanguageSupport(StreamLanguage.define(c));
const cppSupport = new LanguageSupport(StreamLanguage.define(cpp));
const javaSupport = new LanguageSupport(StreamLanguage.define(java));
const csharpSupport = new LanguageSupport(StreamLanguage.define(csharp));
const scalaSupport = new LanguageSupport(StreamLanguage.define(scala));
const kotlinSupport = new LanguageSupport(StreamLanguage.define(kotlin));
const tomlSupport = new LanguageSupport(StreamLanguage.define(toml));
const cmakeSupport = new LanguageSupport(StreamLanguage.define(cmake));
const perlSupport = new LanguageSupport(StreamLanguage.define(perl));
const httpSupport = new LanguageSupport(StreamLanguage.define(http));
const dockerFileSupport = new LanguageSupport(StreamLanguage.define(dockerFile));
const powerShellSupport = new LanguageSupport(StreamLanguage.define(powerShell));
const propertiesSupport = new LanguageSupport(StreamLanguage.define(properties));
const stexSupport = new LanguageSupport(StreamLanguage.define(stex));
const nginxSupport = new LanguageSupport(StreamLanguage.define(nginx));
const haskellSupport = new LanguageSupport(StreamLanguage.define(haskell));
const luaSupport = new LanguageSupport(StreamLanguage.define(lua));
const jinja2Support = new LanguageSupport(StreamLanguage.define(jinja2));
const rubySupport = new LanguageSupport(StreamLanguage.define(ruby));

export const codeLanguages = [
  LanguageDescription.of({
    name: 'JavaScript',
    alias: ['javascript', 'js'],
    support: jsSupport,
  }),
  LanguageDescription.of({
    name: 'TypeScript',
    alias: ['typescript', 'ts'],
    support: tsSupport,
  }),
  LanguageDescription.of({
    name: 'Python',
    alias: ['python', 'py'],
    support: pySupport,
  }),
  LanguageDescription.of({
    name: 'XML',
    alias: ['xml'],
    support: xmlSupport,
  }),
  LanguageDescription.of({
    name: 'HTML',
    alias: ['html'],
    support: htmlSupport,
  }),
  LanguageDescription.of({
    name: 'CSS',
    alias: ['css'],
    support: cssSupport,
  }),
  LanguageDescription.of({
    name: 'JSON',
    alias: ['json'],
    support: jsonSupport,
  }),
  LanguageDescription.of({
    name: 'Markdown',
    alias: ['markdown', 'md'],
    support: markdown(),
  }),
  LanguageDescription.of({
    name: 'YAML',
    alias: ['yaml', 'yml'],
    support: yamlSupport,
  }),
  LanguageDescription.of({
    name: 'PHP',
    alias: ['php'],
    support: php(),
  }),
  LanguageDescription.of({
    name: 'SQL',
    alias: ['sql'],
    support: sqlSupport,
  }),
  LanguageDescription.of({
    name: 'Go',
    alias: ['go'],
    support: goSupport,
  }),
  LanguageDescription.of({
    name: 'Rust',
    alias: ['rust'],
    support: rustSupport,
  }),
  LanguageDescription.of({
    name: 'Shell',
    alias: ['shell', 'bash', 'sh'],
    support: shellSupport,
  }),
  LanguageDescription.of({
    name: 'C',
    alias: ['c'],
    support: cSupport,
  }),
  LanguageDescription.of({
    name: 'C++',
    alias: ['cpp', 'c++'],
    support: cppSupport,
  }),
  LanguageDescription.of({
    name: 'Java',
    alias: ['java'],
    support: javaSupport,
  }),
  LanguageDescription.of({
    name: 'C#',
    alias: ['csharp', 'cs'],
    support: csharpSupport,
  }),
  LanguageDescription.of({
    name: 'Scala',
    alias: ['scala'],
    support: scalaSupport,
  }),
  LanguageDescription.of({
    name: 'Kotlin',
    alias: ['kotlin'],
    support: kotlinSupport,
  }),
  LanguageDescription.of({
    name: 'TOML',
    alias: ['toml'],
    support: tomlSupport,
  }),
  LanguageDescription.of({
    name: 'CMake',
    alias: ['cmake'],
    support: cmakeSupport,
  }),
  LanguageDescription.of({
    name: 'Perl',
    alias: ['perl'],
    support: perlSupport,
  }),
  LanguageDescription.of({
    name: 'HTTP',
    alias: ['http'],
    support: httpSupport,
  }),
  LanguageDescription.of({
    name: 'Dockerfile',
    alias: ['dockerfile'],
    support: dockerFileSupport,
  }),
  LanguageDescription.of({
    name: 'PowerShell',
    alias: ['powershell', 'ps1'],
    support: powerShellSupport,
  }),
  LanguageDescription.of({
    name: 'Properties',
    alias: ['properties'],
    support: propertiesSupport,
  }),
  LanguageDescription.of({
    name: 'LaTeX',
    alias: ['latex', 'tex', 'stex'],
    support: stexSupport,
  }),
  LanguageDescription.of({
    name: 'Nginx',
    alias: ['nginx'],
    support: nginxSupport,
  }),
  LanguageDescription.of({
    name: 'Haskell',
    alias: ['haskell'],
    support: haskellSupport,
  }),
  LanguageDescription.of({
    name: 'Lua',
    alias: ['lua'],
    support: luaSupport,
  }),
  LanguageDescription.of({
    name: 'Jinja2',
    alias: ['jinja2', 'jinja'],
    support: jinja2Support,
  }),
  LanguageDescription.of({
    name: 'Ruby',
    alias: ['ruby', 'rb'],
    support: rubySupport,
  }),
];
