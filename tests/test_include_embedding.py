#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

TARGET = """# Target Title
intro text

## Animals
cats and dogs

### Cats
meow

## Plants
trees
"""


def _store(storage, path, content):
    from otterwiki.helper import get_filename

    # normalise the filename the same way Page.save() does, so pages are
    # stored under the on-disk name include resolution looks them up by
    # (lowercased unless RETAIN_PAGE_NAME_CASE); otherwise the tests fail on
    # case-sensitive filesystems. See issue #563.
    filename = get_filename(path)
    storage.store(
        filename=filename,
        content=content,
        author=("Tester", "test@example.com"),
        message="test page",
    )


def _render(host_pagepath, markdown):
    """Render *markdown* as if it were the content of *host_pagepath*."""
    from otterwiki.server import app_renderer
    from otterwiki.plugins import call_hook
    from otterwiki.wiki import Page

    host = Page(pagepath=host_pagepath)
    call_hook("page_render_context", page=host, preview=False)
    html, toc, _ = app_renderer.markdown(markdown, page_url=host.page_view_url)
    return html, toc


def test_include_whole_page(req_ctx):
    from otterwiki.server import storage

    _store(storage, "Target", TARGET)
    html, _ = _render("Host", "{{include|src=/Target}}")
    assert "Target Title" in html
    assert "cats and dogs" in html
    assert "trees" in html
    assert 'class="include-embedding"' in html


def test_include_section_with_children(req_ctx):
    from otterwiki.server import storage

    _store(storage, "Target", TARGET)
    html, _ = _render("Host", "{{include|src=/Target|section=animals}}")
    assert "cats and dogs" in html
    assert "meow" in html  # the Cats sub-section is included
    assert "trees" not in html  # the Plants section is not
    assert "intro text" not in html


def test_include_section_is_slugified(req_ctx):
    from otterwiki.server import storage

    _store(storage, "Target", TARGET)
    # section=Animals (capitalised) matches the "animals" anchor
    html, _ = _render("Host", "{{include|src=/Target|section=Animals}}")
    assert "cats and dogs" in html
    # a value with spaces is slugified too
    _store(storage, "Spaced", "# Getting Started\nhello\n")
    html, _ = _render(
        "Host", "{{include|src=/Spaced|section=Getting Started}}"
    )
    assert "hello" in html


def test_include_section_without_children(req_ctx):
    from otterwiki.server import storage

    _store(storage, "Target", TARGET)
    html, _ = _render(
        "Host", "{{include|src=/Target|section=animals|children=false}}"
    )
    assert "cats and dogs" in html
    assert "meow" not in html  # sub-section excluded
    assert "trees" not in html


def test_include_section_without_heading(req_ctx):
    from otterwiki.server import storage

    _store(storage, "Target", TARGET)
    html, _ = _render(
        "Host",
        "{{include|src=/Target|section=animals"
        "|children=false|heading=false}}",
    )
    assert "cats and dogs" in html
    # the heading text is gone, only the body remains
    assert ">Animals<" not in html


def test_include_missing_page(req_ctx):
    html, _ = _render("Host", "{{include|src=/DoesNotExist}}")
    assert "Error" in html
    assert "not found" in html


def test_include_missing_section_lists_available(req_ctx):
    from otterwiki.server import storage

    _store(storage, "Target", TARGET)
    html, _ = _render("Host", "{{include|src=/Target|section=nope}}")
    assert "not found" in html
    assert "animals" in html  # available anchors are listed


def test_include_requires_src(req_ctx):
    html, _ = _render("Host", "{{include|section=animals}}")
    assert "src=" in html


def test_include_rejects_path_traversal(req_ctx):
    html, _ = _render("Host", "{{include|src=/../secret}}")
    assert "traversal" in html


def test_include_relative_resolution(req_ctx):
    from otterwiki.server import storage

    _store(storage, "Space/Target", TARGET)
    # relative src from Space/Host resolves to Space/Target
    html, _ = _render("Space/Host", "{{include|src=Target|section=plants}}")
    assert "trees" in html


def test_include_cycle_detection(req_ctx):
    from otterwiki.server import storage

    _store(storage, "Loop", "# Loop\n{{include|src=/Loop}}\n")
    html, _ = _render("Host", "{{include|src=/Loop}}")
    assert "cycle detected" in html


def test_include_does_not_clobber_host_toc(req_ctx):
    from otterwiki.server import storage

    _store(storage, "Target", TARGET)
    host_md = (
        "# Host Heading\n\n"
        "{{include|src=/Target|section=animals}}\n\n"
        "## Host Second\n"
    )
    _html, toc = _render("Host", host_md)
    anchors = [entry[4] for entry in toc]
    # the host page's own headings survive the nested include render
    assert "host-heading" in anchors
    assert "host-second" in anchors
