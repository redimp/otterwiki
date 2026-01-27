#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import bs4


def test_canonical_links(app_with_user, test_client):
    # root URL "/" should have canonical pointing to itself (/)
    response = test_client.get("/")
    assert response.status_code == 200
    html = response.data.decode()
    soup = bs4.BeautifulSoup(html, "html.parser")

    canonical = soup.find("link", rel="canonical")
    assert canonical is not None, "Canonical link not found on /"
    canonical_url = canonical.get("href")
    assert (
        canonical_url.endswith("/") and not "/Home" in canonical_url
    ), f"Root canonical should point to /, got: {canonical_url}"

    # /Home should have canonical pointing to / (root)
    response = test_client.get("/Home")
    assert response.status_code == 200
    html = response.data.decode()
    soup = bs4.BeautifulSoup(html, "html.parser")

    canonical = soup.find("link", rel="canonical")
    assert canonical is not None, "Canonical link not found on /Home"
    canonical_url = canonical.get("href")
    assert (
        canonical_url.endswith("/") and not "/Home" in canonical_url
    ), f"/Home canonical should point to /, got: {canonical_url}"

    # create a test page
    pagename = "Test Page"
    content = "# Test Page\n\nThis is a test page."

    response = test_client.post(
        f"/{pagename}/save",
        data={"content": content, "commit": "Test canonical"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    # check canonical without trailing slash
    html = response.data.decode()
    soup = bs4.BeautifulSoup(html, "html.parser")
    canonical = soup.find("link", rel="canonical")
    assert canonical is not None, "Canonical link not found on test page"
    canonical_url = canonical.get("href")
    assert (
        "/Test%20Page" in canonical_url
    ), f"Test page canonical incorrect, got: {canonical_url}"

    # check canonical with trailing slash (should be same)
    response = test_client.get(f"/{pagename}/")
    assert response.status_code == 200
    html = response.data.decode()
    soup = bs4.BeautifulSoup(html, "html.parser")
    canonical = soup.find("link", rel="canonical")
    assert (
        canonical is not None
    ), "Canonical link not found on test page with trailing slash"
    canonical_url_slash = canonical.get("href")
    assert (
        canonical_url == canonical_url_slash
    ), "Canonical should be same with/without trailing slash"

    # test canonical URL with custom home page
    app_with_user.config["READ_ACCESS"] = "ANONYMOUS"

    test_client.post(
        "/Start/save",
        data={
            "content": "# Start\n\nStart page.",
            "commit": "Create start",
        },
    )

    app_with_user.config["HOME_PAGE"] = "Start"

    # check root URL points to /
    response = test_client.get("/")
    soup = bs4.BeautifulSoup(response.data.decode(), "html.parser")
    canonical = soup.find("link", rel="canonical")
    assert canonical is not None
    assert canonical.get("href").endswith("/")

    # check /Start URL also points to /
    response = test_client.get("/Start")
    soup = bs4.BeautifulSoup(response.data.decode(), "html.parser")
    canonical = soup.find("link", rel="canonical")
    assert canonical is not None
    assert canonical.get("href").endswith("/")


def test_meta_description_uses_site_description(test_client, create_app):
    test_description = "This is a test wiki"
    create_app.config["SITE_DESCRIPTION"] = test_description

    response = test_client.get("/")
    assert response.status_code == 200
    html = response.data.decode()
    soup = bs4.BeautifulSoup(html, "html.parser")

    meta_desc = soup.find("meta", attrs={"name": "description"})
    assert meta_desc is not None, "Meta description not found"

    description = meta_desc.get("content")
    assert (
        description == test_description
    ), f"Expected '{test_description}', got '{description}'"
