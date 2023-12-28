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


def get_filename(pagepath):
    '''This is the actual filepath on disk (not via URL) relative to the repository root
    This function will attempt to determine if this is a 'folder' or a 'page'.
    '''

    p = pagepath.lower()
    p = clean_slashes(p)

    if not p.endswith(".md"):
        return "{}.md".format(p)

    return p


def get_attachment_directoryname(filename):
    filename = filename.lower()
    if filename[-3:] != ".md":
        raise ValueError
    return filename[:-3]

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


def get_pagename(filepath, full=False, header=None):
    '''This will derive the page name (displayed on the web page) from the url requested'''
    # remove trailing slashes from filepath
    filepath=filepath.rstrip("/")

    if filepath.endswith(".md"):
        filepath = filepath[:-3]

    arr = split_path(filepath)
    for i, part in enumerate(arr):
        hint = part
        # if basename use header as hint
        if i == len(arr)-1 and header is not None:
            hint = header
        if (hint != part and hint.lower() == part.lower()) \
                or (hint == part and hint != part.lower()):
            arr[i] = hint
        else:
            arr[i] = titleSs(part)

    if not full:
        return arr[-1]
    return "/".join(arr)


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

def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    https://stackoverflow.com/a/35804945

    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present 

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    import logging

    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
       raise AttributeError('{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
       raise AttributeError('{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
       raise AttributeError('{} already defined in logger class'.format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)
    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)


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

# vim: set et ts=8 sts=4 sw=4 ai:
