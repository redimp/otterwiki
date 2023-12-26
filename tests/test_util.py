#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import pytest
from otterwiki.util import (
    sizeof_fmt,
    slugify,
    split_path,
    join_path,
    is_valid_email,
    empty,
    sanitize_pagename,
    get_filename,
    get_attachment_directoryname,
    get_pagename,
    get_pagepath,
    random_password,
    mkdir,
    titleSs,
    patchset2hunkdict,
)


def test_sizeof_fmt():
    assert sizeof_fmt(1024) == "1.0KiB"
    assert sizeof_fmt(1024**2) == "1.0MiB"
    assert sizeof_fmt(4 * 1024**3) == "4.0GiB"
    assert sizeof_fmt(8.5 * 1024**4) == "8.5TiB"
    assert sizeof_fmt(512) == "512.0B"
    assert sizeof_fmt(42 * 1024**8) == "42.0YiB"


def test_slugigy():
    assert slugify("") == ""
    assert slugify("abc") == "abc"
    assert slugify("a b c") == "a-b-c"
    assert slugify("a    b") == "a-b"
    assert slugify("äüöÄÜÖß") == "auoauo"


def test_split_path():
    assert split_path("a/b") == ["a", "b"]
    assert split_path("a/b /c") == ["a", "b ", "c"]


def test_join_path():
    assert join_path(["a", "b"]) == "a/b"


def test_split_and_join_path():
    for x in [["a", "b"], ["c", "d", "e"]]:
        assert split_path(join_path(x)) == x
    for x in ["a/b", "c/d/e"]:
        assert join_path(split_path(x)) == x


def test_is_valid_email():
    for e in ["mail@example.de", "mail.mail@mail.example.tld", "ex@mp-le.com"]:
        assert is_valid_email(e) is True
    for e in ["@example.com", "mail@", "mail@.example.com", "john"]:
        assert is_valid_email(e) is False


def test_empty():
    assert empty(None) is True
    assert empty("") is True
    assert empty(" ") is True
    assert empty("x") is False
    assert empty(0) is False


def test_sanitize_pagename():
    assert sanitize_pagename("abc") == "abc"
    assert sanitize_pagename("-abc") == "abc"
    assert sanitize_pagename("-") == ""
    assert sanitize_pagename("Abc Def") == "Abc Def"
    assert sanitize_pagename("////abc") == "abc"
    assert sanitize_pagename("////abc") == "abc"
    assert sanitize_pagename("😊") == "😊"
    assert sanitize_pagename("\\\\abc") == "abc"
    assert sanitize_pagename("abc", allow_unicode=False) == "abc"


def test_random_password():
    p16_1 = random_password(16)
    p16_2 = random_password(16)
    assert len(p16_1) == 16
    assert p16_1 != p16_2


def test_get_filename():
    assert get_filename("Home") == "home.md"
    assert get_filename("hOme") == "home.md"
    assert get_filename("Home.md") == "home.md"
    assert get_filename("HOME.MD") == "home.md"


def test_get_attachment_directoryname():
    assert get_attachment_directoryname("Home.md") == "home"
    with pytest.raises(ValueError):
        assert get_attachment_directoryname("Home")


def test_get_pagepath():
    assert "Home" == get_pagepath("Home")


def test_get_pagename():
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
    assert "Two words" == get_pagename("subdir/two words.md", header="Two words")
    assert "Two words" == get_pagename("subdir1/subdir2/two words.md", header="Two words")
    assert "Two Words" == get_pagename("subdir1/subdir2/two words.md")
    assert "Two Words" == get_pagename("subdir1/subdir2/Two Words")
    assert "Subdir/Two words" == get_pagename("subdir/Two words", full=True)
    assert "Two words/Two words" == get_pagename("Two words/Two words", full=True)


def test_mkdir(tmpdir):
    tmpdir.mkdir("aa")
    path_a = "aa"
    mkdir(path=tmpdir.join(path_a))
    assert os.path.exists(tmpdir.join("aa"))

    path_b = "aa/bb/cc/dd"
    mkdir(path=tmpdir.join(path_b))
    assert os.path.exists(tmpdir.join(path_b))

    path_c = "bb/cc/dd"
    mkdir(path=tmpdir.join(path_c))
    assert os.path.exists(tmpdir.join(path_c))

def test_titleSs():
    assert "Abc Def" == titleSs("abc dEf")
    assert "ßabc Def" == titleSs("ßabc def")
    assert "Åbcd Éfgh" == titleSs("åbcd éfgh")
    assert "Test Magicword" == titleSs("Test MAGICWORD")

def test_patchset2hunkdict():
    from unidiff import PatchSet
    diff = """diff --git a/test_show_commit.md b/test_show_commit.md
index 72943a1..f761ec1 100644
--- a/test_show_commit.md
+++ b/test_show_commit.md
@@ -1 +1 @@
-aaa
+bbb
"""
    p = PatchSet(diff)
    hd = patchset2hunkdict(p)
    # there is only one hunk
    assert len(hd.keys()) == 1
    k = list(hd.keys())[0]
    # check dict keys
    assert k[0] == 'a/test_show_commit.md'
    assert k[1] == 'b/test_show_commit.md'
    # check line 1
    line = hd[k][1]
    assert line[0]['source'] == 1
    assert line[1]['target'] == 1
    assert line[0]['type'] == "-"
    assert line[1]['type'] == "+"
    assert line[0]['style'] == "removed"
    assert line[1]['style'] == "added"
    assert line[0]['value'] == "aaa\n"
    assert line[1]['value'] == "bbb\n"
