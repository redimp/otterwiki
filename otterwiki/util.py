#!/usr/bin/env python

import os.path
import pathlib
import re
import unicodedata
from email.utils import parseaddr
import random
import string
import mimetypes


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


# from https://github.com/Python-Markdown/markdown/blob/master/markdown/extensions/toc.py
def slugify(value, separator="-"):
    """Slugify a string, to make it URL friendly."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore")
    value = re.sub(r"[^\w\s-]", "", value.decode("ascii")).strip().lower()
    return re.sub(r"[%s\s]+" % separator, separator, value)


def sanitize_pagename(value, allow_unicode=True):
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    # remove slashes, question marks ...
    value = re.sub(r"[?|$|.|!|#|/|\\]", r"", value)
    # remove leading -
    value = value.lstrip("-")
    # remove leading and trailing whitespaces
    value = value.strip()
    return value


def split_path(path):
    if path == "":
        return []
    head = os.path.dirname(path)
    tail = os.path.basename(path)
    if head == os.path.dirname(head):
        return [tail]
    return split_path(head) + [tail]


def get_filename(pagepath):
    '''This is the actual filepath on disk (not via URL) relative to the repository root
    This function will attempt to determine if this is a 'folder' or a 'page'.
    '''

    p = pagepath.lower()
    if not p.endswith(".md"):
        return "{}.md".format(p)
    return p


def get_attachment_directoryname(filename):
    filename = filename.lower()
    if filename[-3:] != ".md":
        raise ValueError
    return filename[:-3]


def get_pagename(filepath):
    '''This will derive the page name (displayed on the web page) from the url requested'''
    name = os.path.basename(filepath)
    if name.endswith(".md"):
        name = name[:-3]
        name = name.title()
    return name


def get_pagepath(pagename):
    return pagename


def join_path(path_arr):
    return os.path.join(*path_arr)


def is_valid_email(email):
    mail_regexp = re.compile(
        r"([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\[[\t -Z^-~]*])"
    )
    return mail_regexp.fullmatch(email) is not None


def random_password(len=8):
    return "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(len)
    )


def empty(what):
    if what is None:
        return True
    if isinstance(what, str) and what.strip() == "":
        return True
    return False


def guess_mimetype(path):
    mimetype, encoding = mimetypes.guess_type(path)
    return mimetype


def mkdir(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


# vim: set et ts=8 sts=4 sw=4 ai:
