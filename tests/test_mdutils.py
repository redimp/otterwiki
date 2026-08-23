#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest

from otterwiki.renderer import render
from otterwiki.mdutils import (
    parse_sections,
    extract_section,
    list_anchors,
)


def renderer_anchors(md):
    """The anchors the actual renderer generates, in document order."""
    _, toc, _ = render.markdown(md)
    return [entry[4] for entry in toc]


# --- anchor generation -----------------------------------------------------


def test_anchors_basic():
    md = "# Head 1\ntext\n## Head One\ntext\n"
    assert list_anchors(md) == ["head-1", "head-one"]
    assert list_anchors(md) == renderer_anchors(md)


def test_anchor_dedup_matches_renderer():
    md = "# head 2\n# head 2\n# head 2\n"
    assert list_anchors(md) == ["head-2", "head-2-1", "head-2-2"]
    assert list_anchors(md) == renderer_anchors(md)


@pytest.mark.parametrize(
    "md",
    [
        "# head 1\ntext\n## head 1.1 **bold**\ntext\n# head 2\n# head 2\n",
        "# A `code` heading\n",
        "## A [link](https://example.com) here\n",
        "### An ![img](/x.png) title\n",
        "# _emphasis_ word\n",
        "# snake_case stays\n",
        "# Ünïcödé Heading\n",
        "Setext One\n==========\ntext\nSetext Two\n----------\n",
    ],
)
def test_anchor_parity_with_renderer(md):
    assert list_anchors(md) == renderer_anchors(md)


# --- section structure -----------------------------------------------------


def test_parse_sections_levels_and_order():
    md = "# One\na\n## Two\nb\n### Three\nc\n# Four\nd\n"
    sections = parse_sections(md)
    assert [(s.level, s.anchor) for s in sections] == [
        (1, "one"),
        (2, "two"),
        (3, "three"),
        (1, "four"),
    ]


def test_setext_headings_detected():
    md = "Title H1\n========\n\nbody\n\nTitle H2\n--------\n\nbody\n"
    sections = parse_sections(md)
    assert [(s.level, s.anchor) for s in sections] == [
        (1, "title-h1"),
        (2, "title-h2"),
    ]
    assert list_anchors(md) == renderer_anchors(md)


def test_setext_underline_uses_whole_preceding_paragraph():
    # consecutive non-blank lines form one paragraph that the underline turns
    # into a single heading, matching the renderer
    md = "line one\nline two\n=========\ntext\n"
    assert list_anchors(md) == ["line-one-line-two"]
    assert list_anchors(md) == renderer_anchors(md)


def test_thematic_break_is_not_a_setext_heading():
    # a --- preceded by a blank line is a horizontal rule, not a heading
    md = "some text\n\n---\n\nmore text\n"
    assert parse_sections(md) == []


def test_headings_inside_code_fence_ignored():
    md = "# Real\n```\n# Not a heading\n```\ntext\n"
    assert list_anchors(md) == ["real"]


def test_frontmatter_delimiters_ignored():
    md = "---\ntitle: Foo\n---\n# Real Heading\ntext\n"
    assert list_anchors(md) == ["real-heading"]


# --- extraction ------------------------------------------------------------


def test_extract_section_with_children():
    md = "# One\na\n## Sub\nb\n# Two\nc\n"
    out = extract_section(md, "one")
    assert out == "# One\na\n## Sub\nb"


def test_extract_section_without_children():
    md = "# One\na\n## Sub\nb\n# Two\nc\n"
    out = extract_section(md, "one", include_children=False)
    assert out == "# One\na"


def test_extract_section_without_heading():
    md = "# One\na\nb\n# Two\nc\n"
    out = extract_section(md, "one", include_heading=False)
    assert out == "a\nb"


def test_extract_deeper_section_stops_at_same_level():
    md = "# One\na\n## A\naa\n## B\nbb\n# Two\nc\n"
    assert extract_section(md, "a") == "## A\naa"
    assert extract_section(md, "b") == "## B\nbb"


def test_extract_last_section_runs_to_eof():
    md = "# One\na\n# Two\nb\nc\n"
    assert extract_section(md, "two") == "# Two\nb\nc"


def test_extract_by_deduplicated_anchor():
    md = "# Dup\nfirst\n# Dup\nsecond\n"
    assert extract_section(md, "dup") == "# Dup\nfirst"
    assert extract_section(md, "dup-1") == "# Dup\nsecond"


def test_extract_missing_section_returns_none():
    md = "# One\na\n"
    assert extract_section(md, "does-not-exist") is None


def test_level_independent_lookup():
    # the same slug is queried the same way regardless of heading level
    md = "# top\na\n#### animals\ndeep\n"
    assert extract_section(md, "animals") == "#### animals\ndeep"
