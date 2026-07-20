#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest


def save_shortcut(test_client, pagename, content):
    rv = test_client.post(
        "/{}/save".format(pagename),
        data={
            "content": content,
            "commit": "test",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200


@pytest.fixture
def app_with_default_backlink_settings(create_app):
    create_app.config["WIKILINK_STYLE"] = ""
    create_app.config["RETAIN_PAGE_NAME_CASE"] = False
    return create_app


@pytest.fixture
def test_client(app_with_default_backlink_settings):
    return app_with_default_backlink_settings.test_client()


@pytest.mark.parametrize(
    "wikilink_style,content,expected",
    [
        (
            "",
            "[[Target Title|Path/OldPage]]",
            "[[Target Title|Path/NewPage]]",
        ),
        (
            "LINKTITLE",
            "[[Path/OldPage|Target Title]]",
            "[[Path/NewPage|Target Title]]",
        ),
    ],
)
def test_rename_backlinks_wikilink_style(
    create_app,
    wikilink_style,
    content,
    expected,
):
    app = create_app
    saved = app.config["WIKILINK_STYLE"]
    app.config["WIKILINK_STYLE"] = wikilink_style

    content += "\n"
    expected += "\n"

    with app.test_client() as client:
        save_shortcut(client, "example", content)

        from otterwiki.backlinks import rename_backlinks

        result = rename_backlinks(
            "Path/OldPage",
            "Path/NewPage",
        )

        assert result == {
            "example.md": expected,
        }

        updated = app.storage.load("example.md")
        assert updated == expected

    app.config["WIKILINK_STYLE"] = saved


@pytest.mark.parametrize(
    "retain_case,content,expected",
    [
        (
            False,
            "![](/path/oldpage/image.png)",
            "![](/Path/NewPage/image.png)",
        ),
        (
            True,
            "![](/path/oldpage/image.png)",
            "![](/path/oldpage/image.png)",
        ),
    ],
)
def test_rename_backlinks_retain_page_name_case(
    create_app,
    retain_case,
    content,
    expected,
):
    app = create_app
    saved = app.config["RETAIN_PAGE_NAME_CASE"]
    app.config["RETAIN_PAGE_NAME_CASE"] = retain_case

    content += "\n"
    expected += "\n"

    with app.test_client() as client:
        save_shortcut(client, "example", content)

        from otterwiki.backlinks import rename_backlinks

        result = rename_backlinks(
            "Path/OldPage",
            "Path/NewPage",
        )

        if expected != content:
            assert result == {
                "example.md": expected,
            }
        else:
            assert result == {}

        assert app.storage.load("example.md") == expected

    app.config["RETAIN_PAGE_NAME_CASE"] = saved


@pytest.mark.parametrize(
    "old_page,new_page,content,expected",
    [
        (
            "Pathto/Targetpage",
            "Pathto/Renamedpage",
            "[[Pathto/Targetpage]]",
            "[[Pathto/Renamedpage]]",
        ),
        (
            "Pathto/Targetpage",
            "Pathto/Renamedpage",
            "[[Target Page|Pathto/Targetpage]]",
            "[[Target Page|Pathto/Renamedpage]]",
        ),
        (
            "Pathto/Targetpage",
            "Pathto/Renamedpage",
            "[Description](/Pathto/Targetpage)",
            "[Description](/Pathto/Renamedpage)",
        ),
        (
            "Pathto/Targetpage",
            "Pathto/Renamedpage",
            "[[Pathto/Targetpage#sub-heading]]",
            "[[Pathto/Renamedpage#sub-heading]]",
        ),
        (
            "Pathto/Targetpage",
            "Pathto/Renamedpage",
            "[[Target Page With Anchor|Pathto/Targetpage#sub-heading]]",
            "[[Target Page With Anchor|Pathto/Renamedpage#sub-heading]]",
        ),
        (
            "Pathto/Targetpage",
            "Pathto/Renamedpage",
            "[Anchor](/Pathto/Targetpage#sub-heading)",
            "[Anchor](/Pathto/Renamedpage#sub-heading)",
        ),
        (
            "Pathto/Targetpage",
            "Pathto/Renamedpage",
            "[Otter](/Pathto/Targetpage/otter.png)",
            "[Otter](/Pathto/Renamedpage/otter.png)",
        ),
        (
            "Pathto/Targetpage",
            "Pathto/Renamedpage",
            "![](/Pathto/Targetpage/otter.png)",
            "![](/Pathto/Renamedpage/otter.png)",
        ),
        (
            "Path With Spaces/Target Page",
            "Path With Spaces/Renamed Page",
            "[Description](/Path%20With%20Spaces/Target%20Page)",
            "[Description](/Path%20With%20Spaces/Renamed%20Page)",
        ),
    ],
)
def test_rename_backlinks_supported_links(
    create_app,
    old_page,
    new_page,
    content,
    expected,
):
    app = create_app

    content += "\n"
    expected += "\n"

    with app.test_client() as client:
        save_shortcut(client, "example", content)

        from otterwiki.backlinks import rename_backlinks

        result = rename_backlinks(
            old_page,
            new_page,
        )

        assert result == {
            "example.md": expected,
        }

        assert app.storage.load("example.md") == expected
