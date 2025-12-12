#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

from bs4 import BeautifulSoup


def get_sidebar_shortcuts(test_client):
    """
    Helper function to get all links from the sidebar and the dropdown menu.
    """
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


def get_sidebar_menu(test_client):
    """
    Helper function to get all elements in the custom menu including links and separators
    """
    rv = test_client.get("/")
    assert rv.status_code == 200
    soup = BeautifulSoup(rv.data.decode(), "html.parser")
    sidebar_custom_menu = soup.find("div", id="custom-menu")
    if sidebar_custom_menu is None:
        return None

    menu_items = []
    ul = sidebar_custom_menu.find("ul")
    if ul:
        for li in ul.find_all("li"):
            if li.find("hr"):
                menu_items.append({"type": "separator"})
            elif li.find("a"):
                a = li.find("a")
                menu_items.append(
                    {
                        "type": "link",
                        "text": a.text.strip(),
                        "href": a["href"],
                        "html": str(a),
                    }
                )

    # for backward compatibility, also return just the links in the old format
    sidebar_custom_links = [
        (item["text"], item["href"])
        for item in menu_items
        if item["type"] == "link"
    ]

    return {"items": menu_items, "links": sidebar_custom_links}


def test_sidebar_custom_menu(create_app, test_client, req_ctx):
    from otterwiki.sidebar import SidebarMenu

    create_app.config["SIDEBAR_CUSTOM_MENU"] = ""
    assert SidebarMenu().config == []
    menu_data = get_sidebar_menu(test_client)
    assert menu_data is None

    create_app.config["SIDEBAR_CUSTOM_MENU"] = "[]"
    assert [] == SidebarMenu().config
    menu_data = get_sidebar_menu(test_client)
    assert menu_data is None

    create_app.config["SIDEBAR_CUSTOM_MENU"] = (
        """[{"link": "Home", "title": ""}]"""
    )
    assert [{'link': 'Home', 'title': '', 'icon': ''}] == SidebarMenu().config
    menu_data = get_sidebar_menu(test_client)
    assert menu_data
    assert ('Home', '/Home') in menu_data["links"]

    create_app.config["SIDEBAR_CUSTOM_MENU"] = (
        """[{"link":"https://example.com", "title":"Example"}]"""
    )
    assert {
        "title": "Example",
        "link": "https://example.com",
        "icon": "",
    } in SidebarMenu().config
    menu_data = get_sidebar_menu(test_client)
    assert menu_data
    assert ('Example', 'https://example.com') in menu_data["links"]

    create_app.config["SIDEBAR_CUSTOM_MENU"] = (
        """[{"link": "/Example", "title": ""}]"""
    )
    assert [
        {'link': '/Example', 'title': '', 'icon': ''}
    ] == SidebarMenu().config
    menu_data = get_sidebar_menu(test_client)
    assert menu_data
    assert ('/Example', '/Example') in menu_data["links"]


def test_sidebar_custom_menu_error(create_app, test_client, req_ctx):
    from otterwiki.sidebar import SidebarMenu

    create_app.config["SIDEBAR_CUSTOM_MENU"] = "["
    assert SidebarMenu().config == []
    menu_data = get_sidebar_menu(test_client)
    assert menu_data is None


def test_sidebar_custom_menu_with_icons(create_app, test_client, req_ctx):
    from otterwiki.sidebar import SidebarMenu

    create_app.config["SIDEBAR_CUSTOM_MENU"] = (
        """[{"link": "Home", "title": "Home Page", "icon": "<i class=\\"fas fa-home\\"></i>"}]"""
    )
    config = SidebarMenu().config
    assert len(config) == 1
    assert config[0]["link"] == "Home"
    assert config[0]["title"] == "Home Page"
    assert config[0]["icon"] == '<i class="fas fa-home"></i>'

    menu_data = get_sidebar_menu(test_client)
    assert menu_data is not None
    assert len(menu_data["items"]) == 1
    assert menu_data["items"][0]["type"] == "link"
    assert '<i class="fas fa-home"></i>' in menu_data["items"][0]["html"]
    assert "Home Page" in menu_data["items"][0]["text"]


def test_sidebar_custom_menu_with_separator(create_app, test_client, req_ctx):
    from otterwiki.sidebar import SidebarMenu

    create_app.config["SIDEBAR_CUSTOM_MENU"] = (
        """[{"link": "Home", "title": "Home Page", "icon": ""}, {"link": "---", "title": "", "icon": ""}, {"link": "About", "title": "About Page", "icon": ""}]"""
    )
    config = SidebarMenu().config
    assert len(config) == 3

    menu_data = get_sidebar_menu(test_client)
    assert menu_data is not None
    assert len(menu_data["items"]) == 3
    assert menu_data["items"][0]["type"] == "link"
    assert menu_data["items"][1]["type"] == "separator"
    assert menu_data["items"][2]["type"] == "link"


def test_sidebar_custom_menu_backward_compatibility(
    create_app, test_client, req_ctx
):
    from otterwiki.sidebar import SidebarMenu

    create_app.config["SIDEBAR_CUSTOM_MENU"] = (
        """[{"link": "Home", "title": "Home Page"}]"""
    )
    config = SidebarMenu().config
    assert len(config) == 1
    assert config[0]["link"] == "Home"
    assert config[0]["title"] == "Home Page"
    assert config[0]["icon"] == ""

    menu_data = get_sidebar_menu(test_client)
    assert menu_data is not None
    assert ("Home Page", "/Home") in menu_data["links"]
