#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

from xml.etree.ElementTree import fromstring
from bs4 import BeautifulSoup


def test_sitemap(admin_client):
    """Test sitemap generation and XML validity."""
    response = admin_client.get("/sitemap.xml")
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/xml; charset=utf-8'
    root = fromstring(response.data)
    assert root.tag == '{http://www.sitemaps.org/schemas/sitemap/0.9}urlset'


def test_home_page_sitemap_default(app_with_user, test_client):
    """Test sitemap generation with default home page."""
    app_with_user.config["HOME_PAGE"] = ""
    app_with_user.config["READ_ACCESS"] = "ANONYMOUS"

    # Create pages
    test_client.post(
        "/Home/save",
        data={
            "content": "# Home\n\nHome page.",
            "commit": "Create home",
        },
    )
    test_client.post(
        "/About/save",
        data={
            "content": "# About\n\nAbout page.",
            "commit": "Create about",
        },
    )

    # Get sitemap
    response = test_client.get("/sitemap.xml")
    assert response.status_code == 200
    xml = response.data.decode()

    # Home page should have root URL in sitemap
    soup = BeautifulSoup(xml, "xml")
    locs = [loc.text for loc in soup.find_all("loc")]

    # Should have root URL for home page
    root_urls = [
        loc for loc in locs if loc.endswith("/") and loc.count("/") == 3
    ]
    assert len(root_urls) >= 1


def test_home_page_sitemap_custom(app_with_user, test_client):
    """Test sitemap generation with custom home page."""
    app_with_user.config["READ_ACCESS"] = "ANONYMOUS"

    # Create pages
    test_client.post(
        "/Landing/save",
        data={
            "content": "# Landing\n\nLanding page.",
            "commit": "Create landing",
        },
    )
    test_client.post(
        "/About/save",
        data={
            "content": "# About\n\nAbout page.",
            "commit": "Create about",
        },
    )

    # Set custom home page
    app_with_user.config["HOME_PAGE"] = "Landing"

    # Get sitemap
    response = test_client.get("/sitemap.xml")
    assert response.status_code == 200
    xml = response.data.decode()

    # Landing page should have root URL in sitemap
    soup = BeautifulSoup(xml, "xml")
    locs = [loc.text for loc in soup.find_all("loc")]

    # Should have root URL for landing page
    root_urls = [
        loc for loc in locs if loc.endswith("/") and loc.count("/") == 3
    ]
    assert len(root_urls) >= 1
