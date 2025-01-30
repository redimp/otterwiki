/* vim: set et sts=4 ts=4 sw=4 ai: */

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
    _getSelectedLines: function() {
        const [s, e] = [cm_editor.getCursor('start').line, cm_editor.getCursor('end').line]
        return [...Array(e - s + 1).keys()].map(i => i + s);
    },
    _setLine: function(n, text) {
        cm_editor.replaceRange(
            text, { line: n, ch: 0, },
                  { line: n, ch: 999999, }
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
    _toggleBlock: function(syntax_chars, token, separate_end_chars) {
        // FIXME: with multiline blocks that include newlines in their chars, this is pretty wonky...
        if (!(syntax_chars instanceof Array)) {
            syntax_chars = [syntax_chars];
        }
        if (separate_end_chars !== undefined && !(separate_end_chars instanceof Array) ) {
            separate_end_chars = [separate_end_chars];
        } else {
            separate_end_chars = [];
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
            start_char = syntax_chars[0]
            end_char = syntax_chars[0]

            if (separate_end_chars.length) {
                end_char = separate_end_chars[0]
            }
            cm_editor.doc.replaceRange(start_char + end_char, cursor);
        } else {
            // selection that is supposed to be toggled
            const cursor_start = cm_editor.getCursor('start');
            const cursor_end = cm_editor.getCursor('end');
            var text = cm_editor.getSelection()
            // check if block starts or ends with syntax_chars/separate_end_chars
            toggle_off = false;
            for (const chars of syntax_chars) {

                // determine whether the selected block already has start & end chars
                // and which combination they are
                let start_matches = false;
                let end_matches = false;
                let end_length = 0;

                if (text.startsWith(chars)) start_matches = true;

                if (separate_end_chars.length) {
                    for (const end_char of syntax_chars) {
                        if (text.endsWith(end_char)) {
                            end_matches = true;
                            end_length = end_char.length;
                            break;
                        }
                    }
                } else {
                    if (text.endsWith(chars)) {
                        end_matches = true;
                        end_length = chars.length;
                    }
                }

                if (start_matches && end_matches) {
                    toggle_off = true;
                    // slice off syntax chars
                    text = text.slice(chars.length, text.length - end_length);
                    cm_editor.replaceSelection(text);
                    // update end cursor (start cursor is fine)
                    cursor_end.ch = cursor_end.ch - end_length;
                    // if on the same line // FIXME: Is this actually relevant? this is the same as the line above
                    if (cursor_start.line == cursor_end.line) { cursor_end.ch = cursor_end.ch - end_length; }
                    // select new area
                    cm_editor.setSelection(cursor_start, cursor_end);
                }
            }
            if (!toggle_off) {
                const end_char = separate_end_chars.length ? separate_end_chars[0] : syntax_chars[0];
                text = syntax_chars[0] + text + end_char;
                cm_editor.replaceSelection(text);
                // update end cursor (start cursor is fine)
                cursor_end.ch = cursor_end.ch + end_char.length;
                // if on the same line // FIXME: Is this actually relevant? this is the same as the line above
                if (cursor_start.line == cursor_end.line) { cursor_end.ch = cursor_end.ch + end_char.length; }
                // select new area
                cm_editor.setSelection(cursor_start, cursor_end);
            }
        }
        if (!anythingSelected) {
            if (toggle_off) {
                // FIXME: with the potentially different end chars, this will probably not work?
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
    _getState: function(pos) {
        var cm = cm_editor;
        pos = pos || cm.getCursor('start');
        var stat = cm.getTokenAt(pos);
        if (!stat.type) return {};

        var types = stat.type.split(' ');

        var ret = {},
            data, text;
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
            } else if (data.match(/^header(-[1-6])?$/)) {
                ret[data.replace('header', 'heading')] = true;
            }
        }
        return ret;
    },
    /* formating functions */
    // header: increase the mardown header level till five remove afterwards
    // TODO: refactor so that it works with quotes, too.
    header: function() {
        if (!cm_editor) { return; }
        for (const i of otterwiki_editor._getSelectedLines())
        {
            var line = cm_editor.doc.getLine(i);
            var lineHLevel = line.search(/[^#]/);
            // In case of a line composed of only "#"
            if (lineHLevel < 0) { lineHLevel = line.length; }
            if (lineHLevel == 0) {
                otterwiki_editor._setLine(i, "# " + line);
            } else if (lineHLevel < 5) {
                // add a level
                otterwiki_editor._setLine(i, "#" + line);
            } else {
                // Remove Heading
                otterwiki_editor._setLine(i, line.replace(/^#+\s*/,''));
            }
        }
        cm_editor.focus();
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
    // TODO: How do we handle multiple levels of spoilers, expands etc.?
    //       Maybe we could hijack the Tab indentation?
    spoiler: function() {
        otterwiki_editor._toggleLines(">! ", [/\s*>!\s+/], "spoiler");
    },
    expand: function() {
        // FIXME: This does seem a little hacky - it works, though...
        // add the header line first
        const first_line = otterwiki_editor._getSelectedLines()[0];
        const line = cm_editor.getLine(first_line);

        // drop the header prefix but leave any expand syntax in-place for now
        let updated_line = line.replace(/(\s*>\|\s+)?#\s+/, "$1")
        // if the re didn't alter the line, add the prefix
        if (updated_line == line) {
            updated_line = "# " + line;
        }
        otterwiki_editor._setLine(first_line, updated_line);

        // then add the expand syntax
        otterwiki_editor._toggleLines(">| ", [/\s*>\|\s+/], "expand");
    },
    code: function() {
        otterwiki_editor._toggleBlock(["`","```"], "code");
    },
    quote: function () {
        otterwiki_editor._toggleLines("> ", [/\s*>\s+/], "quote")
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
    img: function(img = "![]()") {
        if (!cm_editor) { return; }
        state = otterwiki_editor._getState();
        // we don't mess with existing tokens of these kinds
        if (state.img || state.link) { return; }

        const link = img;

        var text = cm_editor.getSelection();
        cm_editor.replaceSelection(text + link);

        cm_editor.focus();
    },
    link: function(text = "description", url = "https://") {
        if (!cm_editor) { return; }
        state = otterwiki_editor._getState();
        // we don't mess with existing tokens of these kinds
        if (state.img || state.link) { return; }

        const link = "[" + text + "](" + url + ")";

        var text = cm_editor.getSelection();
        cm_editor.replaceSelection(text + link);

        cm_editor.focus();
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
        var filename = element.value.split("/--/")[0];
        var url = element.value.split("/--/")[1];
        var thumbnail_url = element.value.split("/--/")[2];
        if (thumbnail_url == '') {
            // empty preview box
            document.getElementById("extranav-preview").innerHTML = "";
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
            var preview_img = document.createElement("img");
            preview_img.setAttribute("src", thumbnail_url);
            preview_img.setAttribute("alt", filename);
            document.getElementById("extranav-preview").appendChild(preview_img);
            // update options
            document.getElementById("attachment-image").disabled = false;
            document.getElementById("attachment-thumbnail").disabled = false;
        }
    },
    insert_attachment: function() {
        var element = document.getElementById("attachment-filename");
        if (typeof(element) == 'undefined' || element == null) { return; }
        // split value in filename, url and thumbnail_url
        var filename = element.value.split("/--/")[0];
        var url = element.value.split("/--/")[1];
        var thumbnail_url = element.value.split("/--/")[2];
        var attachment_type = document.querySelector("input[type='radio'][name=attachment-type]:checked").value;
        if (typeof(attachment_type) == 'undefined' || attachment_type == null || attachment_type == '') { attachment_type = "link"; }
        // handle relative and absolute paths
        var attachment_absolute = document.getElementById("attachment-absolute").checked;
        if (typeof(attachment_absolute) == 'undefined' || attachment_absolute == null || attachment_absolute == '') { attachment_absolute = false; }
        if (!attachment_absolute) {
            url = "./" + url.split("/").slice(-1)[0];
            thumbnail_url = "./" + thumbnail_url.split("/").slice(-1)[0];
        }

        if (attachment_type == "image") {
            otterwiki_editor.img('![]('+url+')\n');
        } else if (attachment_type == "thumbnail") {
            otterwiki_editor.img('[![]('+thumbnail_url+')]('+url+')\n');
        } else { // link
            otterwiki_editor.img('['+filename+']('+url+')\n');
        }
        // [![]({{f.thumbnail_url}})]({{f.url}})
    },
    insert_wikilink: function() {
        var element = document.getElementById("wikilink");
        if (typeof(element) == 'undefined' || element == null) { return; }
        // split value in filename, url and thumbnail_url
        var page = element.value.split("//")[0];
        if (typeof(page) == 'undefined' || page == null || page == '') { return; }
        otterwiki_editor.img('[['+page+']]\n');
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
window.addEventListener("keypress", function() {
    var isInputElement = event.srcElement instanceof HTMLInputElement;
    var isTextAreaElement = event.srcElement instanceof HTMLTextAreaElement;

    if(isInputElement || isTextAreaElement) {
        return;
    }

	if (document.getElementById("search-query") != null && event.key === '/') {
        document.getElementById("search-query").focus();
        event.preventDefault();
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
