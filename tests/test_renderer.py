#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
from bs4 import BeautifulSoup
from otterwiki.renderer import (
    render,
    clean_html,
    OtterwikiRenderer,
    pygments_render,
)


def test_lastword():
    lastword = render.lastword
    orig = "aaa bbb ccc"
    modified = lastword.sub(r"ddd \1", orig)
    assert modified == "aaa bbb ddd ccc"


def test_basic_markdown():
    html, toc, _ = render.markdown("**bold** _italic_")
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
    html, toc, _ = render.markdown(md)
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
    html, _, _ = render.markdown(
        """```
abc
```"""
    )
    pre_code = BeautifulSoup(html, "html.parser").find(
        'pre', {'class': 'code'}
    )
    assert pre_code is not None
    assert 'abc' in pre_code.text
    # test highlight
    html, _, _ = render.markdown(
        """```python
n = 0
```"""
    )
    assert '<div class="highlight">' in html
    pre_code = BeautifulSoup(html, "html.parser").find('pre')
    assert pre_code is not None
    assert pre_code.text.startswith('n = 0')
    # test missing lexer
    html, _, _ = render.markdown(
        """```non_existing_lexer
n = 0
```"""
    )
    pre_code = BeautifulSoup(html, "html.parser").find(
        'pre', {'class': 'code'}
    )
    assert pre_code is not None
    assert pre_code.text.startswith('non_existing_lexer')
    # test highlight with line numbers
    html, _, _ = render.markdown(
        """```python=
n = 2
```"""
    )
    assert '<table class="highlighttable">' in html
    table_code = BeautifulSoup(html, "html.parser").find(
        'table', attrs={"class": "highlighttable"}
    )
    assert table_code is not None
    td_linenos = table_code.find(
        "td", attrs={"class": "linenos"}
    )  # pyright: ignore
    assert td_linenos is not None
    assert td_linenos.text.startswith('1')
    td_code = table_code.find("td", attrs={"class": "code"})  # pyright: ignore
    assert td_code is not None
    assert td_code.text.startswith('n = 2')


def test_img():
    text = "![](/path/to/img.png)"
    html, _, _ = render.markdown(text)
    assert 'src="/path/to/img.png"' in html

    text = '![](/path/to/img.png "title")'
    html, _, _ = render.markdown(text)
    assert 'src="/path/to/img.png"' in html
    assert 'title="title"' in html

    text = '![alt text](/path/to/img.png "title")'
    html, _, _ = render.markdown(text)
    assert 'src="/path/to/img.png"' in html
    assert 'title="title"' in html
    assert 'alt="alt text"' in html


def test_html_mark():
    text = "<mark>mark</mark>"
    html, _, _ = render.markdown(text)
    assert "<mark>mark</mark>" in html


def test_wiki_link():
    text = "[[Title|Link]]"
    html, _, _ = render.markdown(text)
    assert '<a href="/Link">Title</a>' in html
    text = "[[Link]]"
    html, _, _ = render.markdown(text)
    assert '<a href="/Link">Link</a>' in html
    text = "[[Text with spaces|Link with spaces]]"
    html, _, _ = render.markdown(text)
    assert '<a href="/Link%20with%20spaces">Text with spaces</a>' in html
    text = "[[A long long long page name]]"
    html, _, _ = render.markdown(text)
    assert (
        '<a href="/A%20long%20long%20long%20page%20name">A long long long page name</a>'
        in html
    )


def test_wiki_link_anchor():
    text = "[[Link with#anchor]]"
    html, _, _ = render.markdown(text)
    assert '<a href="/Link%20with#anchor">Link with#anchor</a>' in html
    text = "[[Link with#Some Heading]]"
    html, _, _ = render.markdown(text)
    assert (
        '<a href="/Link%20with#some-heading">Link with#Some Heading</a>'
        in html
    )


def test_wiki_link_anchor2():
    text = "[[Link with anchor and title|Link with#anchor]]"
    html, _, _ = render.markdown(text)
    assert (
        '<a href="/Link%20with#anchor">Link with anchor and title</a>' in html
    )
    text = "[[Link with title and#Some Heading]]"
    html, _, _ = render.markdown(text)
    assert (
        '<a href="/Link%20with%20title%20and#some-heading">Link with title and#Some Heading</a>'
        in html
    )


def test_wiki_link_subspace():
    text = "[[Paul|people/Paul]]"
    html, _, _ = render.markdown(text)
    assert '<a href="/people/Paul">Paul</a>' in html


def test_wiki_link_compatibility_mode():
    configured_renderer = OtterwikiRenderer(
        config={"WIKILINK_STYLE": "LinkTitle"}
    )
    text = "[[people/Paul|Paul]]"
    html, _, _ = configured_renderer.markdown(text)
    assert '<a href="/people/Paul">Paul</a>' in html
    text = "[[/people/Paul|Paul]]"
    html, _, _ = configured_renderer.markdown(text)
    assert '<a href="/people/Paul">Paul</a>' in html
    text = "[[Link]]"
    html, _, _ = render.markdown(text)
    assert '<a href="/Link">Link</a>' in html


