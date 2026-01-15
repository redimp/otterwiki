#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import pathlib
import re
from io import BytesIO
from flask import url_for
import bs4
import pytest


def _link_by_text(soup, text):
    return soup.find("a", string=text)


def test_html(test_client):
    result = test_client.get("/")
    assert "<!DOCTYPE html>" in result.data.decode()
    assert "<title>" in result.data.decode()
    assert "</html>" in result.data.decode()


def test_healthz(test_client):
    result = test_client.get("/-/healthz")
    assert "ok" in result.data.decode()


def test_create_form(test_client):
    result = test_client.get("/-/create")
    html = result.data.decode()
    assert "Create Page</h2>" in html
    assert '<form action="/-/create" method="POST"' in html


def test_create_page_sanitized(test_client):
    pagename = "CreateTest?"
    html = test_client.post(
        "/-/create",
        data={
            "pagename": pagename,
        },
        follow_redirects=True,
    ).data.decode()
    assert "Please check the pagename" in html


def test_create_page_in(test_client):
    # create a page in a subdirectory
    subdir = "subdir"
    pagename = f"{subdir}/pagename"
    html = test_client.post(
        f"/{pagename}/save",
        data={
            "content": f"{pagename}\n\nTest test 12345678",
            "commit": "Initial commit",
        },
        follow_redirects=True,
    ).data.decode()
    assert "Test test 12345678" in html

    html = test_client.get("/-/create").data.decode()
    assert (
        f"otterwiki.toggle_pagename_prefix('pagename','{pagename}')"
        in html.lower()
    )
    assert (
        f"otterwiki.toggle_pagename_prefix('pagename','{subdir}')"
        in html.lower()
    )


def test_create_page(test_client, req_ctx):
    pagename = "createtest"
    html = test_client.post(
        "/-/create",
        data={
            "pagename": pagename,
        },
        follow_redirects=True,
    ).data.decode()
    # check textarea
    assert "<textarea" in html
    assert 'name="content_editor"' in html
    # test save
    html = test_client.post(
        "/{}/save".format(pagename),
        data={
            "content": "Test test 12345678\n\n**strong**",
            "commit": "Initial commit",
        },
        follow_redirects=True,
    ).data.decode()
    assert "Test test 12345678" in html
    assert "<title>{}".format(pagename.title()) in html
    assert "<p><strong>strong</strong></p>" in html
    # check existing page
    html = test_client.post(
        "/-/create",
        data={
            "pagename": pagename,
        },
        follow_redirects=True,
    ).data.decode()
    assert "exists already" in html


def test_create_page_notlower(test_client, req_ctx):
    pagename = "Create/Test page"
    html = test_client.post(
        "/-/create",
        data={
            "pagename": pagename,
        },
        follow_redirects=True,
    ).data.decode()
    # check textarea
    assert "<textarea" in html
    assert 'name="content_editor"' in html
    # test save
    html = test_client.post(
        "/{}/save".format(pagename),
        data={
            "content": "Test test 12345678\n\n**strong**",
            "commit": "Initial commit",
        },
        follow_redirects=True,
    ).data.decode()
    assert "Test test 12345678" in html
    assert "<title>Test page" in html
    assert "<p><strong>strong</strong></p>" in html
    # check existing page
    html = test_client.post(
        "/-/create",
        data={
            "pagename": pagename,
        },
        follow_redirects=True,
    ).data.decode()
    assert "exists already" in html


