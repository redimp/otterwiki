// Lightweight CSS mode for CodeMirror tailored for Otterwiki.
// Based on CodeMirror's simpleMode helper (MIT License).
(function (mod) {
  if (typeof exports == "object" && typeof module == "object") {
    mod(require("../../lib/codemirror"));
  } else if (typeof define == "function" && define.amd) {
    define(["../../lib/codemirror"], mod);
  } else {
    mod(CodeMirror);
  }
})(function (CodeMirror) {
  "use strict";

  CodeMirror.defineSimpleMode("otterwiki-css", {
    start: [
      { regex: /\/\*/, token: "comment", next: "comment" },
      { regex: /@[A-Za-z_-][\w-]*/, token: "def" },
      { regex: /\{/, token: "bracket", push: "decls" },
      { regex: /\}/, token: "bracket" },
      { regex: /[A-Za-z0-9_.#:-]+/, token: "tag" },
      { regex: /\s+/, token: null }
    ],
    comment: [
      { regex: /.*?\*\//, token: "comment", next: "start" },
      { regex: /.*/, token: "comment" }
    ],
    decls: [
      { regex: /\/\*/, token: "comment", next: "commentDecl" },
      { regex: /\}/, token: "bracket", pop: true },
      { regex: /[A-Za-z_-][\w-]*(?=\s*:)/, token: "property" },
      { regex: /!important\b/, token: "keyword" },
      { regex: /#[0-9a-fA-F]{3,8}\b/, token: "atom" },
      { regex: /\b\d+(\.\d+)?(em|px|rem|vh|vw|%)?\b/, token: "number" },
      { regex: /"(?:[^\\"]|\\.)*"?/, token: "string" },
      { regex: /'(?:[^\\']|\\.)*'?/, token: "string" },
      { regex: /:[ \t]*/, token: "operator" },
      { regex: /;/, token: "operator" },
      { regex: /[A-Za-z_-][\w-]*/, token: "atom" },
      { regex: /\s+/, token: null }
    ],
    commentDecl: [
      { regex: /.*?\*\//, token: "comment", next: "decls" },
      { regex: /.*/, token: "comment" }
    ]
  });

  CodeMirror.defineMIME("text/css", "otterwiki-css");
});
