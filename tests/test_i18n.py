#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import re

import pytest

ENGLISH = "Lost your password?"
FRENCH = "Mot de passe oublié ?"


def login_page(client, **headers):
    return client.get("/-/login", headers=headers).data.decode()


def test_english_by_default(create_app, test_client):
    assert create_app.config["SITE_LANG"] == "en"
    assert create_app.config["LANGUAGE_FROM_BROWSER"] is False
    assert create_app.config["LANGUAGE_MENU"] is False
    html = login_page(test_client)
    assert '<html lang="en"' in html
    assert ENGLISH in html
    assert 'placeholder="Search"' in html


def test_site_lang(create_app, test_client):
    create_app.config["SITE_LANG"] = "fr"
    html = login_page(test_client)
    assert '<html lang="fr"' in html
    assert FRENCH in html
    assert 'placeholder="Rechercher"' in html


@pytest.mark.parametrize("site_lang", ["fr-FR", "fr_FR", " fr-CA "])
def test_site_lang_with_region(create_app, test_client, site_lang):
    create_app.config["SITE_LANG"] = site_lang
    assert FRENCH in login_page(test_client)


@pytest.mark.parametrize("site_lang", ["xx", ""])
def test_site_lang_without_translation(create_app, test_client, site_lang):
    # the content of the wiki can be in a language the interface
    # isn't translated to yet: the interface stays in English
    create_app.config["SITE_LANG"] = site_lang
    assert ENGLISH in login_page(test_client)


def test_browser_ignored_by_default(create_app, test_client):
    assert ENGLISH in login_page(test_client, **{"Accept-Language": "fr"})


def test_browser_language(create_app, test_client):
    create_app.config["LANGUAGE_FROM_BROWSER"] = True
    html = login_page(test_client, **{"Accept-Language": "fr-CA,fr;q=0.9"})
    assert '<html lang="en"' in html  # the language of the content
    assert FRENCH in html
    # no catalog for the browser's languages: SITE_LANG
    create_app.config["SITE_LANG"] = "fr"
    assert FRENCH in login_page(test_client, **{"Accept-Language": "de"})
    # English is available too, and preferred over French
    assert ENGLISH in login_page(
        test_client, **{"Accept-Language": "de,en;q=0.8,fr;q=0.5"}
    )


def test_language_menu_hidden_by_default(create_app, test_client):
    html = test_client.get("/").data.decode()
    assert "/-/language/" not in html
    assert test_client.get("/-/language/fr").status_code == 404


def test_language_menu(create_app, test_client):
    create_app.config["LANGUAGE_MENU"] = True
    html = test_client.get("/").data.decode()
    assert "/-/language/fr" in html
    assert "Français" in html
    assert "English" in html
    rv = test_client.get("/-/language/fr?next=/-/login")
    assert rv.status_code == 302
    assert rv.headers["Location"] == "/-/login"
    assert "otterwiki_language=fr" in rv.headers["Set-Cookie"]
    # the cookie set by the menu wins over the browser and SITE_LANG
    create_app.config["LANGUAGE_FROM_BROWSER"] = True
    html = login_page(test_client, **{"Accept-Language": "en"})
    assert FRENCH in html
    test_client.get("/-/language/en")
    assert ENGLISH in login_page(test_client, **{"Accept-Language": "fr"})


def test_language_menu_disabled_ignores_cookie(create_app, test_client):
    create_app.config["LANGUAGE_MENU"] = True
    test_client.get("/-/language/fr")
    create_app.config["LANGUAGE_MENU"] = False
    assert ENGLISH in login_page(test_client)


def test_language_menu_single_language(create_app, test_client, monkeypatch):
    import otterwiki.server

    create_app.config["LANGUAGE_MENU"] = True
    monkeypatch.setattr(otterwiki.server, "available_locales", lambda: ["en"])
    assert "/-/language/" not in test_client.get("/").data.decode()


def test_language_unknown(create_app, test_client):
    create_app.config["LANGUAGE_MENU"] = True
    assert test_client.get("/-/language/xx").status_code == 404


@pytest.mark.parametrize(
    "next_page",
    ["https://evil.com/", "//evil.com/", "/\\evil.com", "/\t/evil.com", ""],
)
def test_language_no_open_redirect(create_app, test_client, next_page):
    create_app.config["LANGUAGE_MENU"] = True
    rv = test_client.get("/-/language/fr", query_string={"next": next_page})
    assert rv.status_code == 302
    assert rv.headers["Location"] == "/"


def test_admin_language_preferences(app_with_user, admin_client):
    rv = admin_client.post(
        "/-/admin",
        data={
            "site_lang": "fr",
            "language_from_browser": "True",
            "language_menu": "True",
            "server_name": "",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert app_with_user.config["SITE_LANG"] == "fr"
    assert app_with_user.config["LANGUAGE_FROM_BROWSER"] is True
    assert app_with_user.config["LANGUAGE_MENU"] is True
    html = rv.data.decode()
    assert 'id="language_menu" name="language_menu"' in html
    # unchecked boxes are not sent by the browser
    admin_client.post(
        "/-/admin",
        data={
            "site_lang": "fr",
            "server_name": "",
            "update_preferences": "true",
        },
    )
    assert app_with_user.config["LANGUAGE_FROM_BROWSER"] is False
    assert app_with_user.config["LANGUAGE_MENU"] is False


def test_language_menu_is_its_own_dropdown(create_app, test_client):
    create_app.config["LANGUAGE_MENU"] = True
    html = test_client.get("/").data.decode()
    assert 'id="navbar-language-btn"' in html
    # the button shows the current language
    assert re.search(r'id="navbar-language-btn"[^>]*>\s*EN\s*</button>', html)
    # the languages are not in the main menu
    main_menu = html.split('id="navbar-dropdown-toggle-btn-1"')[1]
    assert "/-/language/" not in main_menu
