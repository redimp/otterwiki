# vim: set et ts=8 sts=4 sw=4 ai:

"""
Pages with dots in the filename, added via git, can be reached via the URL
with the .md suffix, see #612.
"""

import pytest

from otterwiki.util import sanitize_dotted_pagepath

AUTHOR = ("Test", "test@example.org")


def test_sanitize_dotted_pagepath():
    assert sanitize_dotted_pagepath("docs/version1.2.md") == (
        "docs/version1.2.md"
    )
    assert sanitize_dotted_pagepath("v1.2/page.md") == "v1.2/page.md"
    assert sanitize_dotted_pagepath("what?1.2.md") == "what1.2.md"
    # no .md suffix
    assert sanitize_dotted_pagepath("docs/version1.2") is None
    # segments starting with a dot
    assert sanitize_dotted_pagepath("../settings.md") is None
    assert sanitize_dotted_pagepath("docs/../../settings.md") is None
    assert sanitize_dotted_pagepath("./page.md") is None
    assert sanitize_dotted_pagepath("docs/.git/config.md") is None
    assert sanitize_dotted_pagepath("docs/.hidden.md") is None
    assert sanitize_dotted_pagepath(".md") is None


@pytest.fixture
def dotted(create_app):
    storage = create_app.storage
    storage.store("docs/version12.md", "# Version12\n\nAAA", author=AUTHOR)
    storage.store("docs/version1.2.md", "# Version1.2\n\nBBB", author=AUTHOR)
    storage.store("v1.2/page.md", "# Page\n\nCCC", author=AUTHOR)
    storage.store("docs/version1.2/file.txt", "DDD", author=AUTHOR)
    return create_app


def test_resolve_dotted_pagepath(dotted, req_ctx):
    from otterwiki.helper import (
        get_pagepath_for_url,
        resolve_dotted_pagepath,
    )

    assert resolve_dotted_pagepath("Docs/Version1.2.md") == (
        "Docs/Version1.2.md"
    )
    assert resolve_dotted_pagepath("v1.2/page.md") == "v1.2/page.md"
    # without the .md suffix the old behavior is used
    assert resolve_dotted_pagepath("Docs/Version1.2") is None
    # no dots, no change
    assert resolve_dotted_pagepath("Docs/Version12.md") is None
    # missing files
    assert resolve_dotted_pagepath("Docs/Version1.3.md") is None
    assert resolve_dotted_pagepath("../docs/version1.2.md") is None

    assert get_pagepath_for_url("docs/version12.md") == "Docs/Version12"
    assert get_pagepath_for_url("docs/version1.2.md") == ("Docs/Version1.2.md")
    assert get_pagepath_for_url("v1.2/page.md") == "V1.2/Page.md"


def test_view_dotted_page(dotted, test_client):
    html = test_client.get("/Docs/Version1.2.md").data.decode()
    assert "BBB" in html
    assert "AAA" not in html
    html = test_client.get("/V1.2/Page.md").data.decode()
    assert "CCC" in html
    # the plain URL keeps the old behavior
    html = test_client.get("/Docs/Version1.2").data.decode()
    assert "AAA" in html
    assert "BBB" not in html
    # a page without dots works with and without the .md suffix
    for url in ["/Docs/Version12", "/Docs/Version12.md"]:
        html = test_client.get(url).data.decode()
        assert "AAA" in html
    # a missing file with dots falls back to the old behavior
    html = test_client.get("/Docs/Version1.3.md").data.decode()
    assert "BBB" not in html
    assert "AAA" not in html


def test_dotted_page_links(dotted, test_client):
    # page index
    html = test_client.get("/-/index").data.decode()
    assert 'href="/Docs/Version1.2.md"' in html
    assert 'href="/V1.2/Page.md"' in html
    assert 'href="/Docs/Version12"' in html
    # sidebar
    html = test_client.get("/Docs/Version1.2.md").data.decode()
    assert 'href="/Docs/Version1.2.md"' in html
    # search
    html = test_client.get("/-/search/BBB").data.decode()
    assert 'href="/Docs/Version1.2.md"' in html
    html = test_client.get("/-/search/CCC").data.decode()
    assert 'href="/V1.2/Page.md"' in html
    # sitemap
    xml = test_client.get("/sitemap.xml").data.decode()
    assert "/Docs/Version1.2.md</loc>" in xml
    assert "/Docs/Version12</loc>" in xml
    # changelog
    html = test_client.get("/-/changelog").data.decode()
    assert 'href="/Docs/Version1.2.md' in html


def test_dotted_page_attachment(dotted, test_client):
    rv = test_client.get("/Docs/Version1.2.md/a/file.txt")
    assert rv.status_code == 200
    assert rv.data == b"DDD"
    rv = test_client.get("/Docs/Version1.2.md/file.txt")
    assert rv.status_code == 200
    assert rv.data == b"DDD"


def test_save_dotted_page(dotted, test_client):
    storage = dotted.storage
    html = test_client.post(
        "/Docs/Version1.2.md/save",
        data={
            "content": "# Version1.2\n\nEEE",
            "commit": "update dotted page",
        },
        follow_redirects=True,
    ).data.decode()
    assert "EEE" in html
    assert "EEE" in storage.load("docs/version1.2.md")
    assert "AAA" in storage.load("docs/version12.md")
    assert not storage.exists("docs/version1.2.md.md")


def test_dotted_page_retain_case(create_app, test_client):
    create_app.config["RETAIN_PAGE_NAME_CASE"] = True
    try:
        storage = create_app.storage
        storage.store("Docs/Version12.md", "# Version12\n\nAAA", author=AUTHOR)
        storage.store(
            "Docs/Version1.2.md", "# Version1.2\n\nBBB", author=AUTHOR
        )
        html = test_client.get("/Docs/Version1.2.md").data.decode()
        assert "BBB" in html
        html = test_client.get("/-/index").data.decode()
        assert 'href="/Docs/Version1.2.md"' in html
        assert 'href="/Docs/Version12"' in html
    finally:
        create_app.config["RETAIN_PAGE_NAME_CASE"] = False


def test_sanitize_dotted_pagepath_without_dot():
    # without a dot in the name the plain pagepath reaches the file
    assert sanitize_dotted_pagepath("docs/version12.md") is None
