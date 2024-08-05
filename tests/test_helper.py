#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import flask
import otterwiki
import otterwiki.gitstorage


def test_toast(create_app, req_ctx, test_client):
    test_string = "aa bb cc dd"
    from otterwiki.helper import toast

    assert not flask.session.modified
    # test toast
    toast(test_string)
    assert flask.session.modified
    assert list(flask.get_flashed_messages()) == [test_string]


def test_toast_session(create_app, req_ctx, test_client):
    test_string = "aa bb cc dd"
    from otterwiki.helper import toast
    from flask import session

    html = test_client.get("/").data.decode()
    assert "<!DOCTYPE html>" in html
    assert test_string not in html
    # test toast
    toast(test_string)
    assert test_string in [x[1] for x in session["_flashes"]]
    toast(test_string, "non-existing-category")
    assert ("alert-primary", test_string) in session["_flashes"]


def test_serializer(create_app, req_ctx):
    s = "Hello World"
    from otterwiki.helper import serialize, deserialize, SerializeError

    assert s == deserialize(serialize(s))
    # check max_age
    with pytest.raises(SerializeError):
        deserialize(serialize(s), max_age=-1)
    # check salt
    with pytest.raises(SerializeError):
        deserialize(serialize(s), salt=s)


def test_health_check_ok(create_app, req_ctx):
    from otterwiki.helper import health_check

    healthy, messages = health_check()
    assert healthy is True
    assert messages == ["ok"]


def test_health_check_error_storage(create_app, req_ctx, tmpdir):
    from otterwiki.helper import health_check
    from otterwiki.gitstorage import GitStorage

    # update the Storage object with a storage on a not initialized directory
    _working_dir = create_app.storage.repo.git._working_dir
    create_app.storage.repo.git._working_dir = str(
        tmpdir.mkdir("test_health_check_error_storage")
    )

    healthy, messages = health_check()
    assert healthy is False
    assert True in [m.startswith("StorageError") for m in messages]
    # restore _working_dir FIXME: no idea why the pytest fixture doesn't work in scope=session
    create_app.storage.repo.git._working_dir = _working_dir


def test_health_check_error_storage(create_app, req_ctx, tmpdir):
    from otterwiki.helper import health_check
    from otterwiki.gitstorage import GitStorage

    # update the Storage object with a storage on a not initialized directory
    _working_dir = create_app.storage.repo.git._working_dir
    create_app.storage.repo.git._working_dir = str(
        tmpdir.mkdir("test_health_check_error_storage")
    )

    healthy, messages = health_check()
    assert healthy is False
    assert True in [m.startswith("StorageError") for m in messages]
    # restore _working_dir
    create_app.storage.repo.git._working_dir = _working_dir


def test_auto_url(create_app, req_ctx):
    from otterwiki.helper import auto_url

    name, path = auto_url("home.md")
    assert name == "Home"
    assert path == "/Home"
    name, path = auto_url("subspace/example.md")
    assert name == "Subspace/Example"
    assert path == "/Subspace/Example"
    name, path = auto_url("page/example.mp4")
    assert name == "page/example.mp4"
    assert path == "/Page/a/example.mp4"


@pytest.fixture
def create_app_raw_filenames(create_app):
    create_app.config["RETAIN_PAGE_NAME_CASE"] = True
    yield create_app
    create_app.config["RETAIN_PAGE_NAME_CASE"] = False


def test_auto_url_raw(create_app_raw_filenames, req_ctx):
    assert req_ctx
    from otterwiki.helper import auto_url

    name, path = auto_url("home.md")
    assert name == "home"
    assert path == "/home"
    name, path = auto_url("subspace/example.md")
    assert name == "subspace/example"
    assert path == "/subspace/example"
    name, path = auto_url("page/example.mp4")
    assert name == "page/example.mp4"
    assert path == "/page/a/example.mp4"


def test_get_filename(create_app, req_ctx):
    from otterwiki.helper import get_filename

    assert get_filename("Home") == "home.md"
    assert get_filename("hOme") == "home.md"
    assert get_filename("Home.md") == "home.md"
    assert get_filename("HOME.MD") == "home.md"


def test_get_filename_raw(create_app_raw_filenames, req_ctx):
    from otterwiki.helper import get_filename

    assert get_filename("Home") == "Home.md"
    assert get_filename("hOme") == "hOme.md"
    assert get_filename("Home.md") == "Home.md"
    assert get_filename("HOME.MD") == "HOME.MD.md"