def test_wiki_link_in_table():
    text = """| name | date | link |
| -------- | -------- | -------- |
| John | 01/31/1996 | [[people/John]] |
| Mary |10/08/2001 | [[Mary|people/Mary]] |

[[Paul|people/Paul]]
`[[Peter|Petra]]`

"""
    html, _, _ = render.markdown(text)
    assert '<td><a href="/people/John">people/John</a></td>' in html
    assert '<a href="/people/Paul">Paul</a>' in html
    assert '<td><a href="/people/Mary">Mary</a></td>' in html


def test_wiki_link_in_code():
    text = """`[[people/John]]`

```
[[Mary|people/Mary]]
```
"""
    html, _, _ = render.markdown(text)
    assert '<a href="/people/John">people/John</a>' not in html
    assert '<a href="/people/Mary">Mary</a>' not in html
    assert '[[people/John]]' in html
    assert '[[Mary|people/Mary]]' in html


def test_table_align():
    text = """
| left th     | center th     | right th  |
|:----------- |:-------------:| ---------:|
| left td     | center td     | right td  |
"""
    html, _, _ = render.markdown(text)
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
    assert (
        clean_html("<script>alert(1)</script>")
        == "&lt;script&gt;alert(1)&lt;/script&gt;"
    )
    assert (
        clean_html('<p onclick="alert(4)">PPPPP</p>')
        == '&lt;p onclick=&#34;alert(4)&#34;&gt;PPPPP&lt;/p&gt;'
    )


def test_clean_html_render():
    text = """Preformatted script:

    <script>alert(1)</script>

```html
<script>alert(3)</script>
```
<script>alert(2)</script>

And last an onclick example:
<p onclick="alert(4)">PPPPP</p>

<video controls width='80%'> <!-- this is updated to width="80%" -->
<source src="/mp4%20example/example.mp4" type="video/mp4">
</video>
"""
    html, _, _ = render.markdown(text)
    # make sure that preformatted html stays preformatted
    pre_code = BeautifulSoup(html, "html.parser").find_all(
        'pre', {'class': 'copy-to-clipboard'}
    )
    assert pre_code is not None
    assert (
        "<script>alert(1)</script>" in pre_code[0].text
    )  # bs4 decodes the html already
    # make sure that highlighted blocks are okay
    assert (
        '<span class=".highlight p">&lt;</span><span class=".highlight nt">script</span><span class=".highlight p">&gt;</span><span class=".highlight nx">alert</span><span class=".highlight p">(</span><span class=".highlight mf">3</span><span class=".highlight p">)&lt;/</span><span class=".highlight nt">script</span><span class=".highlight p">&gt;</span>'
        in str(pre_code[1])
    )
    # but script code is removed
    assert '<script>alert(2)</script>' not in html
    # and that onlick is removed
    assert '<p onclick="alert(4)"' not in html
    # check multimedia
    assert '<video controls="" width="80%">' in html
    assert "</video>" in html


def test_strikethrough():
    md = """
~~strike1~~
alpha bravo ~~strike2~~ charlie
~~s~t~r~i~k~e~3~~
~~strike4~~"""
    html, _, _ = render.markdown(md)
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
    html, _, _ = render.markdown(md)
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
    html, _, _ = render.markdown(md)
    assert "\\[a=b\\]" in html
    assert "\\[c=d\\]" in html
    assert "\\[a^2+b^2=c^2\\]" in html


def test_math_code_inline():
    text = "`$a$`"
    html, _, _ = render.markdown(text)
    assert "\\(a\\)" in html


def test_latex_inline():
    md = """
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

    html, _, _ = render.markdown(md)
    assert "\\(latex1\\)" in html
    assert "\\(latex2\\)" in html
    assert "\\(latex3\\)" in html
    assert "\\(latex4\\)" not in html
    assert "\\(latex5\\)" not in html
    assert "\\(latex6\\)" in html


def test_footnote_named():
    md = """Footnote identifier[^1] are single characters or words[^bignote].
And can be referenced multiple[^1] times.

[^1]: Footnotes test

[^bignote]: Or more complex.

    Indent paragraphs to include them
    in the footnote.

    Add as many paragraphs as you like.
