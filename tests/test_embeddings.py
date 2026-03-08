#!/usr/bin/env python3
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
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


def test_attachmentlist(create_app):
    author = ("Test Author", "test@example.com")
    create_app.storage.store(
        "testpage.md",
        content="# Test\n{{Attachments}}\n",
        author=author,
        message="test page",
    )
    create_app.storage.store(
        "testpage/report.txt",
        content="hello",
        author=author,
        message="add report",
    )
    client = create_app.test_client()
    response = client.get("/Testpage/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    table_div = soup.find("div", class_="attachmentlist-embedding")
    assert table_div is not None
    table = table_div.find("table")
    assert table is not None
    assert "report.txt" in html


def test_attachmentlist_caption(create_app):
    author = ("Test Author", "test@example.com")
    create_app.storage.store(
        "testpage2.md",
        content="# Test\n{{Attachments\n|caption=My Files\n}}\n",
        author=author,
        message="test page",
    )
    create_app.storage.store(
        "testpage2/data.csv",
        content="a,b,c",
        author=author,
        message="add data",
    )
    client = create_app.test_client()
    response = client.get("/Testpage2/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    table_div = soup.find("div", class_="attachmentlist-embedding")
    assert table_div is not None
    caption = table_div.find("caption")
    assert caption is not None
    assert caption.text == "My Files"
    assert "data.csv" in html


def test_attachmentlist_filter(create_app):
    author = ("Test Author", "test@example.com")
    create_app.storage.store(
        "testpage3.md",
        content="# Test\n{{Attachments\n|filter=*.txt\n}}\n",
        author=author,
        message="test page",
    )
    create_app.storage.store(
        "testpage3/notes.txt",
        content="notes",
        author=author,
        message="add notes",
    )
    create_app.storage.store(
        "testpage3/image.png",
        content=b"\x89PNG\r\n",
        author=author,
        message="add image",
        mode="wb",
    )
    client = create_app.test_client()
    response = client.get("/Testpage3/view")
    assert response.status_code == 200
    html = response.data.decode()
    assert "notes.txt" in html
    assert "image.png" not in html


def test_attachmentlist_empty(create_app):
    author = ("Test Author", "test@example.com")
    create_app.storage.store(
        "testpage4.md",
        content="# Test\n{{Attachments}}\n",
        author=author,
        message="test page",
    )
    client = create_app.test_client()
    response = client.get("/Testpage4/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    table_div = soup.find("div", class_="attachmentlist-embedding")
    assert table_div is not None


def test_attachmentlist_format_minimal(create_app):
    author = ("Test Author", "test@example.com")
    create_app.storage.store(
        "testpage5.md",
        content="# Test\n{{Attachments\n|format=minimal\n}}\n",
        author=author,
        message="test page",
    )
    create_app.storage.store(
        "testpage5/readme.txt",
        content="readme",
        author=author,
        message="add readme",
    )
    client = create_app.test_client()
    response = client.get("/Testpage5/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    table_div = soup.find("div", class_="attachmentlist-embedding")
    assert table_div is not None
    # only filename column — no Author or Comment headers
    assert "readme.txt" in html
    assert "Author" not in table_div.decode_contents()
    assert "Comment" not in table_div.decode_contents()
    assert "Size" not in table_div.decode_contents()


def test_attachmentlist_format_details(create_app):
    author = ("Test Author", "test@example.com")
    create_app.storage.store(
        "testpage6.md",
        content="# Test\n{{Attachments\n|format=details\n}}\n",
        author=author,
        message="test page",
    )
    create_app.storage.store(
        "testpage6/data.txt",
        content="data",
        author=author,
        message="add data",
    )
    client = create_app.test_client()
    response = client.get("/Testpage6/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    table_div = soup.find("div", class_="attachmentlist-embedding")
    assert table_div is not None
    contents = table_div.decode_contents()
    assert "data.txt" in contents
    assert "Size" in contents
    assert "Date" in contents
    assert "Author" not in contents
    assert "Comment" not in contents


def test_attachmentlist_no_icons(create_app):
    author = ("Test Author", "test@example.com")
    create_app.storage.store(
        "testpage7.md",
        content="# Test\n{{Attachments\n|icons=false\n}}\n",
        author=author,
        message="test page",
    )
    create_app.storage.store(
        "testpage7/file.txt",
        content="content",
        author=author,
        message="add file",
    )
    client = create_app.test_client()
    response = client.get("/Testpage7/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    table_div = soup.find("div", class_="attachmentlist-embedding")
    assert table_div is not None
    # no img or fa icon in the table
    assert table_div.find("img") is None
    assert "fa-file" not in table_div.decode_contents()
