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
}
