#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
Tests for configurable home page functionality.

Tests cover:
1. Default behavior (Home page)
2. Custom page mode
3. Special page redirect mode
4. Compatibility with RETAIN_PAGE_NAME_CASE
5. Initialization with HOME_PAGE environment variable
"""

import pytest
import os
import otterwiki.gitstorage
from flask import url_for


def test_home_page_default(app_with_user, test_client):
    original_home_page = app_with_user.config.get("HOME_PAGE")

    try:
        app_with_user.config["HOME_PAGE"] = ""
        app_with_user.config["READ_ACCESS"] = "ANONYMOUS"

        test_client.post(
            "/Home/save",
            data={
                "content": "# Welcome\n\nThis is the home page.",
                "commit": "Initial home page",
            },
        )

        response = test_client.get("/")
        assert response.status_code == 200
        html = response.data.decode()

        assert "Welcome" in html
        assert "This is the home page" in html
    finally:
        if original_home_page is not None:
            app_with_user.config["HOME_PAGE"] = original_home_page
        elif "HOME_PAGE" in app_with_user.config:
            del app_with_user.config["HOME_PAGE"]


def test_home_page_special_page_index(app_with_user, test_client):
    original_home_page = app_with_user.config.get("HOME_PAGE")

    try:
        app_with_user.config["HOME_PAGE"] = "/-/index"
        app_with_user.config["READ_ACCESS"] = "ANONYMOUS"

        test_client.post(
            "/Home/save",
            data={
                "content": "# Home\n\nHome page content.",
                "commit": "Create home",
            },
        )
        test_client.post(
            "/About/save",
            data={
                "content": "# About\n\nAbout page content.",
                "commit": "Create about",
            },
        )

        response = test_client.get("/")
        assert response.status_code == 302
        assert "/-/index" in response.location
    finally:
        if original_home_page is not None:
            app_with_user.config["HOME_PAGE"] = original_home_page
        elif "HOME_PAGE" in app_with_user.config:
            del app_with_user.config["HOME_PAGE"]


def test_home_page_custom(app_with_user, test_client):
    original_home_page = app_with_user.config.get("HOME_PAGE")

    try:
        test_client.post(
            "/Welcome/save",
            data={
                "content": "# Welcome to Our Wiki\n\nThis is a custom home page.",
                "commit": "Create welcome page",
            },
        )

        app_with_user.config["HOME_PAGE"] = "Welcome"
        app_with_user.config["READ_ACCESS"] = "ANONYMOUS"

        response = test_client.get("/")
        assert response.status_code == 200
        html = response.data.decode()
        assert "Welcome to Our Wiki" in html
        assert "This is a custom home page" in html
    finally:
        if original_home_page is not None:
            app_with_user.config["HOME_PAGE"] = original_home_page
        elif "HOME_PAGE" in app_with_user.config:
            del app_with_user.config["HOME_PAGE"]


def test_home_page_custom_nested(app_with_user, test_client):
    original_home_page = app_with_user.config.get("HOME_PAGE")

    try:
        test_client.post(
            "/Docs/Index/save",
            data={
                "content": "# Documentation Index\n\nWelcome to the docs.",
                "commit": "Create docs index",
            },
        )

        app_with_user.config["HOME_PAGE"] = "Docs/Index"
        app_with_user.config["READ_ACCESS"] = "ANONYMOUS"

        response = test_client.get("/")
        assert response.status_code == 200
        html = response.data.decode()
        assert "Documentation Index" in html
        assert "Welcome to the docs" in html
    finally:
        if original_home_page is not None:
            app_with_user.config["HOME_PAGE"] = original_home_page
        elif "HOME_PAGE" in app_with_user.config:
            del app_with_user.config["HOME_PAGE"]


def test_home_page_custom_with_trailing_slash(app_with_user, test_client):
    original_home_page = app_with_user.config.get("HOME_PAGE")

    try:
        test_client.post(
            "/Welcome/save",
            data={
                "content": "# Welcome Page\n\nTrailing slash test.",
                "commit": "Create welcome",
            },
        )

        app_with_user.config["HOME_PAGE"] = "Welcome/"
        app_with_user.config["READ_ACCESS"] = "ANONYMOUS"

        response = test_client.get("/")
        assert response.status_code == 200
        html = response.data.decode()
        assert "Welcome Page" in html
        assert "Trailing slash test" in html
    finally:
        if original_home_page is not None:
            app_with_user.config["HOME_PAGE"] = original_home_page
        elif "HOME_PAGE" in app_with_user.config:
            del app_with_user.config["HOME_PAGE"]


def test_home_page_custom_with_retain_case(app_with_user, test_client):
    original_home_page = app_with_user.config.get("HOME_PAGE")

    try:
        app_with_user.config["RETAIN_PAGE_NAME_CASE"] = True
        app_with_user.config["READ_ACCESS"] = "ANONYMOUS"

        test_client.post(
            "/MyWelcome/save",
            data={
                "content": "# My Welcome Page\n\nCustom home with case retained.",
                "commit": "Create MyWelcome",
            },
        )

        app_with_user.config["HOME_PAGE"] = "MyWelcome"

        response = test_client.get("/")
        assert response.status_code == 200
        html = response.data.decode()
        assert "My Welcome Page" in html
        assert "Custom home with case retained" in html
    finally:
        if original_home_page is not None:
            app_with_user.config["HOME_PAGE"] = original_home_page
        elif "HOME_PAGE" in app_with_user.config:
            del app_with_user.config["HOME_PAGE"]


@pytest.fixture
def create_app_with_home_page_env(tmpdir):
    """Create app with HOME_PAGE set via environment variable before initialization."""
    original_home_page = os.environ.get("HOME_PAGE")
    original_settings = os.environ.get("OTTERWIKI_SETTINGS")

    def _create_app(home_page_value):
        tmpdir.mkdir("repo")
        _storage = otterwiki.gitstorage.GitStorage(
            path=str(tmpdir.join("repo")), initialize=True
        )
        settings_cfg = str(tmpdir.join("settings.cfg"))

        with open(settings_cfg, "w") as f:
            f.writelines(
                [
                    "REPOSITORY = '{}'\n".format(str(_storage.path)),
                    "SITE_NAME = 'TEST WIKI'\n",
                    "DEBUG = True\n",
                    "TESTING = True\n",
                    "MAIL_SUPPRESS_SEND = True\n",
                    "SECRET_KEY = 'Testing Testing Testing'\n",
                ]
            )

        os.environ["HOME_PAGE"] = home_page_value
        os.environ["OTTERWIKI_SETTINGS"] = settings_cfg

        import sys

        # remove cached modules to force fresh import
        modules_to_remove = [
            k for k in sys.modules.keys() if k.startswith('otterwiki')
        ]
        for mod in modules_to_remove:
            del sys.modules[mod]

        from otterwiki.server import app, db, storage

        app._otterwiki_tempdir = storage.path
        app.storage = storage
        app.config["TESTING"] = True
        app.config["DEBUG"] = True

        return app, storage

    yield _create_app

    # cleanup: restore original environment variables and reimport modules
    if original_home_page is not None:
        os.environ["HOME_PAGE"] = original_home_page
    elif "HOME_PAGE" in os.environ:
        del os.environ["HOME_PAGE"]

    if original_settings is not None:
        os.environ["OTTERWIKI_SETTINGS"] = original_settings
    elif "OTTERWIKI_SETTINGS" in os.environ:
        del os.environ["OTTERWIKI_SETTINGS"]

    # remove cached modules to force fresh import for next test
    import sys

    modules_to_remove = [
        k for k in sys.modules.keys() if k.startswith('otterwiki')
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


def test_initialization_with_default_home_page(create_app_with_home_page_env):
    app, storage = create_app_with_home_page_env("")

    files, _ = storage.list()
    assert 'home.md' in files or 'Home.md' in files

    if 'home.md' in files:
        content = storage.load('home.md')
    else:
        content = storage.load('Home.md')
    assert 'Welcome to your wiki!' in content


def test_initialization_with_special_page_home(
    create_app_with_home_page_env,
):
    app, storage = create_app_with_home_page_env("/-/index")

    files, _ = storage.list()
    assert len(files) == 0


def test_initialization_with_custom_home_page(create_app_with_home_page_env):
    app, storage = create_app_with_home_page_env("Welcome")

    files, _ = storage.list()
    assert 'welcome.md' in files

    content = storage.load('welcome.md')
    assert 'Welcome to your wiki!' in content


def test_initialization_with_custom_nested_home_page(
    create_app_with_home_page_env,
):
    app, storage = create_app_with_home_page_env("Docs/Index")

    files, _ = storage.list()
    assert 'docs/index.md' in files

    content = storage.load('docs/index.md')
    assert 'Welcome to your wiki!' in content
