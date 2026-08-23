#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
Markdown utilities for An Otter Wiki.

Splits a markdown document into sections that are keyed by heading anchor.
The anchors are generated the same way
``otterwiki.renderer.OtterwikiMdRenderer.heading`` generates them, so a
section can be queried by the very slug that is used for heading links and
``[[WikiLink#anchor]]`` fragments, independent of the heading level.

This module is intentionally free of any Flask/rendering dependency (it only
imports :func:`otterwiki.util.slugify`) so that it can be unit tested in
isolation. It is used by the ``{{include}}`` embedding to transclude a single
section of a page.

Heading detection is line based and aware of

- a leading YAML frontmatter block (``---`` ... ``---``),
- fenced code blocks (```` ``` ```` and ``~~~``), so ``#`` inside code is
  never mistaken for a heading,

and understands both ATX headings (``# Heading``) and setext headings
(a text line underlined with ``===`` or ``---``).
"""

import re
from dataclasses import dataclass
from typing import Callable, List, Optional

from otterwiki.util import slugify

__all__ = [
    "Section",
    "parse_sections",
    "extract_section",
    "list_anchors",
]

# a fenced code block opener/closer, e.g. ``` or ~~~~ with an optional info
# string; up to three leading spaces are allowed per CommonMark.
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
# an ATX heading: 1-6 hashes, optional title, optional closing hashes
_ATX_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
# a trailing closing sequence of an ATX heading (`` ## Heading ## ``)
_ATX_TRAILING_RE = re.compile(r"[ \t]+#+[ \t]*$")
# a setext underline: a line consisting solely of ``=`` (h1) or ``-`` (h2)
_SETEXT_UNDERLINE_RE = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
_BLANK_RE = re.compile(r"^[ \t]*$")

# inline constructs that need reducing to their visible text before slugifying,
# so that the anchor matches the rendered heading (which slugifies the text
# after inline markdown has been rendered and html tags stripped).
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
_CODESPAN_RE = re.compile(r"`+")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
# emphasis underscores at word boundaries (``_em_`` / ``__strong__``); intra
# word underscores (``snake_case``) are left untouched, matching mistune.
_EMPH_US_OPEN_RE = re.compile(r"(?<!\w)_{1,3}(?=\S)")
_EMPH_US_CLOSE_RE = re.compile(r"(?<=\S)_{1,3}(?!\w)")


def _wikilink_text(match: "re.Match[str]") -> str:
    """Return the visible text of a ``[[target|title]]`` / ``[[target]]``.

    Mirrors the default WIKILINK_STYLE where the part before the ``|`` is the
    visible text; the ``#fragment`` is dropped. This is best effort - wiki
    links inside headings are rare.
    """
    inner = match.group(1)
    left = inner.split("|", 1)[0]
    return left.split("#", 1)[0]


def _inline_to_text(text: str) -> str:
    """Reduce inline markdown in a heading to its visible plain text."""
    # an image renders to an <img> tag; its alt lives in an attribute, so it
    # contributes no visible text and is dropped (matching the renderer).
    text = _IMAGE_RE.sub("", text)
    text = _LINK_RE.sub(r"\1", text)
    text = _WIKILINK_RE.sub(_wikilink_text, text)
    text = _CODESPAN_RE.sub("", text)
    text = _HTML_TAG_RE.sub("", text)
    text = _EMPH_US_OPEN_RE.sub("", text)
    text = _EMPH_US_CLOSE_RE.sub("", text)
    return text


def default_anchor(raw_title: str) -> str:
    """Base anchor (without de-duplication) for a raw markdown heading title.

    slugify() strips the remaining emphasis/mark markers (``*``, ``~``, ``=``)
    as non-word characters, so only the constructs reduced above need explicit
    handling here.
    """
    return slugify(_inline_to_text(raw_title))


@dataclass
class Section:
    level: int  #: heading level, 1..6
    title: str  #: heading text reduced to visible plain text
    anchor: str  #: de-duplicated anchor slug, matching the renderer
    start: int  #: line index of the heading (setext: the text line)
    body_start: int  #: first line index after the heading/underline


def _find_headings(lines: List[str]):
    """Yield ``(start, body_start, level, raw_title)`` for each heading.

    ``start`` is the heading line (for setext: the text line above the
    underline), ``body_start`` is the first line of the section body.
    """
    headings = []
    n = len(lines)

    # skip a leading YAML frontmatter block
    start_idx = 0
    if n > 0 and lines[0].strip() == "---":
        for j in range(1, n):
            if lines[j].strip() == "---":
                start_idx = j + 1
                break

    fence = None  # (char, length) while inside a fenced code block
    # first line that a setext paragraph may reach back to; advanced past every
    # heading so a setext underline cannot swallow a previous heading's lines.
    boundary = start_idx
    i = start_idx
    while i < n:
        line = lines[i]

        # fenced code block handling
        if fence is None:
            m = _FENCE_RE.match(line)
            if m:
                marker = m.group(1)
                fence = (marker[0], len(marker))
                i += 1
                continue
        else:
            stripped = line.strip()
            if (
                stripped
                and set(stripped) == {fence[0]}
                and len(stripped) >= fence[1]
            ):
                fence = None
            boundary = i + 1
            i += 1
            continue

        # ATX heading
        m = _ATX_RE.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2) or ""
            title = _ATX_TRAILING_RE.sub("", title).strip()
            headings.append((i, i + 1, level, title))
            boundary = i + 1
            i += 1
            continue

        # setext heading: this line is an underline of the preceding paragraph.
        # The whole preceding paragraph (all consecutive non-blank lines) is
        # turned into the heading, matching the renderer.
        m = _SETEXT_UNDERLINE_RE.match(line)
        if m and i > start_idx:
            underline = m.group(1)
            j = i - 1
            while (
                j >= boundary
                and not _BLANK_RE.match(lines[j])
                and not _ATX_RE.match(lines[j])
                and not _FENCE_RE.match(lines[j])
            ):
                j -= 1
            text_start = j + 1
            if text_start <= i - 1:
                title = " ".join(
                    lines[k].strip() for k in range(text_start, i)
                )
                level = 1 if underline[0] == "=" else 2
                headings.append((text_start, i + 1, level, title))
                boundary = i + 1
                i += 1
                continue

        i += 1

    return headings


def parse_sections(
    markdown: str,
    anchor_func: Optional[Callable[[str], str]] = None,
) -> List[Section]:
    """Parse *markdown* into a flat, document-ordered list of :class:`Section`.

    Anchors are de-duplicated exactly like the renderer: the first occurrence
    of a slug keeps it, the next become ``slug-1``, ``slug-2`` and so on.
    """
    if anchor_func is None:
        anchor_func = default_anchor
    lines = markdown.split("\n")
    counts: dict[str, int] = {}
    sections: List[Section] = []
    for start, body_start, level, raw_title in _find_headings(lines):
        base = anchor_func(raw_title)
        if base in counts:
            counts[base] += 1
            anchor = f"{base}-{counts[base]}"
        else:
            counts[base] = 0
            anchor = base
        sections.append(
            Section(
                level=level,
                title=_inline_to_text(raw_title).strip(),
                anchor=anchor,
                start=start,
                body_start=body_start,
            )
        )
    return sections


def list_anchors(
    markdown: str,
    anchor_func: Optional[Callable[[str], str]] = None,
) -> List[str]:
    """Return the anchors of all sections, in document order."""
    return [s.anchor for s in parse_sections(markdown, anchor_func)]


def extract_section(
    markdown: str,
    anchor: str,
    include_children: bool = True,
    include_heading: bool = True,
    anchor_func: Optional[Callable[[str], str]] = None,
) -> Optional[str]:
    """Return the markdown of the section identified by *anchor*.

    The section runs from its heading to the start of the next heading of a
    level less than or equal to the target (``include_children=True``) or to
    the next heading of any level (``include_children=False``); otherwise to
    the end of the document. With ``include_heading=False`` the heading line
    itself is omitted. Returns ``None`` if no section matches *anchor*.
    """
    lines = markdown.split("\n")
    sections = parse_sections(markdown, anchor_func)

    idx = next((i for i, s in enumerate(sections) if s.anchor == anchor), None)
    if idx is None:
        return None
    target = sections[idx]

    end = len(lines)
    for nxt in sections[idx + 1 :]:
        if include_children:
            if nxt.level <= target.level:
                end = nxt.start
                break
        else:
            end = nxt.start
            break

    start = target.start if include_heading else target.body_start
    chunk = lines[start:end]
    while chunk and chunk[-1].strip() == "":
        chunk.pop()
    return "\n".join(chunk)
