#!/usr/bin/env python3
# vim: set et ts=8 sts=4 sw=4 ai:

from otterwiki.renderer import render
from bs4 import BeautifulSoup


def test_infobox():
    md = """
{{InfoBox
|caption=With Markdown
|key=value
|text-align=justify
|Homepage=[otterwiki.com](https://otterwiki.com)
Lorem **ipsum** dolor sit _amet_, consectetur adipiscing elit.

```bash
markdown=True
```

}}
"""
    html, _, _ = render.markdown(md)
    assert html
