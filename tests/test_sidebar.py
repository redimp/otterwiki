#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

from bs4 import BeautifulSoup


def get_sidebar_shortcuts(test_client):
    rv = test_client.get("/")
    assert rv.status_code == 200
    soup = BeautifulSoup(rv.data.decode(), "html.parser")
    sidebar_menu = soup.find_all("div", class_="sidebar-menu")
    assert len(sidebar_menu) == 1
    sidebar_shortcuts = sidebar_menu[0].find_all(
        "a", class_="sidebar-link-with-icon"
    )
    sidebar_shortcuts = [
        (x.text.strip(), x["href"]) for x in sidebar_shortcuts
    ]

    dropdown_menu = soup.find_all("div", class_="dropdown-menu")
    assert len(dropdown_menu) == 1
    dropdown_shortcuts = dropdown_menu[0].find_all(
        "a", class_="dropdown-item-with-icon"
    )
    dropdown_shortcuts = [
        (x.text.strip(), x["href"]) for x in dropdown_shortcuts
    ]

    return sidebar_shortcuts, dropdown_shortcuts


def test_sidebar_shortcuts(create_app, test_client):
    # test the default settings
    create_app.config["SIDEBAR_SHORTCUTS"] = "home pageindex createpage"
    sidebar_shortcuts, dropdown_shortcuts = get_sidebar_shortcuts(test_client)
    assert ('Home', '/') in sidebar_shortcuts
    assert ('A - Z', '/-/index') in sidebar_shortcuts
    assert ('Create page', '/-/create') in sidebar_shortcuts
    assert ("Changelog", "/-/changelog") not in sidebar_shortcuts

    assert ('Home', '/') not in dropdown_shortcuts
    assert ('A - Z', '/-/index') not in dropdown_shortcuts
    assert ('Create page', '/-/create') not in dropdown_shortcuts
    assert ("Changelog", "/-/changelog") in dropdown_shortcuts

    # change preferences
    create_app.config["SIDEBAR_SHORTCUTS"] = "changelog"
    assert ("Changelog", "/-/changelog") not in sidebar_shortcuts


def test_sidebar_shortcuts_empty(create_app, test_client):
    create_app.config["SIDEBAR_SHORTCUTS"] = ""
    sidebar_shortcuts, dropdown_shortcuts = get_sidebar_shortcuts(test_client)

    assert ('Home', '/') not in sidebar_shortcuts
    assert ('A - Z', '/-/index') not in sidebar_shortcuts
    assert ('Create page', '/-/create') not in sidebar_shortcuts
    assert ("Changelog", "/-/changelog") not in sidebar_shortcuts

    assert ('A - Z', '/-/index') in dropdown_shortcuts
    assert ('Create page', '/-/create') in dropdown_shortcuts
    assert ("Changelog", "/-/changelog") in dropdown_shortcuts