def test_get_attachment_directoryname(create_app, req_ctx):
    from otterwiki.helper import get_attachment_directoryname

    assert get_attachment_directoryname("Home.md") == "home"
    with pytest.raises(ValueError):
        assert get_attachment_directoryname("Home")
    assert get_attachment_directoryname("Another/Test.md") == "another/test"


def test_get_attachment_directoryname_raw(create_app_raw_filenames, req_ctx):

    from otterwiki.helper import get_attachment_directoryname

    assert get_attachment_directoryname("Home.md") == "Home"
    with pytest.raises(ValueError):
        assert get_attachment_directoryname("Home")
    assert get_attachment_directoryname("Another/Test.md") == "Another/Test"


def test_get_pagename(create_app, req_ctx):
    from otterwiki.helper import get_pagename

    assert "Example" == get_pagename("subspace/example.md")
    assert "Example" == get_pagename("subspace/example")
    assert "Subspace/Example" == get_pagename("subspace/example.md", full=True)
    assert "Subspace/Example" == get_pagename("subspace/example", full=True)
    assert "Example" == get_pagename("example.md")
    assert "Example" == get_pagename("example.md", full=True)
    # updated version wich respects upper and lowercase
    assert "ExamplE" == get_pagename("ExamplE")
    assert "Two Words" == get_pagename("two words.md")
    assert "Two Words" == get_pagename("two words")
    assert "Two words" == get_pagename("Two words")
    assert "Two words" == get_pagename("two words", header="Two words")
    # and with subdirectories
    assert "Two words" == get_pagename("subdir/two words", header="Two words")
    assert "Two words" == get_pagename(
        "subdir/two words.md", header="Two words"
    )
    assert "Two words" == get_pagename(
        "subdir1/subdir2/two words.md", header="Two words"
    )
    assert "Two Words" == get_pagename("subdir1/subdir2/two words.md")
    assert "Two Words" == get_pagename("subdir1/subdir2/Two Words")
    assert "Subdir/Two words" == get_pagename("subdir/Two words", full=True)
    assert "Two words/Two words" == get_pagename(
        "Two words/Two words", full=True
    )


def test_get_pagename_raw(create_app_raw_filenames, req_ctx):
    assert req_ctx
    assert create_app_raw_filenames

    from otterwiki.helper import get_pagename

    # testing raw page name functionality
    assert "example" == get_pagename("subspace/example.md")
    assert "example" == get_pagename(
        "subspace/example",
    )
    assert "subspace/example" == get_pagename("subspace/example.md", full=True)
    assert "subspace/example" == get_pagename("subspace/example", full=True)
    assert "example" == get_pagename("example.md")
    assert "example" == get_pagename("example.md", full=True)
    # updated version wich respects upper and lowercase
    assert "ExamplE" == get_pagename("ExamplE")
    assert "two words" == get_pagename("two words.md")
    assert "two words" == get_pagename("two words")
    assert "Two words" == get_pagename("Two words")
    assert "Two words" == get_pagename("two words", header="Two words")
    # and with subdirectories
    assert "Two words" == get_pagename("subdir/two words", header="Two words")
    assert "Two words" == get_pagename(
        "subdir/two words.md", header="Two words"
    )
    assert "Two words" == get_pagename(
        "subdir1/subdir2/two words.md", header="Two words"
    )
    assert "two words" == get_pagename("subdir1/subdir2/two words.md")
    assert "Two Words" == get_pagename("subdir1/subdir2/Two Words")
    assert "subdir/Two words" == get_pagename("subdir/Two words", full=True)
    assert "Two words/Two words" == get_pagename(
        "Two words/Two words", full=True
    )


def test_get_pagename_prefixes(test_client):
    from otterwiki.helper import get_pagename_prefixes
    from test_otterwiki import save_shortcut

    pages = ["Example", "Random page", "Directory/Content"]

    # Create test pages
    for pagename in pages:
        save_shortcut(
            test_client, pagename, f"# {pagename}", f"added {pagename}"
        )
    # session lives in this block
    with test_client:
        # View test pages
        for pagename in pages:
            rv = test_client.get("/{}".format(pagename))
            assert rv.status_code == 200
        assert sorted(get_pagename_prefixes()) == [
            'Directory',
            'Directory/Content',
            'Example',
            'Random page',
        ]
