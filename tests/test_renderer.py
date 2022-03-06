#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
from otterwiki.renderer import markdown_render, markdown_get_toc


def test_basic_markdown():
    html = markdown_render("**bold** _italic_")
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html


def test_toc():
    md = """
# head 1
text
## head 1.1
text
# head 2
# head 2
    """
    html = markdown_render(md)
    toc = markdown_get_toc()
    # head 1
    assert "head 1" == toc[0][1]
    assert 1 == toc[0][2]
    assert "head-1" == toc[0][4]
    # head 1.1
    assert "head 1.1" == toc[1][1]
    assert "head-11" == toc[1][4]
    assert 2 == toc[1][2]
    # check duplicate header handling
    assert "head-2" == toc[2][4]
    assert "head-2-1" == toc[3][4]


def test_code():
    html = markdown_render(
        """```
abc
```"""
    )
    assert '<pre class="code">abc</pre>' in html
    # test highlight
    html = markdown_render(
        """```python
n = 0
```"""
    )
    assert '<div class="highlight">' in html
    # test missing lexer
    html = markdown_render(
        """```non_existing_lexer
n = 0
```"""
    )
    assert '<pre class="code">non_existing_lexer' in html


def test_latex_block():
    text = """
```math
a^2+b^2=c^2
```
"""
    html = markdown_render(text)
    assert "\\[a^2+b^2=c^2\\]" == html


def test_latex_inline():
    text = "$`a`$"
    html = markdown_render(text)
    assert "$<code>a</code>$" in html


def test_img():
    text = "![](/path/to/img.png)"
    html = markdown_render(text)
    assert 'src="/path/to/img.png"' in html

    text = '![](/path/to/img.png "title")'
    html = markdown_render(text)
    assert 'src="/path/to/img.png"' in html
    assert 'title="title"' in html
