#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai

import bs4
import re
from otterwiki.renderer import render

markdown_example = """# Header

Bla Bla.

```bash
WORLD="World"
echo "Hello $WORLD"
```

- a
- b
- c

1. one
2. two
3. three

| column1 | column2 |
|---------|---------|
| row11   | row21   |
| row12   | row22   |
| row13   | row23   |

Inline math: `$a^2+b^2=c^2$`

Math block:
```math
a^2+b^2=c^2
```

---

> This is a quote.
> It can span multiple lines!
>> And multiple levels.
>> *With markdown syntax.*


[[WikiPage]]

[[Text to display|WikiPage]]

[Example Link with text](http://example.com)
"""

"""
<span class=".highlight nb">echo</span> <span class=".highlight s2">&quot;Hello </span><span class=".highlight nv">$WORLD</span><span class=".highlight s2">&quot;</span>
"""


def test_preview(create_app, req_ctx):
    from otterwiki.wiki import Page

    p = Page("test")
    data = p.preview(content=markdown_example, cursor_line=1)
    assert render.htmlcursor in data['preview_content']


def test_preview_all(create_app, req_ctx):
    whitespace = re.compile(r"\s+")
    markdown_arr = markdown_example.splitlines()
    html_example, _, _ = render.markdown(markdown_example)
    html_example_soup = bs4.BeautifulSoup(html_example, "html.parser")
    from otterwiki.wiki import Page

    p = Page("test")
    data = p.preview(content=markdown_example, cursor_line=1)
    preview_soup = bs4.BeautifulSoup(
        data['preview_content'].replace(render.htmlcursor, ""), "html.parser"
    )
    preview_soup = preview_soup.find("div", {"class": "page"})
    assert preview_soup
    for element in html_example_soup:
        assert str(element) in str(preview_soup)
    assert render.htmlcursor in data['preview_content']
    # check every cursor line
    for i, md_line in enumerate(markdown_example.splitlines(), start=1):
        data = p.preview(content=markdown_example, cursor_line=i)
        assert render.htmlcursor.strip() in data['preview_content']
        # clean cursor and newlines
        preview_soup = bs4.BeautifulSoup(
            data['preview_content']
            .replace(render.htmlcursor, "")
            .replace(render.htmlcursor.strip(), ""),
            "html.parser",
        )
        # remove all the whitespace (the htmlcursor leaves annoying artifatcs)
        preview_soup = preview_soup.find("div", {"class": "page"})
        preview_html = whitespace.sub("", str(preview_soup))
        # and check if everything made it into html
        for element in html_example_soup:
            if not element:
                continue
            element = whitespace.sub("", str(element))
            if not len(element):
                continue
            # assert str(element).strip() in str(preview_soup)
            assert str(element) in preview_html


def test_preview_list_bug(create_app, req_ctx):
    from otterwiki.wiki import Page

    p = Page("test")
    content = """Zeile
1. eins
2. zwei
3. drei"""
    data = p.preview(content=content, cursor_line=5)
    assert "<li>eins" in data['preview_content']
    assert "<li>zwei" in data['preview_content']
    assert "<li>drei" in data['preview_content']


def test_preview_italic_bug(create_app, req_ctx):
    from otterwiki.wiki import Page

    p = Page("test")
    content = """# Header

_A paragraph_"""
    data = p.preview(content=content, cursor_line=3)
    assert "<em>A paragraph</em>" in data['preview_content']
    soup = bs4.BeautifulSoup(data['preview_content'], "html.parser").find("em")
    assert soup
    text = soup.text.strip()
    assert "A paragraph" == text


def test_preview_cursor_in_codeblock(create_app, req_ctx):
    from otterwiki.wiki import Page

    p = Page("test")
    content = """# Header

    ```
    code in block
    ```
    """
    data = p.preview(content=content, cursor_line=2)
    soup = bs4.BeautifulSoup(str(data['preview_content']), "html.parser").find(
        "pre"
    )
    assert soup
    text = soup.text.strip("`\n")
    # the "  " are an artifact from the html cursor and expected
    assert "code in block  " == text


def test_preview_cursor_in_abbr(create_app, req_ctx):
    from otterwiki.wiki import Page

    p = Page("test")
    content = """*[HTML]: Hypertext Markup Language
*[CSS]: Cascading Style Sheets

HTML and CSS are essential web technologies.
"""

    data = p.preview(content=content, cursor_line=0)
    assert data and data['preview_content']
    soup = bs4.BeautifulSoup(str(data['preview_content']), "html.parser").find(
        "div", class_="page"
    )
    assert soup and soup.text
    # the "   " are an artifact from the html cursor and expected
    assert "HTML and   CSS are essential web technologies." in soup.text
