## User Guide

### Editing and creating pages

You can edit an existing page using the <span class="btn btn-primary btn-sm btn-hlp"><i class="fas fa-pencil-alt"></i></span> at the top right of the page. If the button is missing, you lack the permissions to edit the page. However, you are still able to view the source code using <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="fab fa-markdown"></i></span> View Source</span>.

To create a page use the <span class="help-button"><span class="btn btn-square btn-sm"><i class="far fa-file"></i></span> Create page</span> button. Next, you have to pick a name for the page you want to create. To help you organize your page structure, buttons provide shortcuts to add the path to recently visited pages and directories. **Please note:** The name of the page will be sanitized; `?$.#\` and trailing slashes `/` will be removed. See below on how to create pages in [Subdirectories](#subdirectories). After submitting the form, the new page is opened in the editor. In case of the page already existing, the existing page will be opened.

You can preview your changes using <span class="btn btn-primary btn-sm btn-hlp"><i class="far fa-eye"></i></span>. Either while editing or from previewing the article your changes can be committed via <span class="btn btn-success btn-sm btn-hlp"> <i class="fas fa-save"></i></span>. This will open a modal where you can enter a commit message. To discard your changes use <span class="btn btn-danger btn-sm btn-hlp" style="border: None;" role="button"><i class="fas fa-window-close"></i></span> and return to the view of the page.

#### General Shortcuts

| Operation      | Linux, Windows,<br>MacOS |
|----------------|:-------------------:|
| Create page    | <kbd>c</kbd>        |
| Edit page      | <kbd>e</kbd>        |
| Toggle sidebar | <kbd>[</kbd>        |
| Toggle sidebar (right) | <kbd>]</kbd>        |
| Search         | <kbd>/</kbd>        |

#### Editor Shortcuts


| Operation     | Linux, Windows                | MacOS                       |
|---------------|------------------------------|-----------------------------|
| Save          | <kbd>Ctrl</kbd>-<kbd>S</kbd> | <kbd>Cmd</kbd>-<kbd>S</kbd> |
| Toggle preview | <kbd>Ctrl</kbd>-<kbd>P</kbd> | <kbd>Cmd</kbd>-<kbd>P</kbd> |
| Search        | <kbd>Ctrl</kbd>-<kbd>F</kbd> | <kbd>Cmd</kbd>-<kbd>F</kbd> |
| Find next     | <kbd>Ctrl</kbd>-<kbd>G</kbd> | <kbd>Cmd</kbd>-<kbd>G</kbd> |
| Find previous | <kbd>Shift</kbd>-<kbd>Ctrl</kbd>-<kbd>G</kbd> | <kbd>Shift</kbd>-<kbd>Cmd</kbd>-<kbd>G</kbd> |
| Replace       | <kbd>Shift</kbd>-<kbd>Ctrl</kbd>-<kbd>F</kbd> | <kbd>Cmd</kbd>-<kbd>Option</kbd>-<kbd>F</kbd> |
| Replace all   | <kbd>Shift</kbd>-<kbd>Ctrl</kbd>-<kbd>R</kbd> | <kbd>Shift</kbd>-<kbd>Cmd</kbd>-<kbd>Option</kbd>-<kbd>F</kbd> |


To make formatting easier the following shortcuts are available:


|                     | Linux, Windows                | MacOS                       |
|---------------------|-------------------------------|-----------------------------|
| Bold                | <kbd>Ctrl</kbd>-<kbd>B</kbd>  | <kbd>Cmd</kbd>-<kbd>B</kbd> |
| Italic              | <kbd>Ctrl</kbd>-<kbd>I</kbd>  | <kbd>Cmd</kbd>-<kbd>I</kbd> |
| Strike through      | <kbd>Shift</kbd>-<kbd>Ctrl</kbd>-<kbd>S</kbd> | <kbd>Shift</kbd>-<kbd>Cmd</kbd>-<kbd>S</kbd> |
| Link                | <kbd>Ctrl</kbd>-<kbd>K</kbd>  | <kbd>Cmd</kbd>-<kbd>K</kbd> |
| Insert/Format Table | <kbd>Ctrl</kbd>-<kbd>J</kbd>  | <kbd>Cmd</kbd>-<kbd>J</kbd> |


#### Page history

You can view the history of a page with <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="far fa-file-alt"></i></span> History</span>. All edits of the page will be listed in order. The date of the commit, the Author and the commit message are displayed.

**Comparing revisions:** Select the two revisions to compare and hit <span class="btn btn-primary btn-sm btn-hlp">Compare Revisions</span>. The diff will be displayed.

**View revision:** You can open every revision using the date <span class="help-button"><a href="#">YYYY-MM-DD hh:mm</a></span> link in the history.

**Display a single commit:** You can view a single commit using the revision
link, e.g. <span class="help-button"><a href="#" x class="btn revision-small">012abc</a></span>

**Revert a commit:** You can revert a commit using the <span class="help-button"><a hre="#"><i class="fas fa-undo"></i></a></span> link in the history. This will create a revert commit.

#### Page blame

Using <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="fas fa-people-arrows"></i></span> Blame</span> you can display the source of a page having each line annotated with information about the revision that last modified the line and the author of the commit.

**View revision**: You can open every revision using the date
<span class="help-button"><a href="#">YYYY-MM-DD HH:mm</a></span> link of the line.

**Display a single commit**: You can view the state of the page when a specific
commit was made using the revision link of the line, e.g. <span class="help-button"><a href="#" x class="btn revision-small">012abc</a></span>.

#### Page rename

You can rename a page using <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="fas fa-edit"></i></span> Rename</span>. For renaming, the same rules as for [creating pages](#editing-and-creating-pages) apply.

Attachments will be moved with the renamed page.

#### Page delete

A page (with all its attachments) can be deleted with <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="far fa-trash-alt"></i></span> Delete</span>. Please note: This deletion can be reverted. An Otter Wiki never makes the repository forget.

#### Page name

The page name can be anything that can be stored in the file system, with some sanitization: `?$.#\` and trailing slashes `/` will be removed.
Since all pages are stored in all lowercase filenames, the capitalization of the page name is determined by the first header.

