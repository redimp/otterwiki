#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import pytest
from otterwiki.util import (
    sha256sum,
    sizeof_fmt,
    slugify,
    split_path,
    join_path,
    is_valid_email,
    empty,
    sanitize_pagename,
    get_pagepath,
    get_page_directoryname,
    random_password,
    mkdir,
    titleSs,
    patchset2filedict,
    get_header,
    strfdelta_round,
    is_valid_name,
    int_or_None,
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
    # test keep_slashes=True for use with pagepath
    assert slugify("abc", keep_slashes=True) == "abc"
    assert (
        slugify("Some Random Sub/with/A page", keep_slashes=True)
        == "some-random-sub/with/a-page"
    )
    assert (
        slugify("Multiple    Spaces", keep_slashes=True) == "multiple-spaces"
    )
    assert (
        slugify("With Trailing Slash/", keep_slashes=True)
        == "with-trailing-slash/"
    )


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
    for e in ["", " ", None]:
        assert is_valid_email(e) is False


def test_is_valid_name():
    for n in [
        "James S. A. Corey",
        "Marc-Uwe Kling",
        "Masamune Shirow 士郎 正宗",
        "Liu Cixin 刘慈欣",
        "Félix José Palma Macías",
        "Peter Høeg",
    ]:
        assert is_valid_name(n)[0] is True
    for n in ["", "A"]:
        assert is_valid_name(n, min_length=2)[0] is False
    for n in [
        "Click for discount drugs: http://example.com/uri",
        "<random tags>",
        "Click%20for%20discount%20drugs%3A%20http%3A%2F%2Fexample.com%2Furi",
    ]:
        assert is_valid_name(n)[0] is False


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
    assert sanitize_pagename("IT/SystemD") == "IT/SystemD"
    assert sanitize_pagename("IT/SystemD.md") == "IT/SystemDmd"
    # test handle_md (issue #344)
    assert sanitize_pagename("IT/SystemD", handle_md=True) == "IT/SystemD"
    assert sanitize_pagename("IT/Systemd", handle_md=True) == "IT/Systemd"
    assert sanitize_pagename("IT/Systemd.md", handle_md=True) == "IT/Systemd"


def test_random_password():
    p16_1 = random_password(16)
    p16_2 = random_password(16)
    assert len(p16_1) == 16
    assert p16_1 != p16_2


def test_get_pagepath():
    assert "Home" == get_pagepath("Home")


def test_get_page_directoryname():
    assert "" == get_page_directoryname("Home")
    assert "Sub" == get_page_directoryname("Sub/Dir")
    assert "Sub" == get_page_directoryname("/Sub/Dir")
    assert "Sub/Dir" == get_page_directoryname("/Sub/Dir/Page")


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
    assert "Test M🙉A🙈G🙊I🐤C🐣W🐥O🦆R🐔D" == titleSs(
        "Test M🙉A🙈G🙊I🐤C🐣W🐥O🦆R🐔D"
    )
    assert "\"Foobarß\"" == titleSs("\"foobarß\"")
    assert "Foobarß" == titleSs("foobarß")


def test_patchset2filedict():
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
    fd = patchset2filedict(p)
    assert len(fd.keys()) == 1
    assert list(fd.keys())[0] == "test_show_commit.md"


def test_get_header():
    md = """# simple

random text.
"""
    assert "simple" == get_header(md)

    md = """#    simple with spaces

random text.
"""
    assert "simple with spaces" == get_header(md)

    md = """random block

# first header

random text.
"""
    assert "first header" == get_header(md)

    md = """random block

# first header

random text.

## second header

random text.
"""
    assert "first header" == get_header(md)

    md = """random block

some header
===========

random text.

second header
-------------

random text.
"""
    assert "some header" == get_header(md)


def test_strfdelta_round():
    from datetime import timedelta

    assert (
        strfdelta_round(timedelta(seconds=2), round_period="second")
        == "2 secs"
    )
    assert (
        strfdelta_round(
            timedelta(hours=1, minutes=2, seconds=3), round_period="second"
        )
        == "1 hour 2 mins 3 secs"
    )
    assert (
        strfdelta_round(timedelta(days=1, seconds=3), round_period="second")
        == "1 day 3 secs"
    )
    assert (
        strfdelta_round(
            timedelta(days=4, hours=3, minutes=1, seconds=3),
            round_period="second",
        )
        == "4 days 3 hours 1 min 3 secs"
    )
    assert strfdelta_round(timedelta(seconds=2), round_period="minute") == ""
    assert (
        strfdelta_round(timedelta(days=21), round_period="minute") == "3 weeks"
    )


def test_int_or_None():
    assert int_or_None(10) == 10
    assert int_or_None("20") == 20
    assert int_or_None([1, 2]) is None
    assert int_or_None(None) is None
    assert int_or_None("abc") is None
    assert int_or_None(3.14) == 3
    assert int_or_None("") is None
    assert int_or_None(True) == 1
    assert int_or_None(False) == 0
    assert int_or_None(10.9) == 10
    assert int_or_None(2.7) == 2


def test_sha256sum():
    assert (
        sha256sum("")
        == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert (
        sha256sum("\n")
        == "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b"
    )
    assert (
        sha256sum("An Otter Wiki")
        == "c0b00e171401dfa2c70f2524fa977d66ead451ec9837543556fc66087b211646"
    )
