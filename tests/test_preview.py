#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai
# -*- coding: utf-8 -*-

import pytest
from pprint import pprint
from test_otterwiki import create_app, req_ctx
from otterwiki.renderer import markdown_render

markdown_example = """# Header

Bla Bla.

```bash
WORLD="World"
echo "Hello $WORLD"
```

- a
- b
- c

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
    html_example = markdown_render(markdown_example)
    html_example_arr = html_example.split("<")
    from otterwiki.wiki import Page
    p = Page("test")
    preview_html = p.preview(content=markdown_example)
    for part in html_example_arr:
        assert part in preview_html
    # check every cursor line
    for i,md_line in enumerate(markdown_example.splitlines(),start=1):
        preview_html = p.preview(content=markdown_example,cursor_line=i,cursor_ch=1) 
        preview_html = preview_html.replace("<span id=\"cursor\"></span>","")
        for j,part in enumerate(html_example_arr):
            cursor_line='name="cursor_line" value="{}"'.format(i)
            assert cursor_line in preview_html
            assert part in preview_html

