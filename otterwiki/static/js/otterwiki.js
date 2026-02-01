/* vim: set et sts=4 ts=4 sw=4 ai: */

const lineEnd = 999999;
const maxMultiLevels = 5;

var otterwiki_editor = {
    /* simple functions */
    undo: function() {
        if (!cm_editor) { return; }
        cm_editor.undo();
    },
    redo: function() {
        if (!cm_editor) { return; }
        cm_editor.redo();
    },
    /* helper functions */
    _setSelectedLines: function(lines) {
        cm_editor.setSelection(
            head = {
                line: lines[0],
                ch: 0
            },
            anchor = {
                line: lines[lines.length - 1],
                ch: lineEnd
            }
        );
    },
    _getSelectedLines: function() {
        const [s, e] = [cm_editor.getCursor('start').line, cm_editor.getCursor('end').line]
        return [...Array(e - s + 1).keys()].map(i => i + s);
    },
    _setLine: function(n, text) {
        cm_editor.replaceRange(
            text, { line: n, ch: 0, },
                  { line: n, ch: lineEnd, }
        );
    },
    _findWordAt: function(pos) {
        var line = cm_editor.getLine(pos.line);
        var start = pos.ch, end = pos.ch;
        if (line) {
            var check = function(ch) {
                return !(/\s|[,\.!\?]/.test(ch));
            }
            while (start > 0 && check(line.charAt(start - 1))) { --start; }
            while (end < line.length && check(line.charAt(end))) { ++end; }
        }
        return { anchor: {line: pos.line, ch: start}, head: { line: pos.line, ch: end }};
    },
    _toggleBlock: function(syntax_chars, token) {
        if (!(syntax_chars instanceof Array)) {
            syntax_chars = [syntax_chars];
        }
        var anythingSelected = true;
        var toggle_off = false;
        // store cursor
        const cursor = cm_editor.getCursor();
        if (cm_editor.getSelection().length == 0) {
            // if nothing is selected, select the word under the cursor
            anythingSelected = false;
            const word = otterwiki_editor._findWordAt(cm_editor.getCursor());
            cm_editor.setSelection(word.anchor, word.head);
        }
        if (cm_editor.getSelection().trim().length == 0) {
            // if still nothing is selected, just insert the syntax characters at the cursor
            cm_editor.doc.replaceRange(syntax_chars[0]+syntax_chars[0], cursor);
        } else {
            // selection that is supposed to be toggled
            const cursor_start = cm_editor.getCursor('start');
            const cursor_end = cm_editor.getCursor('end');
            var text = cm_editor.getSelection()
            // check if block starts with syntax_chars
            toggle_off = false;
            for (const chars of syntax_chars) {
                if (text.startsWith(chars) && text.endsWith(chars)) {
                    toggle_off = true;
                    // slice off syntax chars
                    text = text.slice(chars.length, text.length - chars.length);
                    cm_editor.replaceSelection(text);
                    // update end cursor (start cursor is fine)
                    cursor_end.ch = cursor_end.ch - chars.length;
                    // if on the same line
                    if (cursor_start.line == cursor_end.line) { cursor_end.ch = cursor_end.ch - chars.length; }
                    // select new area
                    cm_editor.setSelection(cursor_start, cursor_end);
                }
            }
            if (!toggle_off) {
                text = syntax_chars[0] + text + syntax_chars[0];
                cm_editor.replaceSelection(text);
                // update end cursor (start cursor is fine)
                cursor_end.ch = cursor_end.ch + syntax_chars[0].length
                // if on the same line
                if (cursor_start.line == cursor_end.line) { cursor_end.ch = cursor_end.ch + syntax_chars[0].length; }
                // select new area
                cm_editor.setSelection(cursor_start, cursor_end);
            }
        }
        if (!anythingSelected) {
            if (toggle_off) {
                setTimeout(() => {
                    cursor.ch -= syntax_chars[0].length;
                    cm_editor.setCursor(cursor);
                }, 0);
            } else {
                setTimeout(() => {
                    cursor.ch += syntax_chars[0].length;
                    cm_editor.setCursor(cursor);
                }, 0);
            }
        }

        cm_editor.focus();
    },
    _toggleMultilineBlock: function(syntaxStartChars, headerRegex = null, syntaxEndChars = null, placeholderContent = null) {
        // This function prepends and appends a selection of one or more entire lines
        // with a new line of "syntax_(start|end)_chars".

        if (!(syntaxStartChars instanceof Array)) {
            syntaxStartChars = [syntaxStartChars];
        }
        if (syntaxEndChars !== null && !(syntaxEndChars instanceof Array)) {
            syntaxEndChars = [syntaxEndChars];
        } else {
            syntaxEndChars = syntaxStartChars;
        }

        if (placeholderContent !== null && !(placeholderContent instanceof Array)) {
            placeholderContent = [placeholderContent];
        } else if (placeholderContent === null) {
            placeholderContent = [];
        }

        let selectedLines = otterwiki_editor._getSelectedLines();
        if (selectedLines.length == 0) return;

        const headerValue = syntaxStartChars[0];
        const tailValue = syntaxEndChars[0];
        let removeBlock = false;
        const firstLine = cm_editor.getLine(selectedLines[0]);

        // The user wants to insert the block on an empty line -> insert with place holder values
        if (selectedLines.length == 1 && firstLine.match(/^$/)) { // user selected an empty line
            const placeholderBlock = headerValue + "\n" + placeholderContent.join("\n") + "\n" + tailValue;
            otterwiki_editor._setLine(selectedLines[0], placeholderBlock);

            const firstLineNum = selectedLines[0];
            selectedLines = []

            // update selected lines to select only the placeholder content
            for (let i = 1; i <= placeholderContent.length; i++) {
                selectedLines.push(firstLineNum + i);
            }
            otterwiki_editor._setSelectedLines(selectedLines);

            cm_editor.focus();
            return
        }

        // Decide whether to add or remove the block, and whether the first line already
        // has content. In the latter case, we have to insert an extra line for the header,
        // because it needs to be on its own line.
        // The first line already is a header =>  Determine whether we should remove, or change the header
        if (headerRegex !== null && firstLine.match(headerRegex)) {

            // Decide whether the first line is the current header line
            let isHeader = false;
            for (const startChar of syntaxStartChars) {
                if (firstLine.trim() == startChar) {
                    isHeader = true;
                    break;
                }
            }

            // the first line includes the header of the block -> remove it
            if (isHeader) {
                otterwiki_editor._setLine(selectedLines[0], "");
                removeBlock = true;

            } else { // the first line is a header, but a different one -> replace header and quit
                otterwiki_editor._setLine(selectedLines[0], headerValue);
                cm_editor.focus();
                return;
            }

        } else if (!firstLine.trim().match("^$")) { // when the first selected line is not empty
            otterwiki_editor._setLine(selectedLines[0], headerValue + "\n" + firstLine);

            // set the selection so the newly added extra line is being included as well
            selectedLines.push(selectedLines[selectedLines.length - 1] + 1);
            otterwiki_editor._setSelectedLines(selectedLines);

            selectedLines = otterwiki_editor._getSelectedLines();

        } else {
            otterwiki_editor._setLine(selectedLines[0], headerValue);
        }

        if (removeBlock) {
            let endFound = false;
            for (const ln of selectedLines.splice(1)) {
                const lineValue = cm_editor.getLine(ln);

                for (const endChar of syntaxEndChars) {
                    if (lineValue.trim() == endChar) {
                        otterwiki_editor._setLine(ln, "");
                        endFound = true;
                        break;
                    }
                }

                if (endFound) break;
            }

            if (!endFound) {
                // We only get here when the ending line was not found in the selection
                // Find block end based on the syntax chars, abort if no end found
                let blockEndLine = -1;
                for (const endChar of syntaxEndChars) {
                    blockEndLine = otterwiki_editor._findNextOccurenceLine(endChar)

                    if (blockEndLine !== -1) {
                        break;
                    }
                }

                if (blockEndLine !== -1) {
                    otterwiki_editor._setLine(blockEndLine, "");
                } else {
                    console.log("ERROR: No block end found! Remove manually.")
                }
            }

        } else {

            // Determine whether the last line is empty, and we may just set the block end
            // or it already contains text, requiring us to add another line
            const lastLineNum = selectedLines[selectedLines.length - 1]
            const lastLine = cm_editor.getLine(lastLineNum);
            let prefix = "";
            if (!lastLine.trim().match(/^$/)) { // last selected line is not empty
                prefix = lastLine + "\n";

                // as we are adding a newline, we need to extend the selected lines by 1
                selectedLines.push(selectedLines[selectedLines.length - 1] + 1);
            }
            otterwiki_editor._setLine(lastLineNum, prefix + tailValue);

            // update the selection
            otterwiki_editor._setSelectedLines(selectedLines);
        }

        cm_editor.focus();
    },
    _toggleLines: function(line_prefix, line_re, token) {
        if (!(line_re instanceof Array)) {
            line_re = [line_re];
        }
        linenumbers = otterwiki_editor._getSelectedLines();
        var count = 1;
        for (const ln of linenumbers) {
            const line = cm_editor.getLine(ln);
            for (const re of line_re) {
                var updated_line = line.replace(re, "");
                // if the re didn't alter the line, add the prefix
                if (updated_line == line) {
                    if (line_prefix == "\\d") {
                        updated_line = count + ". " + line;
                    } else {
                        updated_line = line_prefix + line;
                    }
                }
                otterwiki_editor._setLine(ln, updated_line);
            }
            count += 1;
        }
        cm_editor.focus();
    },
    _toggleLinesMultiLevel: function(indentChar, maxLevel=maxMultiLevels) {
        if (!cm_editor) { return; }
        for (const i of otterwiki_editor._getSelectedLines()) {
            var line = cm_editor.doc.getLine(i);
            var lineHLevel = line.search("[^" + indentChar + "]");
            // In case of a line composed of only "indentChar"
            if (lineHLevel < 0) { lineHLevel = line.length; }
            if (lineHLevel == 0) {
                otterwiki_editor._setLine(i, indentChar + " " + line);
            } else if (lineHLevel / indentChar.length < maxLevel) {
                // add a level
                otterwiki_editor._setLine(i, indentChar + line);
            } else {
                // Remove all indentChars (not sure why the RegExp is needed. It won't work without, though)
                otterwiki_editor._setLine(i, line.replace(new RegExp("^(?:" + indentChar + ")+\\s*"), ''));
            }
        }
        cm_editor.focus();
    },
    _toggleAlert: function(header, placeholderContent = null) {
        const headerValue = "[!" + header.toUpperCase() + "]";
        const headerRegex = "^> \\[!(?:NOTE|TIP|IMPORTANT|WARNING|CAUTION)\\]\\s*$";

        if (placeholderContent !== null && !(placeholderContent instanceof Array)) {
            placeholderContent = [placeholderContent];
        } else if (placeholderContent === null) {
            placeholderContent = [];
        }

        let selectedLines = otterwiki_editor._getSelectedLines();
        if (selectedLines.length == 0) return;

        const firstLine = cm_editor.getLine(selectedLines[0]);
        let placeholderUsed = false;

        // The user wants to insert the block on an empty line -> insert with place holder values
        if (selectedLines.length == 1 && firstLine.match(/^$/)) { // user selected an empty line
            placeholderUsed = true;

            const firstLineNum = selectedLines[0];
            otterwiki_editor._setLine(firstLineNum, "\n" + placeholderContent.join("\n"));

            // update selected lines to select only the placeholder content
            selectedLines = [];
            for (let i = 0; i <= placeholderContent.length; i++) {
                selectedLines.push(firstLineNum + i);
            }
            otterwiki_editor._setSelectedLines(selectedLines);
        }

        // Decide whether to add or remove the alert block, and whether the first line already
        // has content. In the latter case, we have to insert an extra line for the alert
        // header, because it needs to be on its own line.
        // The first line already is a header => Determine whether we should unalert, or change the header
        if (firstLine.match(headerRegex)) {

            // the first line includes the header of the alert block -> "unalert"
            if (firstLine.includes(headerValue)) {
                otterwiki_editor._setLine(selectedLines[0], "> "); // keep the quote, as this is handled below

            } else { // the first line is a header, but a different one -> replace header and quit
                otterwiki_editor._setLine(selectedLines[0], firstLine.replace(/\[![A-Z]+]/, headerValue));
                return;
            }

        } else if (!firstLine.match("^$")) { // when the first selected line is not empty
            otterwiki_editor._setLine(selectedLines[0], headerValue + "\n" + firstLine);

            // set the selection so the newly added extra line is being included as well
            selectedLines.push(selectedLines[selectedLines.length - 1] + 1);
            otterwiki_editor._setSelectedLines(selectedLines);

        } else {
            otterwiki_editor._setLine(selectedLines[0], headerValue);
        }

        // Now, simply quote all selected lines (the header part is what makes alerts special)
        otterwiki_editor.quote(false);

        // Finally, update the selection in case a placeholder was used
        if (placeholderUsed) {
            const lastLine = selectedLines[selectedLines.length - 1];
            cm_editor.setSelection({ line: lastLine, ch: 2 }, { line: lastLine, ch: lineEnd })
        }
    },
    _getState: function(pos) {
        var cm = cm_editor;
        pos = pos || cm.getCursor('start');
        var stat = cm.getTokenAt(pos);

        var ret = {},
            data, text;

        if (stat.linkHref || stat.linkText || stat.linkTitle) {
            ret.link = true;
        }

        if (stat.image || stat.imageAltText || stat.imageMarker) {
            ret.image = true;
        }

        if (stat.code === -1 || stat.code === 1) {
            ret.code = true;
        }

        if (!stat.type) return ret;

        var types = stat.type.split(' ');
        for (var i = 0; i < types.length; i++) {
            data = types[i];
            if (data === 'strong') {
                ret.bold = true;
            } else if (data === 'variable-2') {
                text = cm.getLine(pos.line);
                if (/^\s*\d+\.\s/.test(text)) {
                    ret['ol'] = true;
                } else {
                    ret['ul'] = true;
                }
            } else if (data === 'atom') {
                ret.quote = true;
            } else if (data === 'em') {
                ret.italic = true;
            } else if (data === 'quote') {
                ret.quote = true;
            } else if (data === 'strikethrough') {
                ret.strikethrough = true;
            } else if (data === 'comment') {
                ret.code = true;
            } else if (data === 'link' && !ret.image) {
                ret.link = true;
            } else if (data === 'image') {
                ret.image = true;
            } else if (data === 'url') {
                ret.url = true;
            } else if (data.match(/^header(-[1-6])?$/)) {
                ret[data.replace('header', 'heading')] = true;
            }
        }
        return ret;
    },
    /* formating functions */
    // header: increase the mardown header level till five remove afterwards
    header: function() {
        otterwiki_editor._toggleLinesMultiLevel("#");
    },
    bold: function() {
        otterwiki_editor._toggleBlock(["**","__"], "bold");
    },
    italic: function() {
        otterwiki_editor._toggleBlock(["_","*"], "italic");
    },
    strikethrough: function() {
        otterwiki_editor._toggleBlock("~~", "strikethrough");
    },
    spoiler: function() {
        const placeholder = "Hidden content";
        const selectedLines = otterwiki_editor._getSelectedLines();
        const firstLine = cm_editor.getLine(selectedLines[0]);
        let placeholderUsed = false;

        if (selectedLines.length == 1 && firstLine.match(/^\s*$/)) {
            otterwiki_editor._setLine(selectedLines[0], placeholder);
            placeholderUsed = true;
        }

        otterwiki_editor._toggleLinesMultiLevel(">!");

        // Update selection in case a placeholder was used
        // we can only do this after the spoiler prefix has been added
        if (placeholderUsed) {
            cm_editor.setSelection({ line: selectedLines[0], ch: 3 }, { line: selectedLines[0], ch: 3 + placeholder.length });
        }
    },
    expand: function() {
        // Determine the current format of the first selected line
        // If it already is a header -> undo the expand block
        // otherwise, add a markdown header indicator
        let selectedLines = otterwiki_editor._getSelectedLines()
        const firstLineNum = selectedLines[0];
        const firstLine = cm_editor.getLine(firstLineNum);

        const headerPlaceholder = "Summary";
        const contentPlaceholder = "Folded content";
        let extendSelection = false;
        let placeholderUsed = false;

        // Apply the header regex (matches both, lines with expand and lines without)
        let updatedLine = firstLine.replace(/(\s*>\|\s+)?#\s+/, "$1")

        // if the regex did not alter the line, there is no header present yet
        // --> add the header prefix
        if (updatedLine.length > 0 && updatedLine == firstLine) {
            updatedLine = "# " + firstLine;
        } else if (updatedLine.length == 0) {
            placeholderUsed = true;
            updatedLine = "# " + headerPlaceholder;

            // if the user selected only one line, add placeholder content as well
            if (selectedLines.length == 1) {
                updatedLine += "\n" + contentPlaceholder;
                extendSelection = true;
            }
        }
        otterwiki_editor._setLine(firstLineNum, updatedLine);

        // we have to extend the selection AFTER updating the line
        // otherwise this would fail if extending below the current max line
        if (extendSelection) {
            otterwiki_editor._setSelectedLines([firstLineNum, firstLineNum + 1]);
            selectedLines = otterwiki_editor._getSelectedLines();
        }

        // Finally, add the expand syntax on each selected line
        otterwiki_editor._toggleLines(">| ", [/\s*>\|\s+/], "expand");

        // Update selection in case a placeholder was used
        if (placeholderUsed && !extendSelection) {
            // ... select the header value, in case only the header was added as placeholder
            // offset of 5 comes from the expand syntax '>| ' and the header syntax '# '
            cm_editor.setSelection({ line: firstLineNum, ch: 5 }, { line: firstLineNum, ch: 5 + headerPlaceholder.length });

        } else if (placeholderUsed && extendSelection) {
            // ... select the content placeholder in case header AND content were placeholders
            const lastLine = selectedLines[selectedLines.length - 1];

            // offset of 3 comes from the expand syntax '>| '
            cm_editor.setSelection({ line: lastLine, ch: 3 }, { line: lastLine, ch: 3 + contentPlaceholder.length });
        }
    },
    code: function() {
        otterwiki_editor._toggleBlock(["`", "```"], "code");
    },
    codeBlock: function() {
        otterwiki_editor._toggleMultilineBlock("```", /^```\w*/, null, "code");
    },
    hr: function() {
        let linenumbers = otterwiki_editor._getSelectedLines();
        let changed = false;
        let line = "";
        let ln = 0;
        for (ln of linenumbers) {
            line = cm_editor.getLine(ln);
            let updated_line = line.replace(/^---\w*/, "");
            if (updated_line != line) {
                changed = true;
                otterwiki_editor._setLine(ln, updated_line);
            }
        }
        if (!changed) {
            let cursor = cm_editor.getCursor('start');
            let line_insert = "---";
            let hr_ln = ln;
            // check if the current line is not empty
            if (cm_editor.getLine(ln) != "") {
                hr_ln += 2;
                line_insert = line + "\n\n" + line_insert;
            }
            // check the next line
            if (cm_editor.lastLine() < ln+1 || cm_editor.getLine(ln+1) != "") {
                line_insert = line_insert + "\n"
            }
            otterwiki_editor._setLine(ln, line_insert);
            // update cursor
            cursor.line = Math.min(hr_ln,  cm_editor.lastLine());
            cursor.ch = 3;
            cm_editor.setCursor(cursor);
        }
        cm_editor.focus();
    },
    // quote: increase the markdown quote level till five, remove afterwards
    quote: function (multilevel = true) {
        otterwiki_editor._toggleLinesMultiLevel(">", multilevel ? maxMultiLevels : 1);
    },
    ul: function() {
        otterwiki_editor._toggleLines("- ",[/\s*[-+*]\s+/], "ul");
   },
    ol: function() {
        otterwiki_editor._toggleLines("\\d",[/\s*\d+\.\s+/], "ol");
    },
    cl: function() {
        otterwiki_editor._toggleLines("- [ ] ",[/\s*[-+*] \[ \]\s+/], "ul");
    },
    panelNotice: function() {
        otterwiki_editor._toggleMultilineBlock(":::info", /^:::(info|warning|danger)/, ":::", ["# Header", "Content"]);
    },
    panelWarning: function() {
        otterwiki_editor._toggleMultilineBlock(":::warning", /^:::(info|warning|danger)/, ":::", ["# Header", "Content"]);
    },
    panelDanger: function() {
        otterwiki_editor._toggleMultilineBlock(":::danger", /^:::(info|warning|danger)/, ":::", ["# Header", "Content"]);
    },
    img: function(img = "![]()") {
        if (!cm_editor) { return; }
        state = otterwiki_editor._getState();
        // we don't mess with existing tokens of these kinds
        if (state.image || state.link) { return; }

        const link = img;

        var text = cm_editor.getSelection();
        cm_editor.replaceSelection(text + link);

        let cursor = cm_editor.getCursor();
        cursor.ch -= 1;
        cm_editor.setCursor(cursor);

        cm_editor.focus();
    },
    diagram: function() {
        otterwiki_editor._toggleMultilineBlock("```mermaid", /^```mermaid/, "```", "See https://mermaid.js.org/intro/");
    },
    alertNote: function() {
        otterwiki_editor._toggleAlert("note", ["Content"]);
    },
    alertTip: function() {
        otterwiki_editor._toggleAlert("tip", ["Content"]);
    },
    alertImportant: function() {
        otterwiki_editor._toggleAlert("important", ["Content"]);
    },
    alertWarning: function() {
        otterwiki_editor._toggleAlert("warning", ["Content"]);
    },
    alertCaution: function() {
        otterwiki_editor._toggleAlert("caution", ["Content"]);
    },
    link: function(text = "description", url = "https://") {
        if (!cm_editor) { return; }
        let state = otterwiki_editor._getState();
        // we don't mess with existing tokens of these kinds
        if (state.img || state.link || state.url ) { return; }

        if (cm_editor.getSelection().length == 0) {
            // if nothing is selected, select the word under the cursor
            anythingSelected = false;
            let word = otterwiki_editor._findWordAt(cm_editor.getCursor());
            cm_editor.setSelection(word.anchor, word.head);
        }
        if (cm_editor.getSelection().trim().length == 0) {
            cm_editor.replaceSelection("[description](https://)");
        } else {
            let text = cm_editor.getSelection();
            cm_editor.replaceSelection("["+ text + "]" + "(https://)");
        }
        let cursor = cm_editor.getCursor();
        cursor.ch -= 1;
        cm_editor.setCursor(cursor);

        cm_editor.focus();
    },
    footnote: function() {
        const startChar = "[^";
        const endChar = "]";

        let selectedLines = otterwiki_editor._getSelectedLines();
        if (selectedLines.length > 1) {
            // If multiple lines are selected, use the last one
            otterwiki_editor._setSelectedLines(selectedLines.slice(selectedLines.length - 1));
            selectedLines = otterwiki_editor._getSelectedLines();
        }

        // Determine how to insert the footnote in the text
        let footNoteValue = "footnote_identifier";
        const selectedText = cm_editor.getSelection();
        const lineContent = cm_editor.getLine(selectedLines[0]);

        // default values for assumption that the line is empty and no text is selected
        let newLine = startChar + footNoteValue + endChar;
        let fnIdentifierStart = startChar.length;
        let fnIdentifierEnd = fnIdentifierStart + footNoteValue.length;

        if (selectedText) { // Text is selected, make it the footnote content
            const selectedTextStart = lineContent.indexOf(selectedText);
            const selectedTextEnd = selectedTextStart + selectedText.length;

            footNoteValue = selectedText;

            newLine = lineContent.slice(0, selectedTextStart) + startChar + footNoteValue + endChar + lineContent.slice(selectedTextEnd);

            fnIdentifierStart = selectedTextStart + startChar.length;
            fnIdentifierEnd = selectedTextEnd + startChar.length

        } else if (lineContent.length) { // No text is selected, but line is not empty
            const cursorPos = cm_editor.getCursor('start');
            newLine = lineContent.slice(0, cursorPos.ch) + newLine + lineContent.slice(cursorPos.ch);

            fnIdentifierStart = cursorPos.ch + startChar.length;
            fnIdentifierEnd = fnIdentifierStart + footNoteValue.length;
        }

        otterwiki_editor._setLine(selectedLines[0], newLine);

        // Add the footnote to the end of the document
        // TODO: It would be more user-friendly to insert the footnote at the correct position
        const lastLine = cm_editor.lineCount() - 1;
        const lastLineContent = cm_editor.getLine(lastLine);

        // if the last line already is a foot note reference, simply append our current footnote
        // otherwise, add an _extra_ newline to get some spacing to the actual content
        const separator = lastLineContent.startsWith(startChar) && lastLineContent.includes(endChar + ": ") ? "" : "\n";
        otterwiki_editor._setLine(lastLine, lastLineContent + separator + "\n" + startChar + footNoteValue + endChar + ": footnote_description");

        // NOTE: it seems as though footnote references are supported anywhere in the document
        //       as long as the lines starts with a correctly formatted footnote reference.
        //       This is not considered here, footnote references are always appended to the document's end

        // Last, select the newly added footnote's identifier
        cm_editor.setSelection({ line: selectedLines[0], ch: fnIdentifierStart }, { line: selectedLines[0], ch: fnIdentifierEnd });
        cm_editor.focus()
    },
    _findNextOccurenceLine: function(lineContent) {
        // Find the next line starting AFTER the current selection that matches lineContent
        const selectedLines = otterwiki_editor._getSelectedLines();
        const lineAfterSelection = selectedLines[selectedLines.length - 1];
        const editorLastLine = cm_editor.doc.lineCount();

        for (let l = lineAfterSelection; l < editorLastLine; l++) {
            if (cm_editor.getLine(l) == lineContent) {
                return l;
            }
        }
        return -1;
    },
    _findBlock: function(selectBlock = false) {
        var block_start = Number.MAX_SAFE_INTEGER;
        var block_end = Number.MIN_SAFE_INTEGER;
        var block_end_len = 0;
        for (const i of otterwiki_editor._getSelectedLines()) {
            const line = cm_editor.getLine(i);
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

        // if this is zero, only empty lines have been found.
        if (block_end_len == 0) { return false; }

        // check lines before block_start
        for (var i = block_start; i > 0; i--) {
            const line = cm_editor.getLine(i);
            if (line.trim().length > 0) {
                block_start = i;
            } else {
                break;
            }
        }
        // check lines after block_end
        for (var i = block_end; i < cm_editor.doc.lineCount(); i++) {
            const line = cm_editor.getLine(i);
            if (line.trim().length > 0) {
                block_end = i;
                block_end_len = line.length;
            } else {
                break;
            }
        }
        if (selectBlock) {
            // create selection
            cm_editor.doc.setSelection({line: block_start, ch: 0}, {line: block_end, ch: block_end_len});
        }
        // and return selection
        return [{line: block_start, ch: 0}, {line: block_end, ch: block_end_len}];
    },
    _findCursorCell: function(row, ch) {
        let cells = row.split(/(?<!\\)\|/);
        let x = 0;
        let c = 0;
        for (x in cells) {
            c += cells[x].length+1;
            if (ch < c) return x;
        }
        return cells.length - 1;
    },
    _findTable: function() {
        var orig_cursor = cm_editor.getCursor('start');
        var orig_cursor_end = cm_editor.getCursor('end');
        const block = otterwiki_editor._findBlock(true);
        // no block found
        if (!block) return;
        const [block_start, block_end] = block;
        // the relative cursor is positoned in the selection
        var relative_cursor = { line: orig_cursor.line - block_start.line, ch: orig_cursor.ch };
        // get selected block
        var text = cm_editor.getSelection();
        // parse table
        var match = text.match(/\|(.+)\n *\|( *[-:]+[-| :]*)\n((?: *\|.*(?:\n|$))*)\n{0,1}/);
        if (match == null) {
            // restore selection
            cm_editor.setSelection(orig_cursor, orig_cursor_end);
            return;
        }
        // clean header, align and cells
        var header = match[1].replace(/\| *$/, '');
        var align = match[2].replace(/\| *$/, '');
        var celltext = match[3].replace(/(?: *\| *)?\n$/, '');
        // calc column for relative_cursor
        if (relative_cursor.line == 0) relative_cursor.col = otterwiki_editor._findCursorCell(header, relative_cursor.ch);
        if (relative_cursor.line == 1) relative_cursor.col = otterwiki_editor._findCursorCell(align, relative_cursor.ch);
        // split header and align row
        header = header.split(/ *\| */);
        align = align.split(/ *\| */);
        celltext = celltext.split(/\n/)
        var cells = [];
        var i, j, line, cell, row;
        var n_columns = Math.max(header.length, align.length);
        // trim header
        for (i in header)
        {
            header[i] = header[i].trim();
        }
        // parse cell text
        for (i in celltext)
        {
            row = [];
            line = celltext[i];

            // calc column for relative_cursor
            if (relative_cursor.line - 2 == i) relative_cursor.col = otterwiki_editor._findCursorCell(line, relative_cursor.ch) - 1;

            // mistune does:
            // line = line.replace(/^ *\| *| *\| *$/, '');

            // remove leading pipe
            line = line.replace(/^ *\| */, '');
            // remove trailing pipe
            line = line.replace(/ *\|$/, '');
            // split line by pipes and respect escaped \|
            // line = line.split(/ *(?<!\\)\| */);
            line = line.split(/(?<!\\)\|/);
            // update colum counter
            n_columns = Math.max(n_columns, line.length);
            for (j in line)
            {
                row.push(line[j].trim());
            }
            cells.push(row);
        }
        // parse align
        for (i in align) {
            if (align[i].startsWith(':')) {
                if (align[i].endsWith(':')) { align[i]='center'; }
                else { align[i]='left'; }
            } else if (align[i].endsWith(':')) {
                align[i]='right';
            } else {
                align[i]='undef';
            }
        }
        // calculate colum width and fix all the rows
        let colum_width = new Array(n_columns).fill(1);
        // add missing cells to .. header
        while (header.length < n_columns) header.push('');
        for (j in header) colum_width[j] = Math.max(colum_width[j], header[j].length);
        // .. align
        while (align.length < n_columns) align.push('undef')
        // .. cells
        for (i in cells) {
            while (cells[i].length < n_columns) cells[i].push('');
            for (j in cells[i]) colum_width[j] = Math.max(colum_width[j], cells[i][j].length);
        }
        return { header: header, align: align, cells: cells, colum_width: colum_width, row: parseInt(relative_cursor.line), col: parseInt(relative_cursor.col) };
    },
    _alignStr: function (s = "", l = 0, a = "") {
        if (a == "right") return s.padStart(l, ' ');
        if (a == "center") {
            let flip = false;
            while (s.length < l) {
                if (flip) s += " ";
                else s = " " + s;
                flip = !flip;
            }
            return s;
        }
        return s.padEnd(l, ' ');
    },
    _tableArray: function(t) {
        var arr = [];
        var row = [];
        // generate header
        for (var j in t.header) {
            row.push(" "+otterwiki_editor._alignStr(t.header[j], t.colum_width[j], t.align[j])+" ");
        }
        arr.push(row);
        // generate alignment row
        row = [];
        for (var j in t.align) {
            if (t.align[j] == "left") row.push(":"+"-".repeat(t.colum_width[j])+" ");
            else if (t.align[j] == "right") row.push(" "+"-".repeat(t.colum_width[j])+":");
            else if (t.align[j] == "center") row.push(":"+"-".repeat(t.colum_width[j])+":");
            else row.push(" "+"-".repeat(t.colum_width[j])+" ");
        }
        arr.push(row);
        // generate cells row by row
        for (var i in t.cells) {
            row = [];
            for (var j in t.cells[i]) {
                row.push(" "+otterwiki_editor._alignStr(t.cells[i][j], t.colum_width[j], t.align[j])+" ");
            }
            arr.push(row);
        }
        return arr;
    },
    table_arr_replace: function(arr, row = null, col = 0) {
        // build markdown table from array
        var text = "";
        for (var i in arr) {
            text += "|" + arr[i].join("|")+ "|\n";
        }
        // insert into the editor and remove the trailing newline
        cm_editor.replaceSelection(text.trim(), "around");
        // place cursor if row not null
        if (row != null) {
            var cursor = cm_editor.getCursor('start');
            cursor.line += row;
            cursor.ch = 2;
            for (var j=1; j<=col; j++)
            {
                cursor.ch += arr[0][j-1].length + 1;
            }
            cm_editor.setCursor(cursor);
        }
    },
    table: function() {
        if (!cm_editor) { return; }
        // store cursor
        var orig_cursor = cm_editor.getCursor('start')
        // find table in current block
        t = otterwiki_editor._findTable();
        if (!(t)) {
            // no table found: add an empty one
            const text = cm_editor.getSelection();
            const table = "\n\n| Column 1 | Column 2 | Column 3 |\n| -------- | -------- | -------- |\n| Text     | Text     | Text     |\n\n"
            cm_editor.replaceSelection(text + table);
        } else {
            arr = otterwiki_editor._tableArray(t);
            otterwiki_editor.table_arr_replace(arr);
        }
        cm_editor.focus();
    },
    // row manipulation
    table_add_row: function() {
        if (!cm_editor) return;
        // find table
        var t = otterwiki_editor._findTable();
        if (!t) return;
        // get table as array
        var arr = otterwiki_editor._tableArray(t);
        // craft row
        var empty_row = [];
        for (var j in t.colum_width)
        {
            empty_row.push(otterwiki_editor._alignStr("", t.colum_width[j]+2, t.align[j]));
        }
        // insert row into arr
        var row = Math.max(2, t.row);
        if (row>=arr.length) {
            arr.push(empty_row);
        } else {
            arr.splice(row, 0, empty_row);
        }
        // update editor
        otterwiki_editor.table_arr_replace(arr, Math.max(2, row));
        cm_editor.focus();
    },
    table_remove_row: function() {
        if (!cm_editor) return;
        // find table
        var t = otterwiki_editor._findTable();
        if (!t) return;
        if (t.row < 2) return;
        // get table as array
        var arr = otterwiki_editor._tableArray(t);
        // row limits
        var row = Math.min(arr.length-1,Math.max(2, t.row));
        arr.splice(row, 1);
        // update editor
        otterwiki_editor.table_arr_replace(arr, row, t.col);
        cm_editor.focus();
    },
    table_move_row_up: function() {
        if (!cm_editor) return;
        var c = cm_editor.getCursor('start')
        // find table
        var t = otterwiki_editor._findTable();
        if (!t) return;
        if (t.row < 3) {
            // either already on top in the header
            cm_editor.setCursor(c);
        } else {
            // get table as array
            var arr = otterwiki_editor._tableArray(t);
            arr[t.row]=arr.splice(t.row-1, 1, arr[t.row])[0];
            // update editor
            otterwiki_editor.table_arr_replace(arr, t.row - 1, t.col);
        }
        cm_editor.focus();
    },
    table_move_row_down: function() {
        if (!cm_editor) return;
        // find table
        var t = otterwiki_editor._findTable();
        if (!t) return;
        // already on bottom of the table
        if (t.row >= t.cells.length + 1) return; // +2 -1
        // get table as array
        var arr = otterwiki_editor._tableArray(t);
        arr[t.row]=arr.splice(t.row+1, 1, arr[t.row])[0];
        // update editor
        otterwiki_editor.table_arr_replace(arr, t.row+1, t.col);
        cm_editor.focus();
    },
    // column manipulation
    table_add_column: function() {
        if (!cm_editor) return;
        // find table
        var t = otterwiki_editor._findTable();
        if (!t) return;
        // get table as array
        var arr = otterwiki_editor._tableArray(t);
        // craft row
        for (var i in arr)
        {
            let cell = "   ";
            if (i==1) cell = " - ";
            arr[i].splice(t.col, 0, cell);
        }
        // update editor
        otterwiki_editor.table_arr_replace(arr, t.row, t.col);
        cm_editor.focus();
    },
    table_remove_column: function() {
        if (!cm_editor) return;
        // find table
        var t = otterwiki_editor._findTable();
        if (!t) return;
        // get table as array
        var arr = otterwiki_editor._tableArray(t);
        // craft row
        for (var i in arr)
        {
            arr[i].splice(t.col, 1);
        }
        // update editor
        otterwiki_editor.table_arr_replace(arr, t.row, Math.min(arr[0].length-1,t.col));
        cm_editor.focus();
    },
    table_move_column: function(offset = 1) {
        if (!cm_editor) return;
        var c = cm_editor.getCursor('start')
        // find table
        var t = otterwiki_editor._findTable();
        if (!t) return;
        // get table as array
        var arr = otterwiki_editor._tableArray(t);
        offset = parseInt(offset);
        if (t.col+offset >= arr[0].length || t.col+offset < 0) {
            // restore cursor
            cm_editor.setCursor(c);
        } else {
            for (var i in arr) {
                arr[i][t.col]=arr[i].splice(t.col+offset, 1, arr[i][t.col])[0];
            }
            // update editor
            otterwiki_editor.table_arr_replace(arr, t.row, t.col+offset);
        }
        cm_editor.focus();
    },
    // alignment manipulation
    table_align_col: function(align = 'undef') {
        if (!cm_editor) return;
        // find table
        var t = otterwiki_editor._findTable();
        if (!t) return;
        // update alignment
        if (t.align[t.col] != align)
            t.align[t.col] = align;
        else
            t.align[t.col] = 'undef';
        // get table as array with the updated alignment
        var arr = otterwiki_editor._tableArray(t);
        otterwiki_editor.table_arr_replace(arr, t.row, t.col);
        cm_editor.focus();
    },
    update_attachment_preview: function() {
        var element = document.getElementById("attachment-filename");
        if (typeof(element) == 'undefined' || element == null) { return; }
        // split value in filename, url and thumbnail_url
        let filename = element.value.split("/--/")[0];
        let url = element.value.split("/--/")[1];
        let thumbnail_url = element.value.split("/--/")[2];
        // empty preview box
        document.getElementById("extranav-preview").innerHTML = "";

        if (thumbnail_url == '') {
            // update options
            if (document.getElementById("attachment-link").checked != true)
            {
                document.getElementById("attachment-link").checked = true;
            }
            document.getElementById("attachment-image").disabled = true;
            document.getElementById("attachment-thumbnail").disabled = true;
        } else {
            // image with thumbnail_url
            // update preview box
            let preview_img = document.createElement("img");
            preview_img.setAttribute("src", thumbnail_url);
            preview_img.setAttribute("alt", filename);
            document.getElementById("extranav-preview").appendChild(preview_img);
            // update options
            document.getElementById("attachment-image").disabled = false;
            document.getElementById("attachment-thumbnail").disabled = false;
        }

        // Toggle thumbnail size field visibility based on current selection
        if (typeof toggleThumbnailSizeField === 'function') {
            toggleThumbnailSizeField();
        }
    },
    insert_attachment: function() {
        let element = document.getElementById("attachment-filename");
        if (typeof(element) == 'undefined' || element == null) { return; }
        // split value in filename, url and thumbnail_url
        let filename = element.value.split("/--/")[0];
        let url = element.value.split("/--/")[1];
        let thumbnail_url = element.value.split("/--/")[2];
        let attachment_type = document.querySelector("input[type='radio'][name=attachment-type]:checked").value;
        if (typeof(attachment_type) == 'undefined' || attachment_type == null || attachment_type == '') { attachment_type = "link"; }
        // handle relative and absolute paths
        let attachment_absolute = document.getElementById("attachment-absolute").checked;
        if (typeof(attachment_absolute) == 'undefined' || attachment_absolute == null || attachment_absolute == '') { attachment_absolute = false; }
        if (!attachment_absolute) {
            url = "./" + url.split("/").slice(-1)[0];
            thumbnail_url = "./" + thumbnail_url.split("/").slice(-1)[0];
        }

        // handle thumbnail size parameter
        if (attachment_type == "thumbnail") {
            let thumbnail_size_element = document.getElementById("thumbnail-size");
            let thumbnail_size = thumbnail_size_element ? thumbnail_size_element.value.trim() : '';
            if (thumbnail_size && thumbnail_size.match(/^\d+$/)) {
                // Add size parameter to thumbnail URL
                thumbnail_url += '=' + thumbnail_size;
            }
        }

        if (attachment_type == "image") {
            otterwiki_editor.img('![]('+url+')\n');
        } else if (attachment_type == "thumbnail") {
            otterwiki_editor.img('[![]('+thumbnail_url+')]('+url+')\n');
        } else { // link
            otterwiki_editor.img('['+filename+']('+url+')\n');
        }
    },
    insert_wikilink: function(absolute = true) {
        if (!cm_editor) { return; }
        let state = otterwiki_editor._getState();
        // we don't mess with existing tokens of these kinds
        if (state.img || state.link || state.url ) { return; }

        var element = document.getElementById("wikilink");
        if (typeof(element) == 'undefined' || element == null) { return; }

        // split value in filename, url and thumbnail_url
        var page = element.value.split("//")[0];
        if (typeof(page) == 'undefined' || page == null || page == '') { return; }

        if (cm_editor.getSelection().length == 0) {
            // if nothing is selected, select the word under the cursor
            anythingSelected = false;
            let word = otterwiki_editor._findWordAt(cm_editor.getCursor());
            cm_editor.setSelection(word.anchor, word.head);
        }
        if (cm_editor.getSelection().trim().length == 0) {
            if(!absolute) {
                // from issue #357 allow for link insert with [[ title | page ]] format
                let title = page.split('/').at(-1);
                cm_editor.replaceSelection('[[' + title + '|' + page + ']]\n');
            } else {
                cm_editor.replaceSelection('[[' + page + ']]\n');
            }
        } else {
            let text = cm_editor.getSelection();
            cm_editor.replaceSelection('[['+text+'|'+page+']]\n');
        }
        let cursor = cm_editor.getCursor();
        cursor.ch -= 1;
        cm_editor.setCursor(cursor);

        cm_editor.focus();
    },
    paste_url: function(url) {
        if (!cm_editor) return false;
        let selected_text = cm_editor.getSelection();
        // dont replace an url with a markdown link
        if (/^https?:\/\//.test(selected_text)) { return false; }
        // if an url is pasted on a selected text, check if it should be
        // replaced with a markdown link []()
        if (cm_editor.getSelection().length > 0) {
            state = otterwiki_editor._getState();
            // we don't mess with existing tokens of these kinds
            if (state.image || state.link || state.code || state.url) { return false; }

            // build markdown link
            const link = "[" + selected_text + "](" + url + ")";
            // and replace it in the editor
            cm_editor.replaceSelection(link);
            return true;
        }
        return false;
    },
    on_paste: function(e) {
        let clipboardData = e.clipboardData,
            result = false;
        if (typeof clipboardData === "object") {
            let pastedText = clipboardData.getData("text/plain");
            let matched = /^https?:\/\//.test(pastedText);
            if (matched) {
                result = otterwiki_editor.paste_url(pastedText);
            }
        }
        if (result) { e.preventDefault(); }
        return result;
    }
}

var otterwiki = {
    // Toggle display block/none
    toggleClass: function(show, classname) {
        const boxes = document.getElementsByClassName(classname);
        if (show) {
            for (const box of boxes) {
                box.style.display = 'block';
            }
        } else {
            for (const box of boxes) {
                box.style.display = 'none';
            }
        }
    },
    // Toggle modal (using Javascript)
    toggleModal: function(modalId) {
        var modal = document.getElementById(modalId);

        if (modal) {
            modal.classList.toggle("show");
            var input_commit_message = document.getElementById('commit-message')
            if (input_commit_message) {
                input_commit_message.focus()
            }
        }
    },
    toggleMarkdownHelp: function() {
        var ehm = document.getElementById("editor-help-markdown");
        currDisplay = ehm.style.display;
        if (ehm.style.display === "none")
        {
            ehm.style.display = "block";
            otterwiki.update_mermaid();
        }
        else
        {
            ehm.style.display = "none";
        }
    },
    toggle_spoiler: function(btn) {
        btn.parentNode.classList.toggle('nospoiler');
        if (btn.parentNode.classList.contains('nospoiler'))
        {
            btn.innerHTML = '<i class="far fa-eye-slash"></i>';
        }
        else
        {
            btn.innerHTML = '<i class="far fa-eye"></i>';
        }
    },
    toggle_pagename_prefix: function(element, p) {
        pagename = document.getElementById(element);

        pagename.focus();
        if (pagename.value.startsWith(p + "/")) {
            pagename.value = pagename.value.slice(p.length + 1);
        }
        else if (pagename.value.startsWith(p)) {
            pagename.value = pagename.value.slice(p.length);
        } else {
            pagename.value = p + "/" + pagename.value;
        }
        return false;
    },
    update_mermaid: function() {
        if (typeof(mermaid) == 'undefined' || mermaid == null) { return; }

        var mm_diagrams = document.getElementsByClassName('mermaid');
        for (var i = 0; i < mm_diagrams.length; ++i) {
            mm_diagrams[i].removeAttribute('data-processed');
        }
        mermaid.contentLoaded();
    },
    copy_to_clipboard: function(btn) {
        var pre_element = btn.parentElement.parentElement.querySelector("pre.copy-to-clipboard");
        if (typeof(pre_element) == 'undefined' || pre_element == 'undefined' || pre_element == null) {
            console.log("Error: pre element matching the button could not found. This is a bug.")
            return;
        }
        navigator.clipboard.writeText(pre_element.innerText);
    },
    toggle_invert_by_name: function(checkbox_name) {
        let checkboxes = document.querySelectorAll('input[name='+checkbox_name+']');
        for (let i = 0; i < checkboxes.length; i++) {
            checkboxes[i].checked = !checkboxes[i].checked;
        }
    }
}

var MathJax = {
    tex: {
        inlineMath: [["\\(", "\\)"]],
        displayMath: [ ['\\[', '\\]'], ],
        processEscapes: true,
    }
};

/* Hot Keys */
window.addEventListener("keydown", function(event) {
    let isInputElement = event.srcElement instanceof HTMLInputElement;
    let isTextAreaElement = event.srcElement instanceof HTMLTextAreaElement;
    let tagName = event.target.tagName.toLowerCase();
    let isContentEditable = event.target.isContentEditable;
    // I'm a bit paranoid here, want to be sure that nothing is missed again
    let isEditable = (isInputElement || isTextAreaElement || tagName === 'input' || tagName === 'textarea' || isContentEditable);
    let inCodeMirror = document.getElementsByClassName("CodeMirror");
    inCodeMirror = inCodeMirror.length === 1 && inCodeMirror[0].contains(event.target);

    let command = event.ctrlKey || event.metaKey;
    let alt = event.altKey;
    let shift = event.shiftKey;
    let key = event.key;
    let noModifiers = !(command || alt || shift);

    // Note: each keybinding must check the state of all modifier keys to avoid unintended conflicts.

    let savePageBtn = document.getElementById("save-page-btn");
    if (command && !shift && !alt && key === 's' && savePageBtn != null) {
        event.preventDefault();
        document.getElementById("save-page-btn").click();
        return;
    }

    // Bind CTRL / CMD + p to toggle preview / edit when editing a page
    const preview_buttons = ["preview_btn", "editor_btn"];
    for (let i = 0; i < preview_buttons.length; i++) {
        let button_id = preview_buttons[i];
        let button = document.getElementById(button_id);
        if (command && !shift && !alt && key === 'p' && button != null && button.style.display !== 'none') {
            event.preventDefault();
            button.click();
            break;
        }
    }

    // Editor keybindings
    if (inCodeMirror) {
        if (command && !shift && !alt && key === 'b') {
            otterwiki_editor.bold();
            event.preventDefault();
            return;
        }

        if (command && !shift && !alt && key === 'i') {
            otterwiki_editor.italic();
            event.preventDefault();
            return;
        }

        if (command && !shift && !alt && key === 'k') {
            otterwiki_editor.link();
            event.preventDefault();
            return;
        }

        /* // Disabled CMD-M since this is a MacOS shortcut for minimizing the current window.
        if (command && !shift && !alt && key === 'm') {
            otterwiki_editor.img();
            event.preventDefault();
            return;
        }
        */

        if (command && shift && !alt && key === 's') {
            otterwiki_editor.strikethrough();
            event.preventDefault();
            return;
        }

        /* // Disabled CMD-SHIFT-B since this opens the Bookmarks in Chrome
        if (command && shift && !alt && key === 'b') {
            otterwiki_editor.ul();
            event.preventDefault();
            return;
        }
        */

        /* // Disabled CMD-SHIFT-N since this is the Chrome shortcut for a new incognito window
        if (command && shift && !alt && key === 'n') {
            otterwiki_editor.ol();
            event.preventDefault();
            return;
        }
        */

        /* // Disabled CMD-SHIFT-T since this is the Chrome shortcut re-opening the last closed tab.
        if (command && shift && !alt && key === 't') {
            otterwiki_editor.cl();
            event.preventDefault();
            return;
        }
        */

        /* // Disabled since CTRL-SHIFT-C opens the dev console in Chrome on Windows
        if (command && shift && !alt && key === 'c') {
            otterwiki_editor.codeBlock();
            event.preventDefault();
            return;
        }
        */

        /* // Disabled since these shortcuts worked in no browser for me
        if (!command && !shift && alt && key === "ArrowUp") {
            otterwiki_editor.table_add_row();
            event.preventDefault();
            return;
        }

        if (!command && !shift && alt && key === "ArrowDown") {
            otterwiki_editor.table_add_row();
            otterwiki_editor.table_move_row_down();
            event.preventDefault();
            return;
        }
        */

        if (command && !shift && !alt && key === 'j') {
            otterwiki_editor.table();
            event.preventDefault();
            return;
        }
    }

    if(isEditable) {
        return;
    }

    let searchQuery = document.getElementById("search-query")
    if (noModifiers && key === '/' && searchQuery != null) {
        searchQuery.focus();
        event.preventDefault();
        return;
    }

    let toggleSidebarBtn = document.getElementById("toggle-sidebar-btn");
    if (noModifiers && key === '[' && toggleSidebarBtn != null) {
        toggleSidebarBtn.click();
        event.preventDefault();
        return;
    }

    if (noModifiers && key === ']') {
        let colExtra = document.getElementById("column-extra");
        let colMain = document.getElementById("column-main");
        if (colExtra != null && colMain != null) {
            colMain.classList.toggle("col-xl-9");
            colMain.classList.toggle("col");
            colExtra.classList.toggle("col-xl-3");
            event.preventDefault();
        }
        return;
    }

    let createPageBtn = document.getElementById("create-page-btn");
    if (noModifiers && key === 'c' && createPageBtn != null) {
        event.preventDefault();
        document.getElementById("create-page-btn").click();
        return;
    }

    let editPageBtn = document.getElementById("edit-page-btn");
    if (noModifiers && key === 'e' && editPageBtn != null) {
        event.preventDefault();
        editPageBtn.click();
    }
});


let sidebar_links = document.querySelectorAll('a.sidebar-link');
let header_anchors = document.querySelectorAll('div.page > h1, div.page > h2, div.page > h3, div.page > h4, div.page > h5, div.page > h6');

document.querySelector('#content-wrapper').addEventListener('scroll', (event) => {
  if (typeof(header_anchors) != 'undefined' && header_anchors != null && typeof(sidebar_links) != 'undefined' && sidebar_links != null) {

    var viewHeight = Math.max(document.documentElement.clientHeight, window.innerHeight);
    // highlight the last scrolled-to: set everything inactive first
    sidebar_links.forEach((link, index) => {
      link.classList.remove("sidebar-active");
    });

    // then iterate backwards, on the first match highlight it and break
    // for (var i = header_anchors.length-1; i >= 0; i--) {
    for (var i = 0; i < header_anchors.length; i++) {
      if (header_anchors[i].getBoundingClientRect().y > 0 &&
          header_anchors[i].getBoundingClientRect().y < viewHeight) {
        for (var j = sidebar_links.length - 1; j>= 0; j--) {
          if (sidebar_links[j].href == header_anchors[i].getElementsByClassName("anchor")[0].href) {
            sidebar_links[j].classList.add('sidebar-active');
          }
        }
        break;
      }
    }
  }
});
