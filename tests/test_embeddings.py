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


def test_imageframe_basic():
    md = """
{{ImageFrame
|caption=Test Caption
![alt](/img/test.png)
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    frame = soup.find("div", class_="imageframe-caption")
    assert frame is not None
    # default float is right
    assert "float:right" in frame.get("style", "")
    assert "clear:right" in frame.get("style", "")
    # default width
    assert "width:30%" in frame.get("style", "")
    # caption rendered
    caption = frame.find("div", class_="imageframe")
    assert caption is not None
    assert caption.text == "Test Caption"
    # image rendered inside frame
    assert frame.find("img") is not None


def test_imageframe_position_left():
    md = """
{{ImageFrame
|position=left
|width=50%
![alt](/img/test.png)
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    frame = soup.find("div", class_="imageframe-caption")
    assert frame is not None
    style = frame.get("style", "")
    assert "float:left" in style
    assert "clear:left" in style
    assert "width:50%" in style


def test_imageframe_no_caption():
    md = """
{{ImageFrame
![alt](/img/test.png)
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    frame = soup.find("div", class_="imageframe-caption")
    assert frame is not None
    # no caption div when caption is omitted
    assert frame.find("div", class_="imageframe") is None


def test_imageframe_text_align():
    md = """
{{ImageFrame
|text-align=center
![alt](/img/test.png)
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    frame = soup.find("div", class_="imageframe-caption")
    assert frame is not None
    assert "text-align:center" in frame.get("style", "")


def test_imageframe_custom_style():
    md = """
{{ImageFrame
|style=opacity:0.8
![alt](/img/test.png)
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    frame = soup.find("div", class_="imageframe-caption")
    assert frame is not None
    assert "opacity:0.8" in frame.get("style", "")


def test_imageframe_alias():
    md = """
{{Image Frame
|caption=Alias Test
![alt](/img/test.png)
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    frame = soup.find("div", class_="imageframe-caption")
    assert frame is not None
    caption = frame.find("div", class_="imageframe")
    assert caption is not None
    assert caption.text == "Alias Test"


DATATABLE_MD = """\
{{datatable
| Name | Score |
| ---- | ----: |
| Alice | 42 |
| Bob | 7 |
}}
"""


def test_datatable_basic():
    html, _, _ = render.markdown(DATATABLE_MD)
    soup = BeautifulSoup(html, "html.parser")
    # table must have an s-dt-* id
    table = soup.find("table", id=lambda v: v and v.startswith("s-dt-"))
    assert table is not None
    # content is preserved
    assert "Alice" in html
    assert "Bob" in html


def test_datatable_javascript():
    from otterwiki.plugins import collect_hook

    render.markdown(DATATABLE_MD)
    js_parts = collect_hook("renderer_javascript")
    js = "".join(js_parts)
    assert "simpleDatatables.DataTable" in js
    assert "s-dt-" in js


def test_datatable_options_bool():
    from otterwiki.plugins import collect_hook

    md = """\
{{datatable
|paging=false
|searchable=true
|sortable=false
|fixedHeight=false
| A | B |
| - | - |
| 1 | 2 |
}}
"""
    render.markdown(md)
    js = "".join(collect_hook("renderer_javascript"))
    assert "paging: false" in js
    assert "searchable: true" in js
    assert "sortable: false" in js
    assert "fixedHeight: false" in js


def test_datatable_option_perpage():
    from otterwiki.plugins import collect_hook

    md = """\
{{datatable
|perPage=42
| A | B |
| - | - |
| 1 | 2 |
}}
"""
    render.markdown(md)
    js = "".join(collect_hook("renderer_javascript"))
    assert "perPage: 42" in js
    # custom perPage value must appear in the perPageSelect list
    assert '"42", 42' in js


def test_datatable_option_caption():
    from otterwiki.plugins import collect_hook

    md = """\
{{datatable
|caption=My Table
| A | B |
| - | - |
| 1 | 2 |
}}
"""
    render.markdown(md)
    js = "".join(collect_hook("renderer_javascript"))
    assert 'caption: "My Table"' in js


def test_datatable_multiple_tables():
    from otterwiki.plugins import collect_hook

    md = """\
{{datatable
| A | B |
| - | - |
| 1 | 2 |

| X | Y |
| - | - |
| 3 | 4 |
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all(
        "table", id=lambda v: v and v.startswith("s-dt-")
    )  # pyright: ignore
    assert len(tables) == 2
    # each table must have a unique id
    ids = [t["id"] for t in tables]
    assert ids[0] != ids[1]
    # JS must initialise both
    js = "".join(collect_hook("renderer_javascript"))
    assert js.count("simpleDatatables.DataTable") == 2


def test_datatable_no_table():
    from otterwiki.plugins import collect_hook

    md = """\
{{datatable
No table here, just text.
}}
"""
    html, _, _ = render.markdown(md)
    js = "".join(collect_hook("renderer_javascript"))
    assert "simpleDatatables.DataTable" not in js


def test_datatable_csv_basic(create_app):
    author = ("Test Author", "test@example.com")
    csv_content = "Name;Score\nAlice;42\nBob;7\n"
    create_app.storage.store(
        "csvpage.md",
        content="# CSV Test\n{{datatable\n|src=data.csv\n}}\n",
        author=author,
        message="csv page",
    )
    create_app.storage.store(
        "csvpage/data.csv",
        content=csv_content,
        author=author,
        message="add csv",
    )
    client = create_app.test_client()
    response = client.get("/Csvpage/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find(
        "table", id=lambda v: v and v.startswith("s-dt-")
    )  # pyright: ignore
    assert table is not None
    assert "Alice" in html
    assert "Bob" in html
    # headers from first row
    assert "Name" in html
    assert "Score" in html


def test_datatable_csv_custom_delimiter(create_app):
    author = ("Test Author", "test@example.com")
    csv_content = "Name,Score\nAlice,42\nBob,7\n"
    create_app.storage.store(
        "csvpage_sep.md",
        content="# CSV Test\n{{datatable\n|src=data.csv\n|delimiter=,\n}}\n",
        author=author,
        message="csv page",
    )
    create_app.storage.store(
        "csvpage_sep/data.csv",
        content=csv_content,
        author=author,
        message="add csv",
    )
    client = create_app.test_client()
    response = client.get("/Csvpage_sep/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find(
        "table", id=lambda v: v and v.startswith("s-dt-")
    )  # pyright: ignore
    assert table is not None
    assert "Alice" in html
    assert "Name" in html


def test_datatable_csv_column_selection_by_index(create_app):
    author = ("Test Author", "test@example.com")
    csv_content = "Name;Score;Date\nAlice;42;2024-01-01\nBob;7;2024-02-01\n"
    create_app.storage.store(
        "csvpage_cols.md",
        content="# CSV Test\n{{datatable\n|src=data.csv\n|columns=1,2\n}}\n",
        author=author,
        message="csv page",
    )
    create_app.storage.store(
        "csvpage_cols/data.csv",
        content=csv_content,
        author=author,
        message="add csv",
    )
    client = create_app.test_client()
    response = client.get("/Csvpage_cols/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find(
        "table", id=lambda v: v and v.startswith("s-dt-")  # pyright: ignore
    )  # pyright: ignore
    assert table is not None
    assert "Alice" in html
    assert "Name" in html
    assert "Score" in html
    assert "Date" not in table.decode_contents()


def test_datatable_csv_column_selection_by_name(create_app):
    author = ("Test Author", "test@example.com")
    csv_content = "Name;Score;Date\nAlice;42;2024-01-01\nBob;7;2024-02-01\n"
    create_app.storage.store(
        "csvpage_colname.md",
        content="# CSV Test\n{{datatable\n|src=data.csv\n|columns=Name,Score\n}}\n",
        author=author,
        message="csv page",
    )
    create_app.storage.store(
        "csvpage_colname/data.csv",
        content=csv_content,
        author=author,
        message="add csv",
    )
    client = create_app.test_client()
    response = client.get("/Csvpage_colname/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find(
        "table", id=lambda v: v and v.startswith("s-dt-")  # pyright: ignore
    )
    assert table is not None
    assert "Alice" in table.text
    assert "Date" not in table.decode_contents()


def test_datatable_csv_header_override(create_app):
    author = ("Test Author", "test@example.com")
    csv_content = "Name;Score\nAlice;42\nBob;7\n"
    create_app.storage.store(
        "csvpage_hdr.md",
        content="# CSV Test\n{{datatable\n|src=data.csv\n|headers=Player,Points\n}}\n",
        author=author,
        message="csv page",
    )
    create_app.storage.store(
        "csvpage_hdr/data.csv",
        content=csv_content,
        author=author,
        message="add csv",
    )
    client = create_app.test_client()
    response = client.get("/Csvpage_hdr/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find(
        "table", id=lambda v: v and v.startswith("s-dt-")  # pyright: ignore
    )  # pyright: ignore
    assert table is not None
    assert "Player" in html
    assert "Points" in html
    # original CSV headers should not appear
    assert table.find("thead")
    assert (
        "Name" not in table.find("thead").decode_contents()
    )  # pyright:ignore
    assert (
        "Score" not in table.find("thead").decode_contents()
    )  # pyright:ignore


def test_datatable_csv_no_header(create_app):
    author = ("Test Author", "test@example.com")
    csv_content = "Alice;42\nBob;7\n"
    create_app.storage.store(
        "csvpage_nohdr.md",
        content="# CSV Test\n{{datatable\n|src=data.csv\n|header=false\n}}\n",
        author=author,
        message="csv page",
    )
    create_app.storage.store(
        "csvpage_nohdr/data.csv",
        content=csv_content,
        author=author,
        message="add csv",
    )
    client = create_app.test_client()
    response = client.get("/Csvpage_nohdr/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find(
        "table", id=lambda v: v and v.startswith("s-dt-")  # pyright: ignore
    )  # pyright: ignore
    assert table is not None
    assert "Alice" in html
    assert "Bob" in html
    assert table.find("thead") is None


def test_datatable_csv_missing_file(create_app):
    author = ("Test Author", "test@example.com")
    create_app.storage.store(
        "csvpage_miss.md",
        content="# CSV Test\n{{datatable\n|src=missing.csv\n}}\n",
        author=author,
        message="csv page",
    )
    client = create_app.test_client()
    response = client.get("/Csvpage_miss/view")
    assert response.status_code == 200
    html = response.data.decode()
    assert "not found" in html


def test_datatable_csv_quotechar_default(create_app):
    """Double-quoted fields with embedded separators are parsed correctly."""
    author = ("Test Author", "test@example.com")
    # "Alice, Jr." contains the default separator (;) inside quotes — but we
    # use the default quotechar (") so the field must be kept intact.
    csv_content = 'Name;Score\n"Alice, Jr.";42\nBob;7\n'
    create_app.storage.store(
        "csvpage_qc1.md",
        content="# CSV Test\n{{datatable\n|src=data.csv\n}}\n",
        author=author,
        message="csv page",
    )
    create_app.storage.store(
        "csvpage_qc1/data.csv",
        content=csv_content,
        author=author,
        message="add csv",
    )
    client = create_app.test_client()
    response = client.get("/Csvpage_qc1/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find(
        "table", id=lambda v: v and v.startswith("s-dt-")  # pyright: ignore
    )
    assert table is not None
    # The quoted field must appear as a single cell, not be split
    cells = [td.get_text() for td in table.find_all("td")]
    assert "Alice, Jr." in cells
    assert "42" in cells


def test_datatable_csv_quotechar_custom(create_app):
    """Custom quotechar is respected when parsing CSV fields."""
    author = ("Test Author", "test@example.com")
    # Use single-quote as quotechar; field contains the separator
    csv_content = "Name;Score\n'O;Brien';99\nBob;7\n"
    create_app.storage.store(
        "csvpage_qc2.md",
        content="# CSV Test\n{{datatable\n|src=data.csv\n|quotechar='\n}}\n",
        author=author,
        message="csv page",
    )
    create_app.storage.store(
        "csvpage_qc2/data.csv",
        content=csv_content,
        author=author,
        message="add csv",
    )
    client = create_app.test_client()
    response = client.get("/Csvpage_qc2/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find(
        "table", id=lambda v: v and v.startswith("s-dt-")  # pyright: ignore
    )
    assert table is not None
    cells = [td.get_text() for td in table.find_all("td")]
    assert "O;Brien" in cells
    assert "99" in cells


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