def save_shortcut(test_client, pagename, content, commit_message):
    rv = test_client.post(
        "/{}/save".format(pagename),
        data={
            "content": content,
            "commit": commit_message,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200


def test_pageindex(test_client):
    save_shortcut(
        test_client,
        "Random page",
        "# Random page\nrandom text",
        "added random page",
    )
    save_shortcut(
        test_client,
        "Sub directory/Nested Page",
        "# Nested page\n\n## Nested header\n",
        "added nested page",
    )
    html = test_client.get("/-/index").data.decode()
    soup = bs4.BeautifulSoup(html, "html.parser")
    # check capitalizing (from # Random page)
    a = _link_by_text(soup, "Random page")
    assert a is not None
    assert a.get("href") == "/Random page"
    # Test nested page
    a = _link_by_text(soup, "Nested page")
    assert a is not None
    assert a.get("href") == "/Sub Directory/Nested page"
    # and nested header
    a = _link_by_text(soup, "Nested header")
    assert a is not None
    assert a.get("href") == "/Sub%20Directory/Nested%20page#nested-header"
    # check data-index-path attribute
    body = soup.find("body")
    assert body
    data_index_path = body.get("data-index-path", "")
    assert data_index_path == "/"


def test_page_save(test_client):
    from otterwiki.server import storage

    pagename = "Save Test"
    content = "*em*\n\n**strong**\n"
    commit_message = "Save test commit message"
    save_shortcut(test_client, pagename, content, commit_message)
    # check file content
    assert content == storage.load("{}.md".format(pagename.lower()))
    # check history
    html = test_client.get("/{}/history".format(pagename)).data.decode()
    assert "History" in html
    assert commit_message in html


def test_view_source(test_client):
    pagename = "Source Test"
    content = "# src test\n\n**strong text**\n"
    commit_message = "Source test commit message"
    save_shortcut(test_client, pagename, content, commit_message)
    html = test_client.get("/{}/source".format(pagename)).data.decode()
    assert "# src test" in html
    assert "**strong text**" in html
    # test with ?raw
    html = test_client.get("/{}/source?raw".format(pagename)).data.decode()
    assert content in html


def test_view_revision(test_client, req_ctx):
    pagename = "ViewRevisionTest"
    content = ["aaa", "bbb"]
    commit_messages = ["initial commit", "update"]
    # save page
    save_shortcut(test_client, pagename, content[0], commit_messages[0])
    html0 = test_client.get("/{}".format(pagename)).data.decode()
    assert content[0] in html0
    # update page
    save_shortcut(test_client, pagename, content[1], commit_messages[1])
    html1 = test_client.get("/{}".format(pagename)).data.decode()
    assert content[1] in html1
    # check history
    html = test_client.get("/{}/history".format(pagename)).data.decode()
    # find revisions
    revision = re.findall(
        r"class=\"btn revision-small\">([A-z0-9]+)</a>", html
    )
    assert len(revision) == 2
    # fetch revisions via pageview
    url0 = url_for("pageview", path=pagename, revision=revision[0])
    html0 = test_client.get(url0).data.decode()
    url1 = url_for("pageview", path=pagename, revision=revision[1])
    html1 = test_client.get(url1).data.decode()
    # and check them
    assert revision[0] in html0
    assert revision[1] in html1
    assert content[1] in html0
    assert content[0] in html1
    # fetch revisions via view
    url0 = url_for("view", path=pagename, revision=revision[0])
    html0 = test_client.get(url0).data.decode()
    url1 = url_for("view", path=pagename, revision=revision[1])
    html1 = test_client.get(url1).data.decode()
    # and check them
    assert revision[0] in html0
    assert revision[1] in html1
    assert content[1] in html0
    assert content[0] in html1


def test_view_commit(test_client, req_ctx):
    # check if an invalid commit triggers an 404
    rv = test_client.get(f"/-/commit/xxx")
    assert rv.status_code == 404

    pagename = "ViewCommitTest"
    content = ["aaa initial commit line", "bbb updated commit line"]
    commit_messages = ["initial commit", "update"]
    # save page
    save_shortcut(test_client, pagename, content[0], commit_messages[0])
    html0 = test_client.get("/{}".format(pagename)).data.decode()
    assert content[0] in html0
    # update page
    save_shortcut(test_client, pagename, content[1], commit_messages[1])
    html1 = test_client.get("/{}".format(pagename)).data.decode()
    assert content[1] in html1
    # check history
    html = test_client.get("/{}/history".format(pagename)).data.decode()
    # find revisions
    revision = re.findall(
        r"class=\"btn revision-small\">([A-z0-9]+)</a>", html
    )
    assert len(revision) == 2
    html = test_client.get(f"/-/commit/{revision[0]}").data.decode()

    assert revision[0] in html
    assert content[0] in html
    assert content[1] in html


def test_blame_and_history_and_diff(test_client):
    pagename = "Blame Test"
    content = "Blame Test\naaa_aaa_aaa"
    commit_messages = ["initial commit", "update"]
    save_shortcut(test_client, pagename, content, commit_messages[0])
    # check history
    html = test_client.get("/{}/history".format(pagename)).data.decode()
    assert commit_messages[0] in html
    # check blame
    html = test_client.get("/{}/blame".format(pagename)).data.decode()
    for line in content.splitlines():
        assert line in html
    # update content
    content = "Blame Test\nbbb\nccc\nddd"
    save_shortcut(test_client, pagename, content, commit_messages[1])
    # check history
    html = test_client.get("/{}/history".format(pagename)).data.decode()
    # find revision
    revision = re.findall(
        r"class=\"btn revision-small\">([A-z0-9]+)</a>", html
    )
    assert len(revision) == 2
    for line in commit_messages:
        assert line in html
    # check blame
    html = test_client.get("/{}/blame".format(pagename)).data.decode()
    for line in content.splitlines():
        assert line in html
    assert "aaa_aaa_aaa" not in html
    # fetch diff
    rv = test_client.post(
        "/{}/history".format(pagename),
        data={"rev_a": revision[1], "rev_b": revision[0]},
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert pagename in html
    assert revision[0] in html
    assert revision[1] in html


def test_blame_and_history_404(test_client):
    pagename = "Does not exist"
    # check blame
    rv = test_client.get("/{}/blame".format(pagename), follow_redirects=True)
    assert "Page not found" in rv.data.decode()
    assert rv.status_code == 404
    # check history
    rv = test_client.get("/{}/history".format(pagename), follow_redirects=True)
    assert "Page not found" in rv.data.decode()
    assert rv.status_code == 404


def test_search(test_client):
    # create additional haystacks
    save_shortcut(test_client, "HayStack 0", "Needle 0", "initial commit")
    save_shortcut(test_client, "HayStack 1", "Needle 1", "initial commit")
    save_shortcut(test_client, "Haystack 1a", "NeEdle 1", "initial commit")
    save_shortcut(
        test_client, "Haystack 2", "NeEdle 2\nNeEdle 2", "initial commit"
    )
    # search 1
    rv = test_client.get("/-/search/{}".format("Haystack"))
    assert "Search matched 4 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search 2
    rv = test_client.get("/-/search/{}".format("Needle"))
    assert "Search matched 4 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search 3
    rv = test_client.get("/-/search/{}".format("Needle 1"))
    assert "Search matched 2 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search 4
    rv = test_client.get("/-/search/{}".format("Haystack 1"))
    assert "Search matched 2 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search via post 1
    rv = test_client.post("/-/search", data={"query": "Haystack"})
    assert "Search matched 4 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search via post 2: case sensitive
    rv = test_client.post(
        "/-/search", data={"query": "HayStack", "is_casesensitive": "y"}
    )
    assert "Search matched 4 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search via post 3: case sensitive
    rv = test_client.post(
        "/-/search", data={"query": "NeEdle", "is_casesensitive": "y"}
    )
    assert "Search matched 2 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search via post 4: regex
    rv = test_client.post(
        "/-/search",
        data={"query": "NeEdle", "is_regexp": "y", "is_casesensitive": "y"},
    )
    assert "Search matched 2 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search via post 4: regex
    rv = test_client.post(
        "/-/search", data={"query": "N[eE]+dle", "is_regexp": "y"}
    )
    assert "Search matched 4 pages" in rv.data.decode()
    assert rv.status_code == 200


def test_rename(test_client):
    old_pagename = "RenameTest"
    new_pagename = "RenameTestNew"
    content = "# Rename content\nabc abc abc def def def."
    # create page
    save_shortcut(
        test_client,
        pagename=old_pagename,
        content=content,
        commit_message="initial commit",
    )
    # check content
    rv = test_client.get("/{}/view".format(old_pagename))
    assert rv.status_code == 200
    # check new page doesn't exist
    rv = test_client.get("/{}/view".format(new_pagename))
    assert rv.status_code == 404
    # rename form
    rv = test_client.get("/{}/rename".format(old_pagename))
    assert (
        'form action="/{}/rename" method="POST"'.format(old_pagename)
        in rv.data.decode()
    )
    assert rv.status_code == 200
    # rename page
    rv = test_client.post(
        "/{}/rename".format(old_pagename),
        data={"new_pagename": new_pagename, "message": ""},
        follow_redirects=True,
    )
    # check old page doesn't exist
    rv = test_client.get("/{}/view".format(old_pagename))
    assert rv.status_code == 404
    # check new page exists
    rv = test_client.get("/{}/view".format(new_pagename))
    assert rv.status_code == 200


def test_delete(test_client):
    pagename = "DeleteTest"
    content = "# Delete content\nabc abc abc def def def."
    # create page
    save_shortcut(
        test_client,
        pagename=pagename,
        content=content,
        commit_message="initial commit",
    )
    # check content
    rv = test_client.get("/{}/view".format(pagename))
    assert rv.status_code == 200
    # delete form
    rv = test_client.get("/{}/delete".format(pagename))
    assert rv.status_code == 200
    assert (
        'form action="/{}/delete" method="POST"'.format(pagename)
        in rv.data.decode()
    )
    # delete page
    rv = test_client.post(
        "/{}/delete".format(pagename),
        data={"message": "deleted ..."},
        follow_redirects=True,
    )
    assert rv.status_code == 200
    # check deletion
    rv = test_client.get("/{}/view".format(pagename))
    assert rv.status_code == 404


def test_non_version_control_file(test_client):
    p = test_client.application._otterwiki_tempdir

    filename = "no version file"
    content = 'oh no! no control!'
    with open(os.path.join(p, f'{filename}.md'), 'w') as f:
        f.write(content)

    # first, assert that a file that doesn't exists returns a 404
    response = test_client.get(f"/some crazy file name that doesn't exist")
    assert response.status_code == 404

    # then try that file that was previous created (but not added to version control)
    response = test_client.get(f"/{filename}")
    assert response.status_code == 200
    assert (
        "This page was loaded from the repository but is not added under git version control"
        in response.data.decode()
    )
    assert content in response.data.decode()


def test_move_page(test_client):
    '''test that moving a file works'''
    p = test_client.application._otterwiki_tempdir
    _inner_folder = "a_folder/another_folder/"
    _file_name = "wiki_page"
    _new_file_name = "wiki_page_new"

    pagename = f"{_inner_folder}{_file_name}"
    new_pagename = f"{_inner_folder}{_new_file_name}"

    content = "# My nested file\n\nDid it work?"
    commit = "my commit"

    rv = test_client.post(
        "/{}/save".format(pagename),
        data={
            "content": content,
            "commit": commit,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    rv = test_client.post(
        "/{}/rename".format(pagename),
        data={
            "new_pagename": f"{new_pagename}",
            "message": commit,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    response_text = rv.data.decode().lower()
    if test_client.application.config.get(
        "TREAT_UNDERSCORE_AS_SPACE_FOR_TITLES", False
    ):
        # when underscore replacement is enabled, expect spaces in display text
        expected_display_name = _new_file_name.replace("_", " ")
        assert (
            f'<a href="/{new_pagename}">{expected_display_name}</a>'.lower()
            in response_text
        )
    else:
        # when underscore replacement is disabled, expect original underscores
        assert (
            f'<a href="/{new_pagename}">{_new_file_name}</a>'.lower()
            in response_text
        )


def test_nested_files(test_client):
    p = test_client.application._otterwiki_tempdir
    _inner_folder = "a_folder/another_folder/"
    _file_name = "examplepage"
    pagename = f"{_inner_folder}{_file_name}"

    content = "# My nested file\n\nDid it work?"
    commit = "my commit"

    rv = test_client.post(
        "/{}/save".format(pagename),
        data={
            "content": content,
            "commit": commit,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    nested_wiki_file = pathlib.Path(p, pagename + '.md')
    nested_file_exists = nested_wiki_file.exists()
    assert nested_file_exists == True

    # check the page is there
    rv = test_client.get("/{}".format(pagename))
    assert rv.status_code == 200

    # check path with a trailing slash
    rv = test_client.get("/{}/".format(pagename))
    assert rv.status_code == 200

    # check that the parent page returns the page index
    rv = test_client.get("/{}".format(_inner_folder))
    assert rv.status_code == 200
    assert 'Page Index' in rv.data.decode()
    assert _file_name.capitalize() in rv.data.decode()

    # upload an image
    file_name = 'test_image.png'
    _file_path = pathlib.Path(__file__).parent / file_name
    data = dict(
        file=(BytesIO(open(_file_path, 'rb').read()), file_name),
    )
    response = test_client.post(
        "/{}/attachments".format(pagename),
        content_type='multipart/form-data',
        data=data,
        follow_redirects=True,
    )

    # check the image exists
    assert response.status_code == 200
    assert f'{file_name}">{file_name}</a>' in response.data.decode()

    nest_file_location = pathlib.Path(p, pagename, file_name)

    # check it's location on disk
    exists = nest_file_location.exists()
    assert exists == True

    # delete the image
    rv = test_client.post(
        "/{}/delete".format(pagename),
        data={"message": "deleted ...", "recursive": "recursive"},
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # check all locations are deleted
    assert nested_wiki_file.exists() == False
    assert nest_file_location.exists() == False
    rv = test_client.get("/{}".format(pagename))
    assert rv.status_code == 404


def test_blame_issue200_empty_trailing_lines(test_client, create_app):
    # store the file
    pagename = "blametesttrailinglines"
    content = "# Blame Test 1\n\nBlame Test\n\n\n"
    assert True == create_app.storage.store(
        f"{pagename}.md",
        content=content,
        author=("John", "john@doe.com"),
        message=f"added {pagename}",
    )
    # check blame
    rv = test_client.get("/{}/blame".format(pagename))
    assert rv.status_code == 200


def test_meta_og(test_client):
    pagename = "Meta Test"
    content = (
        "# Meta Test\n\n**strong text** with a [link](https://example.com).\n"
    )
    commit_message = "Meta test commit message"
    save_shortcut(test_client, pagename, content, commit_message)
    html = test_client.get("/{}".format(pagename)).data.decode()
    soup = bs4.BeautifulSoup(html, "html.parser")
    assert soup
    title = soup.find("meta", property="og:title")
    assert title
    title = title.get("content", None)
    description = soup.find("meta", property="og:description")
    assert description
    description = description.get("content", None)
    assert title == pagename
    assert description == "strong text with a link."


@pytest.mark.parametrize(
    "pagename, slug",
    [
        ("MyPage", "mypage"),
        ("Sub/My Other Page", "sub/my-other-page"),
        (
            "'Lots' & \"Lots\" \U0001f525 of <Special Chars>",
            "lots-lots-of-special-chars",
        ),
    ],
)
def test_data_pagepath_attribute(test_client, pagename, slug):
    content = "# Data Page Path Test\n\nTesting data-page-path attribute."
    commit_message = "Data page path test commit message"
    save_shortcut(test_client, pagename, content, commit_message)
    html = test_client.get("/{}".format(pagename)).data.decode()
    soup = bs4.BeautifulSoup(html, "html.parser")
    assert soup
    body = soup.find("body")
    assert body
    data_page_path = body.get("data-page-path", "")
    assert data_page_path == slug


def test_data_indexpath_attribute(test_client):
    pagename = "IndexPathTest/Page"
    content = "# Data Index Path Test\n\nTesting data-index-path attribute."
    commit_message = "Data index path test commit message"
    save_shortcut(test_client, pagename, content, commit_message)
    html = test_client.get("/IndexPathTest").data.decode()
    soup = bs4.BeautifulSoup(html, "html.parser")
    assert soup
    body = soup.find("body")
    assert body
    data_index_path = body.get("data-index-path", "")
    assert data_index_path == "indexpathtest"
