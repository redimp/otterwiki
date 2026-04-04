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
    # default float is right via CSS class
    assert "imageframe-float-right" in frame.get("class", [])
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
    assert "imageframe-float-left" in frame.get("class", [])
    assert "width:50%" in frame.get("style", "")


def test_imageframe_default_floats_right():
    md = """
{{ImageFrame
![alt](/img/test.png)
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    frame = soup.find("div", class_="imageframe-caption")
    assert frame is not None
    assert "imageframe-float-right" in frame.get("class", [])


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


def test_imageframe_src_attachment(create_app):
    """src= option resolves an image attachment and renders an <img> tag."""
    author = ("Test Author", "test@example.com")
    create_app.storage.store(
        "imgframepage.md",
        content="{{ImageFrame\n|src=photo.png\n|caption=My Photo\n}}\n",
        author=author,
        message="add page",
    )
    # store a minimal 1x1 PNG as the attachment
    import base64

    png_1x1 = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    create_app.storage.store(
        "imgframepage/photo.png",
        content=png_1x1,
        author=author,
        message="add image",
        mode="wb",
    )
    client = create_app.test_client()
    response = client.get("/Imgframepage/view")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data.decode(), "html.parser")
    frame = soup.find("div", class_="imageframe-caption")
    assert frame is not None
    a = frame.find("a")
    assert a is not None
    assert "photo.png" in a.get("href", "")
    assert a.get("target") == "_blank"
    img = a.find("img")
    assert img is not None
    assert "photo.png" in img.get("src", "")
    caption = frame.find("div", class_="imageframe")
    assert caption is not None
    assert caption.text == "My Photo"


def test_imageframe_src_attachment_alt(create_app):
    """alt= option sets the img alt attribute."""
    author = ("Test Author", "test@example.com")
    create_app.storage.store(
        "imgframealt.md",
        content="{{ImageFrame\n|src=photo.png\n|alt=A nice photo\n}}\n",
        author=author,
        message="add page",
    )
    import base64

    png_1x1 = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    create_app.storage.store(
        "imgframealt/photo.png",
        content=png_1x1,
        author=author,
        message="add image",
        mode="wb",
    )
    client = create_app.test_client()
    response = client.get("/Imgframealt/view")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data.decode(), "html.parser")
    img = soup.find("img", alt="A nice photo")
    assert img is not None


def test_imageframe_src_absolute_path(create_app):
    """|src=/OtherPage/photo.png loads an attachment from another page."""
    author = ("Test Author", "test@example.com")
    import base64

    png_1x1 = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    # store the image on OtherPage
    create_app.storage.store(
        "otherpage.md",
        content="# Other Page\n",
        author=author,
        message="add other page",
    )
    create_app.storage.store(
        "otherpage/photo.png",
        content=png_1x1,
        author=author,
        message="add image",
        mode="wb",
    )
    # embed it from a different page
    create_app.storage.store(
        "embedder.md",
        content="{{ImageFrame\n|src=/otherpage/photo.png\n|caption=From Other\n}}\n",
        author=author,
        message="add embedder page",
    )
    client = create_app.test_client()
    response = client.get("/Embedder/view")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data.decode(), "html.parser")
    frame = soup.find("div", class_="imageframe-caption")
    assert frame is not None
    a = frame.find("a")
    assert a is not None
    assert "photo.png" in a.get("href", "")
    assert a.get("target") == "_blank"
    img = a.find("img")
    assert img is not None
    assert "photo.png" in img.get("src", "")


def test_imageframe_src_external_url():
    """src= with https:// URL embeds the image directly without attachment lookup."""
    md = """\
{{ImageFrame
|src=https://example.com/photo.jpg
|alt=External photo
|caption=Remote image
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    frame = soup.find("div", class_="imageframe-caption")
    assert frame is not None
    a = frame.find("a")
    assert a is not None
    assert a["href"] == "https://example.com/photo.jpg"
    assert a.get("target") == "_blank"
    img = a.find("img")
    assert img is not None
    assert img["src"] == "https://example.com/photo.jpg"
    assert img["alt"] == "External photo"


def test_imageframe_src_missing_attachment(create_app):
    """src= referencing a non-existent attachment renders an error."""
    author = ("Test Author", "test@example.com")
    create_app.storage.store(
        "imgframemissing.md",
        content="{{ImageFrame\n|src=missing.png\n}}\n",
        author=author,
        message="add page",
    )
    client = create_app.test_client()
    response = client.get("/Imgframemissing/view")
    assert response.status_code == 200
    html = response.data.decode()
    assert 'missing.png' in html
    assert 'not found' in html.lower() or 'error' in html.lower()


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


def test_datatable_csv_absolute_src(create_app):
    """src=/OtherPage/data.csv loads a CSV attachment from another page."""
    author = ("Test Author", "test@example.com")
    csv_content = "City;Population\nBerlin;3.6M\nParis;2.1M\n"
    create_app.storage.store(
        "datasource.md",
        content="# Data Source\n",
        author=author,
        message="add data source page",
    )
    create_app.storage.store(
        "datasource/data.csv",
        content=csv_content,
        author=author,
        message="add csv",
    )
    create_app.storage.store(
        "csvabspage.md",
        content="# CSV Abs Test\n{{datatable\n|src=/datasource/data.csv\n}}\n",
        author=author,
        message="csv abs page",
    )
    client = create_app.test_client()
    response = client.get("/Csvabspage/view")
    assert response.status_code == 200
    html = response.data.decode()
    assert "Berlin" in html
    assert "Paris" in html
    assert "City" in html


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


def test_infobox_alias():
    md = """
{{Info Box
|caption=Alias
|key=val
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    assert soup.find("div", class_="infobox") is not None


def test_infobox_position_left():
    md = """
{{InfoBox
|position=left
|key=val
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    box = soup.find("div", class_="infobox")
    assert box is not None
    assert "infobox-float-left" in box.get("class", [])


def test_infobox_position_right():
    md = """
{{InfoBox
|position=right
|key=val
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    box = soup.find("div", class_="infobox")
    assert box is not None
    assert "infobox-float-right" in box.get("class", [])


def test_infobox_default_floats_right():
    md = """
{{InfoBox
|key=val
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    box = soup.find("div", class_="infobox")
    assert box is not None
    assert "infobox-float-right" in box.get("class", [])


def test_infobox_width():
    md = """
{{InfoBox
|width=50%
|key=val
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    box = soup.find("div", class_="infobox")
    assert box is not None
    assert "width:50%" in box.get("style", "")


def test_infobox_custom_style():
    md = """
{{InfoBox
|style=opacity:0.5
|key=val
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    box = soup.find("div", class_="infobox")
    assert box is not None
    assert "opacity:0.5" in box.get("style", "")


def test_infobox_underscore_key():
    """Keys prefixed with _ have the underscore stripped."""
    md = """
{{InfoBox
|_Hidden Key=secret
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="infobox")
    assert table is not None
    assert "Hidden Key" in table.get_text()
    assert "_Hidden Key" not in table.get_text()


def test_infobox_excluded_keys_not_in_rows():
    """caption, width, float, position, pos, text-align, align and style must not appear as key-value rows."""
    md = """
{{InfoBox
|caption=Cap
|width=40%
|float=left
|position=right
|pos=right
|text-align=center
|align=center
|style=opacity:0.5
|visible=yes
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr", class_="infobox-key-value")
    keys = [
        r.find("strong").get_text(strip=True) for r in rows if r.find("strong")
    ]
    for excluded in (
        "caption",
        "width",
        "float",
        "position",
        "pos",
        "text-align",
        "align",
        "style",
    ):
        assert excluded not in keys
    assert "visible" in keys


def test_infobox_unicode_key():
    """Option keys may contain UTF-8 characters."""
    md = """
{{InfoBox
|Größe=180cm
|名前=Otter
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="infobox")
    assert table is not None
    rows = table.find_all("tr", class_="infobox-key-value")
    keys = {
        r.find("strong")
        .get_text(strip=True): r.find_all("td")[1]
        .get_text(strip=True)
        for r in rows
        if r.find("strong")
    }
    assert keys["Größe"] == "180cm"
    assert keys["名前"] == "Otter"


def test_infobox_escaped_equals_in_key():
    r"""Keys containing \= have the backslash-equals converted to =."""
    md = """
{{InfoBox
|a\\=b=value
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="infobox")
    assert table is not None
    rows = table.find_all("tr", class_="infobox-key-value")
    keys = {
        r.find("strong")
        .get_text(strip=True): r.find_all("td")[1]
        .get_text(strip=True)
        for r in rows
        if r.find("strong")
    }
    assert keys["a=b"] == "value"


def test_infobox_escape_characters_413():
    md = """
{{InfoBox
|caption=Issue #413
|Key=Value
|Key:=Value:
|•Key·=•Value·
|KeyA\\|=Value\\|
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="infobox")
    assert table is not None
    rows = table.find_all("tr", class_="infobox-key-value")
    keys = {
        r.find("strong")
        .get_text(strip=True): r.find_all("td")[1]
        .get_text(strip=True)
        for r in rows
        if r.find("strong")
    }
    assert keys["Key"] == "Value"
    assert keys["•Key·"] == "•Value·"
    assert keys["Key:"] == "Value:"
    assert keys["Key:"] == "Value:"
    assert keys["KeyA|"] == "Value|"


def test_infobox_escape_pipe():
    md = """
{{InfoBox
|caption=Escape a pipe
|KeyPipe\\|=ValuePipe\\|
|\\|LeadPipeKey=\\|ValuePipe
\\|Pipe in Args
Pipe in the middle\\|of the args
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="infobox")
    assert table is not None
    rows = table.find_all("tr", class_="infobox-key-value")
    keys = {
        r.find("strong")
        .get_text(strip=True): r.find_all("td")[1]
        .get_text(strip=True)
        for r in rows
        if r.find("strong")
    }
    assert keys["KeyPipe|"] == "ValuePipe|"
    assert keys["|LeadPipeKey"] == "|ValuePipe"
    # check args
    args = table.find("tr", class_="infobox-args")
    assert args
    assert "|Pipe in Args" in args.text
    assert "Pipe in the middle|of the args" in args.text


def test_infobox_unicode_key_with_escaped_equals():
    r"""Combine UTF-8 key with \= in the same embedding."""
    md = """
{{InfoBox
|Schlüssel\\=1=eins
|clé=deux
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="infobox")
    assert table is not None
    rows = table.find_all("tr", class_="infobox-key-value")
    keys = {
        r.find("strong")
        .get_text(strip=True): r.find_all("td")[1]
        .get_text(strip=True)
        for r in rows
        if r.find("strong")
    }
    assert keys["Schlüssel=1"] == "eins"
    assert keys["clé"] == "deux"


def test_infobox_args():
    """InfoBox with only body text."""
    md = """
{{InfoBox
And test all these as args : \\| \\= • ·
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="infobox")
    assert table is not None
    args = table.find("tr", class_="infobox-args")
    assert args
    assert "And test all these as args : | = • ·" in args.text


def test_infobox_no_content():
    """InfoBox with only key-value options and no body text."""
    md = """
{{InfoBox
|Answer=42
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    box = soup.find("div", class_="infobox")
    assert box is not None
    # no infobox-args row when there is no body content
    assert soup.find("tr", class_="infobox-args") is None
    rows = soup.find_all("tr", class_="infobox-key-value")
    assert len(rows) == 1
    assert "42" in rows[0].get_text()


def test_video_basic():
    md = """
{{Video
/static/otter.mp4
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    video = soup.find("video")
    assert video is not None
    source = video.find("source")
    assert source is not None
    assert source.get("src") == "/static/otter.mp4"
    assert source.get("type") == "video/mp4"


def test_video_width():
    md = """
{{Video
|width=60%
/static/otter.mp4
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    video = soup.find("video")
    assert video is not None
    assert video.get("width") == "60%"


def test_video_default_flags():
    """controls, muted and loop are on by default; autoplay is off."""
    md = """
{{Video
/static/otter.mp4
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    video = soup.find("video")
    assert video is not None
    attrs = video.attrs
    assert "controls" in attrs
    assert "muted" in attrs
    assert "loop" in attrs
    assert "autoplay" not in attrs


def test_video_flag_overrides():
    """autoplay=true enables it; controls=false removes it."""
    md = """
{{Video
|controls=false
|autoplay=true
|muted=false
|loop=false
/static/otter.mp4
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    video = soup.find("video")
    assert video is not None
    attrs = video.attrs
    assert "autoplay" in attrs
    assert "controls" not in attrs
    assert "muted" not in attrs
    assert "loop" not in attrs


def test_video_src_option():
    """src= option is equivalent to passing the URL as a body arg."""
    md = """
{{Video
|src=/static/otter.mp4
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    video = soup.find("video")
    assert video is not None
    source = video.find("source")
    assert source is not None
    assert source.get("src") == "/static/otter.mp4"


def test_video_ogg_type():
    md = """
{{Video
/static/otter.ogg
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    source = soup.find("source")
    assert source is not None
    assert source.get("type") == "video/ogg"


def test_video_unknown_extension():
    """Sources with unknown extensions get no type attribute."""
    md = """
{{Video
/static/otter.webm
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    source = soup.find("source")
    assert source is not None
    assert source.get("type") is None


def test_video_multiple_sources():
    md = """
{{Video
/static/otter.mp4
/static/otter.ogg
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    sources = soup.find_all("source")
    assert len(sources) == 2
    srcs = [s.get("src") for s in sources]
    assert "/static/otter.mp4" in srcs
    assert "/static/otter.ogg" in srcs


def test_video_no_src():
    """Missing src renders an error message, not a video element."""
    md = """
{{Video
}}
"""
    html, _, _ = render.markdown(md)
    assert "Error" in html
    assert "Video" in html
    soup = BeautifulSoup(html, "html.parser")
    assert soup.find("video") is None


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


def test_pageindex_embedding(create_app):
    author = ("Test Author", "test@example.com")
    # The parent page with the embedding
    create_app.storage.store(
        "indexpage.md",
        content="# Index\n{{PageIndex}}\n",
        author=author,
        message="add index page",
    )
    # Child pages below indexpage/
    create_app.storage.store(
        "indexpage/alpha.md",
        content="# Alpha\nAlpha page.",
        author=author,
        message="add alpha",
    )
    create_app.storage.store(
        "indexpage/beta.md",
        content="# Beta\nBeta page.",
        author=author,
        message="add beta",
    )
    # A sibling page that should NOT appear
    create_app.storage.store(
        "sibling.md",
        content="# Sibling\nSibling page.",
        author=author,
        message="add sibling",
    )
    client = create_app.test_client()
    response = client.get("/Indexpage/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    pi_div = soup.find("div", class_="pageindex-embedding")
    assert pi_div is not None
    contents = pi_div.decode_contents()
    assert "Alpha" in contents
    assert "Beta" in contents
    assert "Sibling" not in contents


def test_pageindex_embedding_src_filter(create_app):
    author = ("Test Author", "test@example.com")
    create_app.storage.store(
        "filterpage.md",
        content="# Filter\n{{PageIndex\n|src=Ca*\n}}\n",
        author=author,
        message="add filter page",
    )
    create_app.storage.store(
        "filterpage/cat.md",
        content="# Cat\nMeow.",
        author=author,
        message="add cat",
    )
    create_app.storage.store(
        "filterpage/car.md",
        content="# Car\nVroom.",
        author=author,
        message="add car",
    )
    create_app.storage.store(
        "filterpage/dog.md",
        content="# Dog\nWoof.",
        author=author,
        message="add dog",
    )
    client = create_app.test_client()
    response = client.get("/Filterpage/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    pi_div = soup.find("div", class_="pageindex-embedding")
    assert pi_div is not None
    contents = pi_div.decode_contents()
    assert "Cat" in contents
    assert "Car" in contents
    assert "Dog" not in contents


def test_pageindex_embedding_toc(create_app):
    author = ("Test Author", "test@example.com")
    create_app.storage.store(
        "tocindex.md",
        content="# Index\n{{PageIndex\n|toc=true\n}}\n",
        author=author,
        message="add toc index",
    )
    create_app.storage.store(
        "tocindex/tocpage.md",
        content="# Toc Page\n## Section One\n## Section Two\n",
        author=author,
        message="add toc page",
    )
    client = create_app.test_client()
    response = client.get("/Tocindex/view")
    assert response.status_code == 200
    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    pi_div = soup.find("div", class_="pageindex-embedding")
    assert pi_div is not None
    pagetoc = pi_div.find("div", class_="pagetoc")
    assert pagetoc is not None
    assert "Section One" in pagetoc.decode_contents()
    assert "Section Two" in pagetoc.decode_contents()


# ---------------------------------------------------------------------------
# Video embedding — YouTube
# ---------------------------------------------------------------------------


def _yt_iframe(html, index=0):
    """Return the nth iframe from parsed html."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.find_all("iframe")[index]


def test_video_youtube_watch_url():
    md = """\
{{Video
https://www.youtube.com/watch?v=dQw4w9WgXcQ
}}
"""
    html, _, _ = render.markdown(md)
    iframe = _yt_iframe(html)
    assert iframe is not None
    assert "dQw4w9WgXcQ" in iframe["src"]
    assert iframe["src"].startswith("https://www.youtube.com/embed/")


def test_video_youtube_short_url():
    md = """\
{{Video
https://youtu.be/dQw4w9WgXcQ
}}
"""
    html, _, _ = render.markdown(md)
    iframe = _yt_iframe(html)
    assert "dQw4w9WgXcQ" in iframe["src"]


def test_video_youtube_embed_url():
    md = """\
{{Video
https://www.youtube.com/embed/dQw4w9WgXcQ
}}
"""
    html, _, _ = render.markdown(md)
    iframe = _yt_iframe(html)
    assert "dQw4w9WgXcQ" in iframe["src"]


def test_video_youtube_default_options():
    """By default: controls shown, autoplay off, muted on, loop on."""
    md = """\
{{Video
https://youtu.be/dQw4w9WgXcQ
}}
"""
    html, _, _ = render.markdown(md)
    iframe = _yt_iframe(html)
    src = iframe["src"]
    assert "dQw4w9WgXcQ" in src
    # controls on by default — no controls=0
    assert "controls=0" not in src
    # autoplay off by default
    assert "autoplay" not in src
    # muted on by default
    assert "mute=1" in src
    # loop on by default, requires playlist param
    assert "loop=1" in src
    assert "playlist=dQw4w9WgXcQ" in src


def test_video_youtube_autoplay():
    md = """\
{{Video
|autoplay=true
https://youtu.be/dQw4w9WgXcQ
}}
"""
    html, _, _ = render.markdown(md)
    iframe = _yt_iframe(html)
    assert "autoplay=1" in iframe["src"]


def test_video_youtube_muted():
    md = """\
{{Video
|muted=true
https://youtu.be/dQw4w9WgXcQ
}}
"""
    html, _, _ = render.markdown(md)
    iframe = _yt_iframe(html)
    assert "mute=1" in iframe["src"]


def test_video_youtube_controls_off():
    md = """\
{{Video
|controls=false
https://youtu.be/dQw4w9WgXcQ
}}
"""
    html, _, _ = render.markdown(md)
    iframe = _yt_iframe(html)
    assert "controls=0" in iframe["src"]


def test_video_youtube_loop():
    md = """\
{{Video
|loop=true
https://youtu.be/dQw4w9WgXcQ
}}
"""
    html, _, _ = render.markdown(md)
    iframe = _yt_iframe(html)
    assert "loop=1" in iframe["src"]
    # YouTube requires playlist=VIDEO_ID for loop to work
    assert "playlist=dQw4w9WgXcQ" in iframe["src"]


def test_video_youtube_width():
    md = """\
{{Video
|width=80%
https://youtu.be/dQw4w9WgXcQ
}}
"""
    html, _, _ = render.markdown(md)
    iframe = _yt_iframe(html)
    assert iframe["width"] == "80%"


def test_video_youtube_multiple():
    md = """\
{{Video
https://youtu.be/dQw4w9WgXcQ
https://www.youtube.com/watch?v=5VmZFvJg7ro
}}
"""
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    iframes = soup.find_all("iframe")
    assert len(iframes) == 2
    srcs = [f["src"] for f in iframes]
    assert any("dQw4w9WgXcQ" in s for s in srcs)
    assert any("5VmZFvJg7ro" in s for s in srcs)


def test_video_youtube_src_option():
    """YouTube URL passed via |src= option should render as an iframe."""
    md = """\
{{Video
|src=https://youtu.be/dQw4w9WgXcQ
}}
"""
    html, _, _ = render.markdown(md)
    iframe = _yt_iframe(html)
    assert iframe is not None
    assert "dQw4w9WgXcQ" in iframe["src"]


def test_video_youtube_mixed_sources_raises_error():
    md = """\
{{Video
https://youtu.be/dQw4w9WgXcQ
/path/to/video.mp4
}}
"""
    html, _, _ = render.markdown(md)
    assert "Cannot mix YouTube links and file sources" in html


def test_video_youtube_mobile_url():
    md = """\
{{Video
https://m.youtube.com/watch?v=dQw4w9WgXcQ
}}
"""
    html, _, _ = render.markdown(md)
    iframe = _yt_iframe(html)
    assert iframe is not None
    assert "dQw4w9WgXcQ" in iframe["src"]


def test_video_youtube_e_path_url():
    md = """\
{{Video
https://m.youtube.com/e/dQw4w9WgXcQ
}}
"""
    html, _, _ = render.markdown(md)
    iframe = _yt_iframe(html)
    assert iframe is not None
    assert "dQw4w9WgXcQ" in iframe["src"]
