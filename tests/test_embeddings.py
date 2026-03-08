#!/usr/bin/env python3
# vim: set et ts=8 sts=4 sw=4 ai:

from otterwiki.renderer import render
from bs4 import BeautifulSoup


def test_unknownembedding():
    md = """
{{UnknownEmbeddingAAA
}}
"""
    html, _, _ = render.markdown(md)
    assert "Unknown Embedding:" in html
    assert "UnknownEmbeddingAAA" in html

    md = """
{{UnknownEmbeddingBBB}}
"""
    html, _, _ = render.markdown(md)
    assert "Unknown Embedding:" in html
    assert "UnknownEmbeddingBBB" in html


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
    soup = BeautifulSoup(html, "html.parser")
    assert soup
    # make sure the infox is found
    infobox = soup.find("div", class_="infobox")
    assert infobox
    infobox_table = infobox.find("table", class_="infobox")
    assert infobox_table

    # anaylse table
    table_options = {}
    for i, row in enumerate(
        infobox_table.find_all("tr", class_="infobox-key-value")
    ):
        cells = row.find_all("td")
        if len(cells) >= 2:
            key = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            table_options[key] = value

    assert table_options['Homepage'] == 'otterwiki.com'
    assert table_options['key'] == 'value'

    # make sure the link is rendered
    ahomepage = infobox_table.find("a")
    assert ahomepage
    assert ahomepage.get("href") == "https://otterwiki.com"
    # make sure the div.highlight exists
    divhighlight = infobox_table.find("div", class_="highlight")
    assert divhighlight
    assert "markdown=True" == divhighlight.text.strip()
