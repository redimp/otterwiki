/* vim: set et sts=4 ts=4 sw=4 ai: */
/* Editor functions (otterwiki_editor) moved to cm6-bundle.min.js */

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
    let inCodeMirror = document.getElementsByClassName("cm-editor");
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
    if (!(command || alt) && key === '/' && searchQuery != null) {
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
          if (header_anchors[i].getElementsByClassName("anchor").length == 0) continue;
          if (sidebar_links[j].href == header_anchors[i].getElementsByClassName("anchor")[0].href) {
            sidebar_links[j].classList.add('sidebar-active');
          }
        }
        break;
      }
    }
  }
});
