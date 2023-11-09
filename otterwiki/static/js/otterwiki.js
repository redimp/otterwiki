/* vim: set et sts=4 ts=4 sw=4 ai: */

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
        console.log(".");
        currDisplay = ehm.style.display;
        if (ehm.style.display === "none")
        {
            ehm.style.display = "block";
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
    }
}

var MathJax = {
    tex: {
        inlineMath: [["\\(", "\\)"]],
        displayMath: [ ['\\[', '\\]'], ],
        processEscapes: true,
    }
};

