#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring, indent
from flask import url_for, make_response, abort
from otterwiki.server import app, storage
from otterwiki.auth import has_permission
from otterwiki.helper import get_pagename, get_filename


def sitemap():
    """Generate XML sitemap for the wiki."""
    if not has_permission("READ"):
        abort(403)

    urlset = Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

    # Get all markdown files from storage
    files, _ = storage.list()
    md_files = [f for f in files if f.endswith('.md')]

    # Add each wiki page to sitemap
    for filename in md_files:
        try:
            metadata = storage.metadata(filename)
            url_elem = SubElement(urlset, 'url')
            pagepath = get_pagename(filename, full=True)

            # handle configured home page as / in URL generation
            home_page = app.config.get("HOME_PAGE", "")
            is_home_page = False

            if not home_page and pagepath.lower() == 'home':
                is_home_page = True
            elif home_page and not home_page.startswith("/-/"):
                # custom page - normalize both paths for comparison
                custom_page_normalized = get_filename(
                    home_page.strip("/")
                ).replace(".md", "")
                current_page_normalized = filename.replace(".md", "")
                if app.config.get("RETAIN_PAGE_NAME_CASE"):
                    is_home_page = (
                        custom_page_normalized == current_page_normalized
                    )
                else:
                    is_home_page = (
                        custom_page_normalized.lower()
                        == current_page_normalized.lower()
                    )

            if is_home_page:
                page_url = url_for('index', _external=True)
            else:
                page_url = url_for('view', path=pagepath, _external=True)

            # post-processing to encode the quotes
            page_url = page_url.replace("'", "%27")
            page_url = page_url.replace('"', "%22")

            loc = SubElement(url_elem, 'loc')
            loc.text = page_url

            if metadata and 'datetime' in metadata:
                lastmod = SubElement(url_elem, 'lastmod')
                lastmod.text = metadata['datetime'].strftime('%Y-%m-%d')

            # Calculate priority based on depth
            # 1.0 for root, 0.9 for level 1, 0.8 for level 2, etc.
            # Minimum is 0.1
            priority = SubElement(url_elem, 'priority')
            if pagepath.lower() == 'home' or pagepath == '':
                depth = 0
            else:
                depth = pagepath.count('/')
            calculated_priority = max(1.0 - (depth * 0.1), 0.1)
            priority.text = f'{calculated_priority:.1f}'

        except Exception as e:
            app.logger.warning(f"Skipping {filename} in sitemap: {e}")
            continue

    indent(urlset, space="  ", level=0)
    xml_string = tostring(
        urlset, encoding='utf-8', method='xml', xml_declaration=True
    )
    response = make_response(xml_string)
    response.headers['Content-Type'] = 'application/xml; charset=utf-8'
    return response
