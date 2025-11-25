#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

from xml.etree.ElementTree import fromstring


def test_sitemap(admin_client):
    """Test sitemap generation and XML validity."""
    response = admin_client.get("/sitemap.xml")
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/xml; charset=utf-8'
    root = fromstring(response.data)
    assert root.tag == '{http://www.sitemaps.org/schemas/sitemap/0.9}urlset'
