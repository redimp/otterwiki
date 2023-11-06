## User Guide

### Editing and creating pages

You can edit an existing page use the <span class="btn btn-primary btn-sm btn-hlp"><i class="fas fa-pencil-alt"></i></span> on the top right. If the button is missing, you lack the permissions to edit the page. You can still look at the source code, using <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="fab fa-markdown"></i></span> View Source</span>, though.

To create a page using the <span class="help-button"><span class="btn btn-square btn-sm"><i class="far fa-file"></i></span> Create page</span> button. Next you have to pick a name for the page you want to create. **Please note:** The name of a page will be sanitized; `?$.#\` and trailing slashes `/` will be removed. See below how to create pages in [Subdirectories](#subdirectories). After submitting the form the new page is opened in the editor, in case the page already exists, the existing page will be opened.

You can preview your changes using <span class="btn btn-primary btn-sm btn-hlp"><i class="far fa-eye"></i></span> either while editing or from the preview you can save and commit your changes with <span class="btn btn-success btn-sm btn-hlp"> <i class="fas fa-save"></i></span>. This will open a modal where you can enter a commit message. To discard your changes use <span class="btn btn-danger btn-sm btn-hlp" style="border: None;" role="button"><i class="fas fa-window-close"></i></span> and return to the view of the page.

#### Page history

You can show the history of a page with <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="far fa-file-alt"></i></span> History</span>. Here are the edits that were made listed in order. The date of the commit, the Author and the commit message are displayed.

**Comparing revisions:** Select the two revisions to compare and hit <span class="btn btn-primary btn-sm btn-hlp">Compare Revisions</span>. The diff will be displayed.

**View revision:** You can open every revision using the date <span class="help-button"><a href="#">YYYY-MM-DD hh:mm</a></span> link in the history.

**Display a single commit:** You can show a single commit using the revision
link, e.g. <span class="help-button"><a href="#" x class="btn revision-small">012abc</a></span>

**Revert a commit:** You can revert a commit using the <span class="help-button"><a hre="#"><i class="fas fa-undo"></i></a></span> link in the history. This will create a revert commit.

#### Page blame

Using <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="fas fa-people-arrows"></i></span> Blame</span> you can display the source of a page, with each line annotated with information about the revision that last modified the line and the author of the commit.

**View revision**: You can open every revision using the date
<span class="help-button"><a href="#">YYYY-MM-DD HH:mm</a></span> link of the line.

**Display a single commit**: You can show the state of the page when a specific
commit was made revision link in the line, e.g. <span class="help-button"><a href="#" x class="btn revision-small">012abc</a></span>.

#### Page rename

You can rename a page using <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="fas fa-edit"></i></span> Rename</span>. For renaming the same rules apply as for [creating pages](#creating-and-editing-pages).

Attachments will moved with the renamed page.

#### Page delete

A page (with all it's attachments) can be deleted with <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="far fa-trash-alt"></i></span> Delete</span>. Please note, that this deletion can be reverted. An Otter Wiki never makes the repository forget.

---

### Attachments

Attachments to pages can be created in two ways. First you can access the attachments of the current page
using
<span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="fa fa-paperclip"></i></span> Attachments</span>. Second while editing a page you can simply paste an image into the editor.
The pasted image will be uploaded and attached to the page you are editing.

#### Editing attachments

Open the attachment menu via <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="fa fa-paperclip"></i></span> Attachments</span>. 
In addition to uploading, you can here also open each attachment via the <span class="help-button"><a hre="#"><i class="fas fa-edit"></i></a></span> for editing, which allows you to replace, rename or delete the attachment. The history of the attachment is displayed and offers the possibility to revert changes using <span class="help-button"><a hre="#"><i class="fas fa-undo"></i></a></span>.

#### Inline attached images

To inline images in pages use the markdown syntax: `![](/Page/attachment.jpg)`.
On large screens, the editor displays a list of the most recent attachments on the
right hand side. There you can use <span class="help-button"><a href="#" class="btn btn-xsm"><i class="fas fa-copy"></i> Copy</a></span> to copy the markdown code to your clipboard
and paste it in the editor. On the attachment page, you find the markdown codes
when opening the pop-up using via <span class="help-button"><a hre="#"><i class="fas fa-copy"></i></a></span> next to the <span class="help-button"><a href="#">filename.jpg</a></span>.

##### Thumbnails

Adding `?thumbnail` to the URL of an attachment, e.g. `![](/Page/attachment.jpg?thumbnail)`
you get a scaled down version of the attached image. Per default the image is scaled down to an
image with maximum size of 80x80. You can configure the maximum size by adding
an number to the option, e.g. `?thumbnail=400` will scale the image
symmetrically so that the longest side is not larger than 400 pixels. Thumbnails are
never scaled up.

---

### Search

The search covers the content of all pages in the most recent commit. The
results are ranked by the number of hits, matching page names will be
prioritized. For each page a brief summary of the matching part will be
displayed.

<p>The search is by default not case sensitive, this can be enabled with
<span class="help-button"><input type="checkbox" style="display:inline;" id="is_casesensitive" checked>
Match case </span>.</p>

<p>For more complex searches you can make use of regular expressions. Enable
this with <span class="help-button"><input type="checkbox" style="display:inline;" id="is_regexp" checked>
Regular expression</span>. For case sensitive regex searches enable both <em>Match
case</em> and <em>Regular expression</em>.</p>

### Page index

An overview about all pages is given by the Page index, you can open it with
<span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-list"></i></span> A-Z</span> from the left sidebar. All pages are listed, sorted by page name and 
grouped by their first letter.

To list the headings of all pages use the toggle on top of the page:
<div class="d-inline-block custom-switch font-size-12 btn-hlp" style="border-radius: 0.5rem; background-color: rgba(100, 100, 100, 0.1);">
  <input type="checkbox" id="switch-headings" value="">
  <label for="switch-headings">Toggle page headings</label>
</div>

This can make the Page index look convoluted.

### Changelog

The Changelog <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="fas fa-history"></i></span> Changelog</span> displays all commits that have been
made in the wiki. Each and every change to pages or their attachments are stored
as commits.

**View revision**: You can open each page in the state listed using the links in
the **File** column.

**Display a single commit**: You can show the state of the page when a specific
commit was made revision link in the line, e.g. <span class="help-button"><a href="#" x class="btn revision-small">012abc</a></span>.

**Revert a commit:** You can revert a commit using the <span class="help-button"><a hre="#"><i class="fas fa-undo"></i></a></span> link in the history. This will create a revert commit.

---

### Subdirectories

You can create a page in a subdirectory by placing the name of the subdirectory
before the page name, separated by a slash, for example `Subdirectory/Page`.
For a better overview has a subdirectory it's own Page index.

Subdirectories can have subdirectories. The limit is given by git and the
underlying file system. No limit that would be touched during human use.

---


[modeline]: # ( vim: set fenc=utf-8 spell spl=en sts=4 et tw=80: )
