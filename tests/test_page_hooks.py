#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
The hooks a plugin uses to arrange pages in folders, e.g. one folder per
language: page_list_filter, breadcrumbs_filter, page_menu_entries,
page_new_content and resolve_wikilink.
"""

import pytest

from otterwiki.plugins import hookimpl, plugin_manager

AUTHOR = ("Hook Tester", "hooks@example.com")


class FolderPlugin:
    """Keeps to the fr/ folder, like a multilingual plugin would."""

    def __init__(self):
        self.rendered_pages = []

    @hookimpl
    def page_list_filter(self, filenames, context):
        filenames[:] = [f for f in filenames if f.startswith("fr/")]

    @hookimpl
    def breadcrumbs_filter(self, breadcrumbs, pagepath):
        if breadcrumbs and breadcrumbs[0][1].lower() == "fr":
            del breadcrumbs[0]

    @hookimpl
    def page_menu_entries(self, pagepath):
        return [
            {
                "url": f"/de/{pagepath}",
                "label": "Translate into Deutsch",
                "icon": "fas fa-language",
            }
        ]

    @hookimpl
    def admin_menu_entries(self):
        return [
            {
                "url": "/-/admin/plugin/folders/settings",
                "label": "Folder Settings",
                "icon": "fas fa-folder",
            }
        ]

    @hookimpl
    def page_language(self, pagepath):
        if pagepath.lower().startswith("fr/"):
            return "fr"
        return None

    @hookimpl
    def page_new_content(self, pagepath):
        if pagepath.lower().startswith("de/"):
            return "# Neue Seite\n\n"
        return None

    @hookimpl
    def resolve_wikilink(self, link, source_pagepath):
        if source_pagepath and source_pagepath.lower().startswith("fr/"):
            if not link.lower().startswith("/fr/"):
                return "/fr" + link
        return None

    @hookimpl
    def renderer_process_wikilink(
        self, wikilink_html, wikilink_url, wikilink_text, page
    ):
        self.rendered_pages.append(page)
        return wikilink_html


@pytest.fixture
def plugin(create_app):
    from otterwiki.server import storage

    storage.store("home.md", "# Home\n", author=AUTHOR, message="home")
    storage.store(
        "fr/setup.md", "# Installation\n", author=AUTHOR, message="1"
    )
    storage.store(
        "fr/index.md",
        "# Index\n\nSee [[Setup]].\n",
        author=AUTHOR,
        message="2",
    )
    storage.store("en/setup.md", "# Setup\n", author=AUTHOR, message="3")
    plugin = FolderPlugin()
    plugin_manager.register(plugin)
    yield plugin
    plugin_manager.unregister(plugin)


def main_content(html):
    # the page without the sidebar, which has its own filter hook
    return html.split('id="content-wrapper"', 1)[1]


def test_page_list_filter_pageindex(plugin, test_client):
    html = main_content(test_client.get("/-/index").data.decode())
    assert 'href="/Fr/Setup"' in html
    assert 'href="/Fr/Index"' in html
    assert 'href="/En/Setup"' not in html
    assert 'href="/Home"' not in html


def test_page_list_filter_search(plugin, test_client):
    html = main_content(test_client.get("/-/search/Setup").data.decode())
    assert "/Fr/Index" in html
    assert "/En/Setup" not in html


def test_page_list_filter_sitemap(plugin, test_client):
    xml = test_client.get("/sitemap.xml").data.decode()
    assert "Setup" in xml
    assert "/en/" not in xml.lower()
    assert "/home" not in xml.lower()


def test_breadcrumbs_filter(plugin, test_client):
    from otterwiki.helper import get_breadcrumbs

    with test_client.application.test_request_context():
        crumbs = get_breadcrumbs("fr/Setup")
    assert [path for _name, path in crumbs] == ["fr/Setup"]


def test_page_menu_entries(plugin, test_client):
    html = test_client.get("/fr/Setup").data.decode()
    assert 'href="/de/fr/Setup"' in html
    assert "Translate into Deutsch" in html
    assert "fas fa-language" in html


def test_page_new_content(plugin, test_client):
    html = test_client.get("/de/Setup?edit").data.decode()
    assert "# Neue Seite" in html
    # the other pages keep the default
    html = test_client.get("/it/Setup?edit").data.decode()
    assert "# Setup" in html


def test_resolve_wikilink(plugin, test_client):
    html = test_client.get("/fr/Index").data.decode()
    assert 'href="/fr/Setup"' in html
    # the renderer hooks now get the page that is rendered
    assert plugin.rendered_pages
    assert plugin.rendered_pages[-1].pagepath.lower() == "fr/index"


def test_resolve_wikilink_keeps_links_outside_the_folder(plugin, test_client):
    from otterwiki.server import storage

    storage.store("other.md", "See [[Setup]].\n", author=AUTHOR, message="4")
    html = test_client.get("/Other").data.decode()
    assert 'href="/Setup"' in html


def test_rename_rewrites_resolved_wikilinks(plugin, create_app):
    from otterwiki.backlinks import rename_backlinks
    from otterwiki.server import storage

    with create_app.test_request_context():
        updated = rename_backlinks("fr/Setup", "fr/Install")
    # the link stays written relative to the folder
    assert updated["fr/index.md"] == "# Index\n\nSee [[Install]].\n"
    assert "fr/index.md" in updated
    assert storage.load("en/setup.md") == "# Setup\n"


def test_rename_out_of_the_folder_writes_the_full_path(plugin, create_app):
    from otterwiki.backlinks import rename_backlinks

    with create_app.test_request_context():
        updated = rename_backlinks("fr/Setup", "Archive/Setup")
    assert updated["fr/index.md"] == "# Index\n\nSee [[Archive/Setup]].\n"


def test_hooks_without_plugin(create_app, test_client):
    # nothing registered: everything as before
    from otterwiki.server import storage

    storage.store(
        "fr/setup.md", "# Installation\n", author=AUTHOR, message="1"
    )
    html = main_content(test_client.get("/-/index").data.decode())
    assert 'href="/Fr/Setup"' in html
    assert 'href="/Home"' in html
    html = test_client.get("/de/Setup?edit").data.decode()
    assert "# Setup" in html


def test_admin_menu_entries(plugin, admin_client):
    html = admin_client.get("/-/admin").data.decode()
    assert 'href="/-/admin/plugin/folders/settings"' in html
    assert "Folder Settings" in html


def test_page_language(plugin, test_client, create_app):
    # SITE_LANG is en, the interface English: a page of fr/ gets a badge
    storage = create_app.storage
    storage.store(
        "fr/guide.md", "# Guide\n\n## Partie\n", author=AUTHOR, message="g"
    )
    html = test_client.get("/fr/Guide").data.decode()
    assert ">FR</span>" in html
    html = test_client.get("/Home").data.decode()
    assert "language-badge" not in html