"""
    html, _, _ = render.markdown(md)
    assert 'id="fn-1"' in html
    assert 'href="#fn-1"' in html
    assert 'id="fnref-1"' in html
    assert 'href="#fnref-1"' in html
    assert 'id="fn-2"' in html
    assert 'href="#fn-2"' in html
    assert 'id="fnref-2"' in html
    assert 'href="#fnref-2"' in html


def test_footnote_multiref():
    md = "\n".join(["Hello World [^1]" for _ in range(27)])
    md += "\n\n[^1]: Footnotes test"
    html, _, _ = render.markdown(md)
    assert '<a class="footnote" href="#fnref-27">aa</a>' in html


def test_footnote_not_found():
    md = "Footnote[^1]"
    html, _, _ = render.markdown(md)
    assert '<p>Footnote[^1]</p>' in html


def test_tasklist():
    md = """- [ ] a
- [x] b
- [ ] c"""
    html, _, _ = render.markdown(md)
    assert 3 == html.count("<li ") == html.count("</li>")
    assert 1 == html.count("checked")

    md = """<p>

- [ ] a
- [x] b
- [ ] c

</p>"""
    html, _, _ = render.markdown(md)
    assert 3 == html.count("<li ") == html.count("</li>")
    assert 1 == html.count("checked")


def test_fancy_blocks():
    md = """::: info
# Head of the block.
With _formatted_ content.
:::"""
    html, _, _ = render.markdown(md)
    assert '<h4 class="alert-heading">Head of the block.</h4>' in html
    assert '<em>formatted</em>' in html
    assert '<div class="alert alert-primary' in html
    assert 'role="alert"' in html

    md = """::: warning
a warning without header
:::"""
    html, _, _ = render.markdown(md)
    assert "<h4>" not in html
    assert 'class="alert alert-secondary' in html
    assert 'role="alert"' in html

    md = """::: success
good news everybody
:::"""
    html, _, _ = render.markdown(md)
    assert "<h4>" not in html
    assert 'class="alert alert-success' in html
    assert 'role="alert"' in html

    md = """::: red
**red alert**
:::"""
    html, _, _ = render.markdown(md)
    assert "<h4>" not in html
    assert "<strong>red alert</strong>" in html
    assert 'class="alert alert-danger' in html
    assert 'role="alert"' in html

    md = """:::
# Head of the block
_unspecified alert_
:::"""
    html, _, _ = render.markdown(md)
    assert '<h4 class="alert-heading">Head of the block</h4>' in html
    assert '<em>unspecified alert</em>' in html

    md = """::: myblock
# Head of my block
With _formatted_ content.
"""
    html, _, _ = render.markdown(md)
    assert 'class="alert alert-myblock' in html


def test_spoiler():
    md = """>! Spoiler blocks reveal their
>! content on click on the icon."""
    html, _, _ = render.markdown(md)
    # easier testing
    html = html.replace("\n", "")
    assert (
        '<p>Spoiler blocks reveal their content on click on the icon.</p>'
        in html
    )
    assert 'spoiler-button' in html


def test_fold():
    md = """>| # Headline is used as summary
>| with the details folded."""
    html, _, _ = render.markdown(md)
    # easier testing
    html = html.replace("\n", "")
    # check headline
    assert '>Headline is used as summary</summary>' in html
    # check fold
    assert "<p>with the details folded.</p>" in html


def test_all_alert_types():
    from otterwiki.renderer_plugins import mistunePluginAlerts

    for type, icon in mistunePluginAlerts.TYPE_ICONS.items():
        md = f"> [!{type}]\n>text\n>text\n"
        html, _, _ = render.markdown(md)
        assert 'text\ntext' in html
        assert icon in html


def test_alerts():
    md = """random paragraph 1.

>[!TIP]
>Note content

random paragraph 2."""
    html, _, _ = render.markdown(md)
    # easier testing
    html = html.replace("\n", "")
    # check content
    assert 'Note content' in html
    assert 'Tip</div>'
    # make sure nothing is lost
    assert '<p>random paragraph 1.</p>' in html
    assert '<p>random paragraph 2.</p>' in html


def test_mistunePluginAlerts():
    from otterwiki.renderer_plugins import mistunePluginAlerts

    for type, icon in mistunePluginAlerts.TYPE_ICONS.items():
        # check regexp
        md = f">[!{type}]\n>Note content\n>content\n"
        m = mistunePluginAlerts.ALERT_BLOCK.search(md)
        assert m is not None
        assert m.group(1) == type


def test_mermaid():
    md = """
