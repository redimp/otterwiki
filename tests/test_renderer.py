#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
from otterwiki.renderer import render, preprocess_wiki_links, clean_html


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
    assert "<h1 id=\"head-1\"" in html
    # head 1.1
    assert "head 1.1 <strong>bold</strong>" == toc[1][1]
    assert "<h2 id=\"head-11-bold\"" in html
    # check raw
    assert "head 1.1 bold" == toc[1][3]
    assert "head-11-bold" == toc[1][4]
    assert "<h2 id=\"head-11-bold\"" in html
    assert 2 == toc[1][2]
    # check duplicate header handling
    assert "head-2" == toc[2][4]
    assert "head-2-1" == toc[3][4]
    assert "<h1 id=\"head-2\"" in html
    assert "<h1 id=\"head-2-1\"" in html

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
    text = "[[Text with spaces|Link with spaces]]"
    html, _ = render.markdown(text)
    assert '<a href="/Link%20with%20spaces">Text with spaces</a>' in html


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
        [[Title|Link]]
        [[Text with space|Link with space]]
        """
    )
    assert '[Page](/Page)' in md
    assert '[Title](/Link)' in md
    assert '[Page](/Page)' == preprocess_wiki_links("[[Page]]")
    assert '[Title](/Link)' == preprocess_wiki_links("[[Title|Link]]")
    assert '[Text with space](/Link%20with%20space)' == preprocess_wiki_links(
            "[[Text with space|Link with space]]")
    assert '[Text with space](/Link%20with%20space)' == preprocess_wiki_links(
            "[[Text with space|Link%20with%20space]]")
    # make sure fragment identifier of the URL survived the parser
    assert '[Random#Title](/Random#Title)' == preprocess_wiki_links(
            "[[Random#Title]]")


def test_table_align():
    text = """
| left th     | center th     | right th  |
|:----------- |:-------------:| ---------:|
| left td     | center td     | right td  |
"""
    html, _ = render.markdown(text)
    # check header
    assert '<th style="text-align:left">left th</th>' in html
    assert '<th style="text-align:center">center th</th>' in html
    assert '<th style="text-align:right">right th</th>' in html
    # check cells
    assert '<td style="text-align:left">left td</td>' in html
    assert '<td style="text-align:center">center td</td>' in html
    assert '<td style="text-align:right">right td</td>' in html

def test_clean_html_script():
    assert clean_html("<script>") == "&lt;script&gt;"
    assert clean_html("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert clean_html('<p onclick="alert(4)">PPPPP</p>') == '&lt;p onclick=&#34;alert(4)&#34;&gt;PPPPP&lt;/p&gt;'


def test_clean_html_render():
    text = """Preformatted script:

    <script>alert(1)</script>

```javascript
<script>alert(3)</script>
```
<script>alert(2)</script>

And last an onclick example:
<p onclick="alert(4)">PPPPP</p>

<video width='80%' controls> <!-- this is updated to width="80%" -->
<source src="/mp4%20example/example.mp4" type="video/mp4">
</video>
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
    assert '<p onclick="alert(4)"' not in html
    # check multimedia
    assert "<video width='80%' controls>" in html
    assert "</video>" in html

def test_strikethrough():
    md = """
~~strike1~~
alpha bravo ~~strike2~~ charlie
~~s~t~r~i~k~e~3~~
~~strike4~~"""
    html, _ = render.markdown(md)
    assert "<del>strike1</del>" in html
    assert "<del>strike2</del>" in html
    assert "<del>strike3</del>" not in html
    assert "<del>strike4</del>" in html

def test_mark():
    md = """
==mark1==
alpha bravo ==mark2== charlie
==m=a=r=k=3==

inline code `alpha ==mark7== bravo` charlie

- alpha
- ==mark5==
- charlie

```
==mark6===
```

==mark4=="""
    html, _ = render.markdown(md)
    assert "<mark>mark1</mark>" in html
    assert "<mark>mark2</mark>" in html
    assert "<mark>mark3</mark>" not in html
    assert "<mark>mark4</mark>" in html
    assert "<mark>mark5</mark>" in html
    assert "<mark>mark6</mark>" not in html
    assert "<mark>mark7</mark>" not in html


def test_math_block():
    md = """
```math
a^2+b^2=c^2
```
multiline
```math
a=b
c=d
```
"""
    html, _ = render.markdown(md)
    assert "\\[a=b\\]" in html
    assert "\\[c=d\\]" in html
    assert "\\[a^2+b^2=c^2\\]" in html


def test_math_code_inline():
    text = "`$a$`"
    html, _ = render.markdown(text)
    assert "\\(a\\)" in html


def test_latex_inline():
    md ="""
$latex1$
Alpha bravo $latex2$ charlie

```
alpha bravo $latex4$ charlie
```

and a block

    $latex5$

and a list

- alpha
- $latex6$
- charlie

$latex3$"""

    html, _ = render.markdown(md)
    assert "\\(latex1\\)" in html
    assert "\\(latex2\\)" in html
    assert "\\(latex3\\)" in html
    assert "\\(latex4\\)" not in html
    assert "\\(latex5\\)" not in html
    assert "\\(latex6\\)" in html
