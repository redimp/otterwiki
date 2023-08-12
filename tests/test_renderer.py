#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
from otterwiki.renderer import render, preprocess_wiki_links


def test_lastword():
    lastword = render.lastword
    orig = "aaa bbb ccc"
    modified = lastword.sub(r"ddd \1", orig)
    assert modified == "aaa bbb ddd ccc"


def test_basic_markdown():
    html, toc = render.markdown("**bold** _italic_")
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html


def test_toc():
    md = """
# head 1
text
## head 1.1 **bold**
text
# head 2
# head 2
    """
    html, toc = render.markdown(md)
    # head 1
    assert "head 1" == toc[0][1]
    assert 1 == toc[0][2]
    assert "head-1" == toc[0][4]
    # head 1.1
    assert "head 1.1 <strong>bold</strong>" == toc[1][1]
    # check raw
    assert "head 1.1 bold" == toc[1][3]
    assert "head-11-bold" == toc[1][4]
    assert 2 == toc[1][2]
    # check duplicate header handling
    assert "head-2" == toc[2][4]
    assert "head-2-1" == toc[3][4]


def test_code():
    html, _ = render.markdown(
        """```
abc
```"""
    )
    assert '<pre class="code">abc</pre>' in html
    # test highlight
    html, _ = render.markdown(
        """```python
n = 0
```"""
    )
    assert '<div class="highlight">' in html
    # test missing lexer
    html, _ = render.markdown(
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
    html, _ = render.markdown(text)
    assert "\\[a^2+b^2=c^2\\]" == html


def test_latex_inline():
    text = "$`a`$"
    html, _ = render.markdown(text)
    assert "$<code>a</code>$" in html


def test_img():
    text = "![](/path/to/img.png)"
    html, _ = render.markdown(text)
    assert 'src="/path/to/img.png"' in html

    text = '![](/path/to/img.png "title")'
    html, _ = render.markdown(text)
    assert 'src="/path/to/img.png"' in html
    assert 'title="title"' in html

    text = '![alt text](/path/to/img.png "title")'
    html, _ = render.markdown(text)
    assert 'src="/path/to/img.png"' in html
    assert 'title="title"' in html
    assert 'alt="alt text"' in html


def test_html_mark():
    text = "<mark>mark</mark>"
    html, _ = render.markdown(text)
    assert "<mark>mark</mark>" in html


def test_wiki_link(req_ctx):
    text = "[[Title|Link]]"
    html, _ = render.markdown(text)
    assert '<a href="/Link">Title</a>' in html
    text = "[[Link]]"
    html, _ = render.markdown(text)
    assert '<a href="/Link">Link</a>' in html


def test_wiki_link_subspace(req_ctx):
    text = "[[Paul|people/Paul]]"
    html, _ = render.markdown(text)
    assert '<a href="/people/Paul">Paul</a>' in html


def test_wiki_link_in_table(req_ctx):
    text = """| name | date | link |
| -------- | -------- | -------- |
| John | 01/31/1996 | [[people/John]] |
| Mary |10/08/2001 | [[Mary|people/Mary]] |

[[Paul|people/Paul]]
"""
    html, _ = render.markdown(text)
    assert '<td><a href="/people/John">people/John</a></td>' in html
    assert '<a href="/people/Paul">Paul</a>' in html
    assert '<td><a href="/people/Mary">Mary</a></td>' in html


def test_preprocess_wiki_links():
    md = preprocess_wiki_links(
        """
        [[Page]]
        [[Title|Link]]"""
    )
    assert '[Page](/Page)' in md
    assert '[Page](/Page)' == preprocess_wiki_links("[[Page]]")
    assert '[Title](/Link)' == preprocess_wiki_links("[[Title|Link]]")

def test_sanitizer():
    text = """Preformatted script:

    <script>alert(1)</script>

```javascript
<script>alert(3)</script>
```
<script>alert(2)</script>

And last an onlick example:
<p onclick="alert(4)">PPPPP</p>
"""
    html, _ = render.markdown(text)
    # make sure that preformatted html stays preformatted
    assert (
        '<pre class="code">&lt;script&gt;alert(1)&lt;/script&gt;</pre>' in html
    )
    # and that highlited blocks are okay
    assert (
        '<span class=".highlight o">&lt;</span><span class=".highlight nx">script</span><span class=".highlight o">&gt;</span><span class=".highlight nx">alert</span><span class=".highlight p">(</span><span class=".highlight mf">3</span><span class=".highlight p">)</span><span class=".highlight o">&lt;</span><span class=".highlight err">/script&gt;</span>'
        in html
    )
    # but script code is removed
    assert '<script>alert(2)</script>' not in html
    # and that onlick is removed
    assert 'alert(4)' not in html