```mermaid
graph TD;
    A-->B;
```
"""
    html, _, _ = render.markdown(md)
    assert (
        """<pre class="mermaid">graph TD;
    A--&gt;B;\n</pre>"""
        in html
    )


def test_pygments_render_python_doublebracket():
    code = """df[['a', "b"]]"""
    html = pygments_render(code, "python", linenumbers=False)
    code = BeautifulSoup(html, "html.parser").find(
        'div', {'class': 'highlight'}
    )
    assert code
    code = str(code.text)
    assert """df[['a', "b"]]""" in code


def test_render_python_doublebracket():
    # https://github.com/redimp/otterwiki/issues/190
    md = """```python
df[['a', "b"]]
```"""
    html, _, _ = render.markdown(md)
    code = BeautifulSoup(html, "html.parser").find(
        'div', {'class': 'highlight'}
    )
    assert code
    code = code.text
    assert """df[['a', "b"]]""" in code


def test_indent_preformatted_issue206():
    md = """# Preformatted

     Hello :) This is at 5 spaces.
     5 spaces here as well."""
    html, _, _ = render.markdown(md)
    pre = BeautifulSoup(html, "html.parser").find('pre')
    assert pre
    assert (
        """ Hello :) This is at 5 spaces.
 5 spaces here as well."""
        == pre.text
    )
    # backtick block
    md = """# Code block

```
 One leading space here
  and two here.
```
"""
    html, _, _ = render.markdown(md)
    pre = BeautifulSoup(html, "html.parser").find('pre')
    assert pre
    assert (
        """ One leading space here
  and two here.\n"""
        == pre.text
    )

    # backtick block with language
    md = """# Code block

```c
 int main(int argc, char **argv) {
  }
```
"""
    html, _, _ = render.markdown(md)
    code = BeautifulSoup(html, "html.parser").find(
        'div', {'class': 'highlight'}
    )
    assert code
    assert (
        """ int main(int argc, char **argv) {
  }\n"""
        == code.text
    )


def test_indent_preformatted_issue212():
    md = """# Example page

    This is preformatted.

This is regular."""
    html, _, _ = render.markdown(md)
    pre = BeautifulSoup(html, "html.parser").find('pre')
    assert pre
    assert """This is preformatted.\n""" == pre.text


def test_nested_list():
    md = """# Nested lists
1. A
    - B
    - C
2. D
"""
    html, _, _ = render.markdown(md)
    ol = BeautifulSoup(html, "html.parser").find('ol')
    assert ol
    li = ol.find_all("li")  # pyright: ignore
    assert len(li) == 4
    ul = li[0].find("ul")
    assert ul
    li = ul.find_all("li")  # pyright: ignore
    assert len(li) == 2


def test_empty_blocks_issue216():
    md = """:::info
:::
    """
    html, _, _ = render.markdown(md)
    assert html

    md = """>|"""
    html, _, _ = render.markdown(md)
    assert html


def test_frontmatter():
    md = """---
title: Title from frontmatter
tag: test
date: 2025-04-06 11:05:01
---
    """
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    assert soup
    # check if the "title" key added a <h1></h1>
    h1 = soup.find("h1")
    assert h1
    assert h1.text == "Title from frontmatter"
    # check if the tag was added to the frontmatter
    details = soup.find("details", {"id": "frontmatter"})
    assert details
    pre = details.find("pre")
    assert pre is not None
    assert hasattr(pre, "text")
    assert "tag: test" in pre.text  # pyright:ignore


def test_library_requirements_mermaid():
    md = """
```mermaid
graph TD;
    A-->B;
```
"""
    html, toc, library_requirements = render.markdown(md)
    assert library_requirements['requires_mermaid'] is True
    assert library_requirements['requires_mathjax'] is False
    assert '<pre class="mermaid">' in html


def test_library_requirements_mathjax_inline():
    md = "This is inline math: `$a^2+b^2=c^2$`"
    html, toc, library_requirements = render.markdown(md)
    assert library_requirements['requires_mermaid'] is False
    assert library_requirements['requires_mathjax'] is True
    assert "\\(a^2+b^2=c^2\\)" in html


def test_library_requirements_mathjax_block():
    md = """# Math Example

Here is a math block:

```math
x + y = z
```

End of example."""
    html, toc, library_requirements = render.markdown(md)
    assert library_requirements['requires_mermaid'] is False
    assert library_requirements['requires_mathjax'] is True
    assert "\\[x + y = z\\]" in html
    assert "<h1" in html


def test_library_requirements_both():
    md = """
# Test Page

Inline math: `$E=mc^2$`

```mermaid
graph TD;
    A-->B;
```

Math block:
```math
F = ma
```
"""
    html, toc, library_requirements = render.markdown(md)
    assert library_requirements['requires_mermaid'] is True
    assert library_requirements['requires_mathjax'] is True
    assert "\\(E=mc^2\\)" in html
    assert '<pre class="mermaid">' in html
    assert "\\[F = ma\\]" in html


def test_library_requirements_none():
    md = """
# Simple Page

Just some **bold** and *italic* text.

- List item 1
- List item 2

| Column 1 | Column 2 |
|----------|----------|
| Cell 1   | Cell 2   |
"""
    html, toc, library_requirements = render.markdown(md)
    assert library_requirements['requires_mermaid'] is False
    assert library_requirements['requires_mathjax'] is False
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html
