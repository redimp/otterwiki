#!/usr/bin/env python

import os.path
import pathlib
import re
import unicodedata
from email.utils import parseaddr
import random
import string
import mimetypes
import time
import datetime
from functools import lru_cache


def ttl_lru_cache(ttl: int = 60, maxsize: int = 128):
    """
    Time aware lru caching thx to https://stackoverflow.com/a/73026174/212768
    """
    def wrapper(func):

        @lru_cache(maxsize)
        def inner(__ttl, *args, **kwargs):
            # Note that __ttl is not passed down to func,
            # as it's only used to trigger cache miss after some time
            return func(*args, **kwargs)
        return lambda *args, **kwargs: inner(time.time() // ttl, *args, **kwargs)
    return wrapper


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

def clean_slashes(value):
    '''This will insure that any path separated by slashes only has one
    slash between each dir and does not end in slash'''

    _split_path = value.split("/")

    # This will remove empty strings
    _path = [p for p in _split_path if p]

    value = "/".join(_path)
    return value

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
    value = re.sub(r"[?|$|.|!|#|\\]", r"", value)
    #old version below
    #value = re.sub(r"[?|$|.|!|#|/|\\]", r"", value)

    # remove leading -
    value = value.lstrip("-")
    # remove leading and trailing whitespaces
    value = value.strip()

    #remove trailing slash. even if creating a folder, we will default
    # to making it new_folder/Home
    # This is a while loop because the regex no longer take this char off outright, only when it ends in  "/"
    value = clean_slashes(value)

    return value


def split_path(path):
    if path == "":
        return []
    head = os.path.dirname(path)
    tail = os.path.basename(path)
    if head == os.path.dirname(head):
        return [tail]
    return split_path(head) + [tail]


def titleSs(s):
    """
    This function is a workaround for str.title() not knowing upercase 'ß'.
    """
    if 'ß' not in s:
        return s.title()
    magicword = 'M🙉A🙈G🙊I🐤C🐣W🐥O🦆R🐔D'
    while magicword in s:
        magicword = 2*magicword
    s = s.replace('ß',magicword)
    s = s.title()
    return s.replace(magicword,'ß')


def get_pagepath(pagename):
    return pagename


def get_page_directoryname(pagepath):
    parts = split_path(pagepath)
    return join_path(parts[:-1])


def join_path(path_arr):
    if len(path_arr) < 1:
        return ""
    return os.path.join(*path_arr)


def is_valid_email(email):
    if not type(email) == str:
        return False
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


def patchset2hunkdict(patchset):
    hunk_helper = {}
    _line_type_style = {
        " ": "",
        "+": "added",
        "-": "removed",
    }
    for file in patchset:
        for hunk in file:
            lines = {}
            for l in hunk.source_lines():
                if not l.source_line_no in lines:
                    lines[l.source_line_no] = []
                lines[l.source_line_no].append(
                    {
                        "source": l.source_line_no,
                        "target": l.target_line_no or "",
                        "type": l.line_type,
                        "style": _line_type_style[l.line_type],
                        "value": l.value,
                    }
                )
            for l in hunk.target_lines():
                if l.source_line_no is not None:
                    continue
                if not l.target_line_no in lines:
                    lines[l.target_line_no] = []
                lines[l.target_line_no].append(
                    {
                        "source": l.source_line_no or "",
                        "target": l.target_line_no,
                        "type": l.line_type,
                        "style": _line_type_style[l.line_type],
                        "value": l.value,
                    }
                )
            hunk_helper[
                (
                    file.source_file,
                    file.target_file,
                    hunk.source_start,
                    hunk.source_length,
                )
            ] = lines
    return hunk_helper


def get_local_timezone():
    """get the timezone the server is running on"""
    return datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo;

AXT_HEADING = re.compile(
    r' {0,3}(#{1,6})(?!#+)(?: *\n+|' r'\s+([^\n]*?)(?:\n+|\s+?#+\s*\n+))'
)
SETEX_HEADING = re.compile(r'([^\n]+)\n *(=|-){2,}[ \t]*\n+')

def get_header(content):
    filehead = content[:512]
    # find first markdown header in filehead
    heading = [line for (_, line) in AXT_HEADING.findall(filehead)]
    heading += [line for (line, _) in SETEX_HEADING.findall(filehead)]
    if len(heading):
        return heading[0]
    return None



# vim: set et ts=8 sts=4 sw=4 ai:
