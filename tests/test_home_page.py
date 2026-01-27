#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
Tests for configurable home page functionality.

Tests cover:
1. Default behavior (Home page)
2. Root index mode
3. Custom page mode
4. Compatibility with RETAIN_PAGE_NAME_CASE
"""

import pytest
from flask import url_for


def test_home_page_default(app_with_user, test_client):
    app_with_user.config["HOME_PAGE"] = "default"
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


def test_home_page_root_index(app_with_user, test_client):
    app_with_user.config["HOME_PAGE"] = "root_index"
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
    test_client.post(
        "/Contact/save",
        data={
            "content": "# Contact\n\nContact page content.",
            "commit": "Create contact",
        },
    )

    response = test_client.get("/")
    assert response.status_code == 200
    html = response.data.decode()
    assert "Home page content" not in html
    assert "Page Index" in html
    assert "About" in html or "Contact" in html or "Home" in html


def test_home_page_custom(app_with_user, test_client):
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


def test_home_page_custom_nested(app_with_user, test_client):
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


def test_home_page_custom_with_retain_case(app_with_user, test_client):
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