Note: When `RETAIN_PAGE_NAME_CASE` is enabled, the capitalization of the filename determines the capitalization of the page name.

---

### Attachments

Attachments to pages can be created in two ways. First you can access the attachments of the current page
using
<span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="fa fa-paperclip"></i></span> Attachments</span>. Second, while editing a page, you can simply paste an image into the editor.
The pasted image will be uploaded and attached to the page you are editing.

#### Editing attachments

Open the attachment menu via <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="fa fa-paperclip"></i></span> Attachments</span>.
In addition to uploading, each attachment can also be opened via the <span class="help-button"><a hre="#"><i class="fas fa-edit"></i></a></span> for editing, which allows you to replace, rename or delete the attachment. The history of the attachment is displayed and offers the possibility to revert changes using <span class="help-button"><a hre="#"><i class="fas fa-undo"></i></a></span>.

#### Inline attached images

To inline images in pages use the markdown syntax: `![](/Page/attachment.jpg)`.

On larger screens, a list of recently used attachments appears on the right. From this list, you can select an attachment and choose how to use it. Then, utilize the copy icon (<span class="help-button"><a href="#" class="btn btn-xsm"><i class="fas fa-copy"></i></a></span>) to insert the corresponding markdown code into the editor.

##### Thumbnails and Image Resizing

To generate a scaled-down version of an attached image, append `?thumbnail`
to the image URL. For example: `![](/page/attachment.jpg?thumbnail)`.

By default, thumbnails are scaled to a maximum size of 80x80 pixels. You can
customize this size by adding a number to the `?thumbnail` option. For instance,
`?thumbnail=400` will scale the image so that its longest side is no larger than
400 pixels, maintaining the aspect ratio.

**Important:** Thumbnails are *never* scaled up.

For more precise control over image scaling, use the `?height=` or `?width=`
parameters. These allow you to specify the desired height or width,
respectively.  The aspect ratio will be preserved unless both `?width=` and
`?height=` are specified.

---

### Search

The search covers the content of all pages in the most recent commit. The
results are ranked by the number of hits. Matching page names will be
prioritized. For each page a brief summary of the matching part will be
displayed.

<p>The search is by default not case-sensitive. Case-sensitivity can be enabled with
<span class="help-button"><input type="checkbox" style="display:inline;" id="is_casesensitive" checked>
Match case </span>.</p>

<p>For more complex searches you can make use of regular expressions. Enable
these with <span class="help-button"><input type="checkbox" style="display:inline;" id="is_regexp" checked>
Regular expression</span>. For case-sensitive regex searches enable both <em>Match
case</em> and <em>Regular expression</em>.</p>

---

### Page index

An overview about all pages is given by the Page index, you can open it with
<span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-list"></i></span> A-Z</span> from the left sidebar. All listed pages are sorted by page name and
grouped by their first letter.

To list the headings of all pages use the toggle on top of the page:
<div class="d-inline-block custom-switch font-size-12 btn-hlp" style="border-radius: 0.5rem; background-color: rgba(100, 100, 100, 0.1);">
  <input type="checkbox" id="switch-headings" value="">
  <label for="switch-headings">Toggle page headings</label>
</div>

This may make the Page index look convoluted.

---

### Changelog

The Changelog <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="fas fa-history"></i></span> Changelog</span> displays all commits that have been
made in the wiki. Each and every change to pages or their attachments are stored
as commits.

**View revision**: You can open each page in the state listed using the links in
the **File** column.

**Display a single commit**: You can show the state of the page when a specific
commit was made by using the revision link in the line, e.g. <span class="help-button"><a href="#" x class="btn revision-small">012abc</a></span>.

**Revert a commit:** You can revert a commit using the <span class="help-button"><a hre="#"><i class="fas fa-undo"></i></a></span> link in the history. This will create a revert commit.

---

### Subdirectories

You can create a page in a subdirectory by placing the name of the subdirectory
before the page name separated by a slash. For example: `Subdirectory/Page`.
For a better overview, a subdirectory has its own Page index.

Subdirectories can have subdirectories. The limit is given by git and the
underlying file system. Given normal, human usage, hitting those limits is highly unlikely.

---


[modeline]: # ( vim: set fenc=utf-8 spell spl=en sts=4 et tw=80: )
