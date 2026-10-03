#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import datetime
import difflib
import mimetypes
import os.path
import pathlib
import secrets
import re
import regex
import string
import time
import unicodedata
from hashlib import sha256
from functools import lru_cache
from typing import List, Tuple
from markupsafe import escape
from unidiff import PatchSet

# the cursor magic word which is ignored by the rendering
cursormagicword = "CuRsoRm4g1cW0Rd"


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

        return lambda *args, **kwargs: inner(
            time.time() // ttl, *args, **kwargs
        )

    return wrapper


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


# from https://github.com/Python-Markdown/markdown/blob/master/markdown/extensions/toc.py
def slugify(value, separator="-", keep_slashes=False):
    """Slugify a string, to make it URL friendly."""
    value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    if keep_slashes:
        value = re.sub(r"[^\w\s\-/]", "", value)
    else:
        value = re.sub(r"[^\w\s\-]", "", value)
    return re.sub(r"[%s\s]+" % separator, separator, value)


def clean_slashes(value):
    '''This will insure that any path separated by slashes only has one
    slash between each dir and does not end in slash'''

    _split_path = value.split("/")

    # This will remove empty strings
    _path = [p for p in _split_path if p]

    value = "/".join(_path)
    return value


def sanitize_pagename(value, allow_unicode=True, handle_md=False):
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    if handle_md:
        value = re.sub(r"\.md$", "", value)
    # remove slashes, question marks ...
    value = re.sub(r"[?|$|.|!|#|\\]", r"", value)

    # remove leading -/
    value = value.lstrip("-/")
    # remove leading and trailing whitespaces
    value = value.strip()

    # remove trailing slash and double slashes
    value = clean_slashes(value)

    return value


def sanitize_filename(value):
    """Unicode-preserving sanitizer for attachment filenames.

    Keeps Unicode (NFKC-normalized, matching sanitize_pagename) while
    removing path components and unsafe characters. Returns "" if nothing
    safe remains, so callers can fall back to secure_filename().
    """
    value = unicodedata.normalize("NFKC", str(value))
    # strip any directory components: keep only the final path segment,
    # treating both / and \ as separators
    value = value.replace("\\", "/").split("/")[-1]
    # remove NUL and control characters
    value = re.sub(r"[\x00-\x1f\x7f]", "", value)
    # strip leading/trailing whitespace and trailing dots (Windows)
    value = value.strip().rstrip(".").strip()
    # reject pure-traversal / empty names; leading dots (e.g. .gitignore)
    # are intentionally preserved
    if value in ("", ".", ".."):
        return ""
    return value


def split_path(path: str) -> List[str]:
    if path == "":
        return []
    head = os.path.dirname(path)
    tail = os.path.basename(path)
    if head == os.path.dirname(head):
        return [tail]
    return split_path(head) + [tail]


def titleSs(s):
    """
    This function is a workaround for str.title() not knowing uppercase 'ß'
    and treating the apostrophe as a word boundary.
    """
    _eszett = ''
    if 'ß' in s:
        _eszett = 'E🙉S🙈Z🙊E🐤T🐣T'
        while _eszett in s:
            _eszett = 2 * _eszett
        s = s.replace('ß', _eszett)
    _apostrophe = ''
    if "'" in s:
        _apostrophe = 'A🙉P🙈O🙊S🐤T🐣R🐥O🦆P🐔H🦜E'
        while _apostrophe in s:
            _apostrophe = 2 * _apostrophe
        s = s.replace("'", _apostrophe)
    s = s.title()
    if _eszett:
        s = re.sub(re.escape(_eszett), 'ß', s, flags=re.IGNORECASE)
    if _apostrophe:
        s = re.sub(re.escape(_apostrophe), "'", s, flags=re.IGNORECASE)
    return s


def get_pagepath(pagename):
    return pagename


def get_page_directoryname(pagepath: str) -> str:
    parts = split_path(pagepath)
    return join_path(parts[:-1])


def join_path(path_arr: List[str]) -> str:
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


def random_password(len=16):
    return "".join(
        secrets.choice(string.ascii_lowercase + string.digits)
        for _ in range(len)
    )


def empty(what):
    if what is None:
        return True
    if isinstance(what, str) and what.strip() == "":
        return True
    return False


def int_or_None(in_val: any) -> int | None:
    """
    Accepts any parameter and attempts to cast it to an integer, rounding down.
    If the cast is successful, it returns the integer.
    If the cast fails, it returns None.

    Args:
        in_val: The parameter to be cast to an integer.

    Returns:
        The integer representation of the input, or None if the cast fails.
    """
    try:
        return int(
            float(in_val)
        )  # Cast to float first, then to int, rounding down
    except (ValueError, TypeError):
        return None


def guess_mimetype(path):
    mimetype, encoding = mimetypes.guess_type(path)
    if mimetype is None:
        mimetype = "application/octet-stream"
    return mimetype


def mkdir(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def patchset2filedict(patchset):
    _line_type_style = {
        " ": "",
        "+": "added",
        "-": "removed",
        "\\": "",  # line.line_type='\\' line.value=' No newline at end of file\n'
    }
    files = {}
    for file in patchset:
        line_data = []
        for hunk in file:
            line_data.append(
                {
                    "source": "",
                    "target": "",
                    "value": f"@@ {hunk.source_start},{hunk.source_length} {hunk.target_start},{hunk.target_length} @@",
                    "style": "hunk",
                }
            )
            for line in hunk:
                line_data.append(
                    {
                        "source": line.source_line_no or "",
                        "target": line.target_line_no or "",
                        "type": line.line_type,
                        "style": _line_type_style[line.line_type],
                        "value": line.value,
                        "hunk": False,
                    }
                )
        files[file.path] = line_data

    return files


def normalize_content(content):
    """
    Normalize page content like saving a page does: unix line endings, no
    leading or trailing whitespace, a single newline at the end.
    """
    return content.replace("\r\n", "\n").strip() + "\n"


def diff_content(content_a, content_b, filename="page.md"):
    """
    Diff two versions of a text, returns the lines of the diff in the format
    of patchset2filedict(). The texts are normalized with normalize_content(),
    so line endings and a missing newline at the end don't show up as changes.
    """
    diff = "".join(
        difflib.unified_diff(
            normalize_content(content_a).splitlines(keepends=True),
            normalize_content(content_b).splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
    )
    if not diff:
        return []
    return list(patchset2filedict(PatchSet(diff)).values())[0]


_DIFF_WORDS_RE = re.compile(r"\w+|\s+|[^\w\s]")


def diff_words(line_a, line_b, min_ratio=0.4):
    """
    Compare two versions of a line word by word. Returns the html of both
    lines with the changed words wrapped in <span class="diff-word">, or
    None if the lines are too different for a word diff to be helpful.
    """
    words_a = _DIFF_WORDS_RE.findall(line_a)
    words_b = _DIFF_WORDS_RE.findall(line_b)
    matcher = difflib.SequenceMatcher(None, words_a, words_b, autojunk=False)
    if matcher.ratio() < min_ratio:
        return None

    def _html(words, changed):
        text = str(escape("".join(words)))
        if changed and text:
            return f'<span class="diff-word">{text}</span>'
        return text

    html_a, html_b = [], []
    for op, a1, a2, b1, b2 in matcher.get_opcodes():
        html_a.append(_html(words_a[a1:a2], op != "equal"))
        html_b.append(_html(words_b[b1:b2], op != "equal"))
    return "".join(html_a), "".join(html_b)


def diff_side_by_side(lines):
    """
    Arrange the lines of a diff (in the format of patchset2filedict()) in two
    columns: removed lines on the left, added lines on the right and
    unchanged lines on both sides. Returns a list of rows, either
    {"hunk": value} or {"left": line or None, "right": line or None}.
    """
    rows = []
    removed = []
    added = []

    def flush():
        # pair a block of removed lines with the following added lines
        for i in range(max(len(removed), len(added))):
            rows.append(
                {
                    "left": removed[i] if i < len(removed) else None,
                    "right": added[i] if i < len(added) else None,
                }
            )
        removed.clear()
        added.clear()

    for line in lines:
        if line["style"] == "hunk":
            flush()
            rows.append({"hunk": line["value"]})
        elif line["type"] == "-":
            if added:
                flush()
            removed.append(line)
        elif line["type"] == "+":
            added.append(line)
        elif line["type"] == " ":
            flush()
            rows.append({"left": line, "right": line})
    flush()
    return rows


def diff_side_by_side_html(lines, html_a=None, html_b=None):
    """
    Arrange the lines of a diff like diff_side_by_side() and prepare the
    cells for templates/snippets/diff_side_by_side.html. html_a and html_b
    are the highlighted lines of both versions, see pygments_render_lines(),
    lines without highlighting are escaped. Returns a list of rows, either
    {"hunk": value} or {"left": cell, "right": cell, "context": bool} with
    a cell being None or {"number": .., "style": .., "html": ..}.
    """

    def _cell(line, number, html_lines):
        if line is None:
            return None
        if html_lines and 0 < number <= len(html_lines):
            html = html_lines[number - 1]
        else:
            html = str(escape(line["value"].rstrip("\n")))
        return {"number": number, "style": line["style"], "html": html}

    rows = []
    for row in diff_side_by_side(lines):
        if "hunk" in row:
            rows.append(row)
            continue
        left, right = row["left"], row["right"]
        left_cell = _cell(left, left and left["source"], html_a)
        right_cell = _cell(right, right and right["target"], html_b)
        if left and right and left["style"] == "removed":
            # a changed line: mark the changed words instead of the
            # markdown syntax, so small changes in long lines stand out
            words = diff_words(
                left["value"].rstrip("\n"), right["value"].rstrip("\n")
            )
            if words is not None:
                left_cell["html"], right_cell["html"] = words
        rows.append(
            {
                "left": left_cell,
                "right": right_cell,
                # unchanged lines are shortened in the diff
                "context": bool(left and left["style"] == ""),
            }
        )
    return rows


def get_local_timezone():
    """get the timezone the server is running on"""
    return datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo


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


def strfdelta_round(tdelta, round_period='second'):
    """timedelta to string,    use for measure running time
    attend period from days downto smaller period, round to minimum period
    omit zero value period

    thanks to https://stackoverflow.com/a/64257852/212768
    """
    period_names = ('week', 'day', 'hour', 'minute', 'second', 'millisecond')
    if round_period not in period_names:
        raise Exception(
            f'round_period "{round_period}" invalid, should be one of {",".join(period_names)}'
        )
    period_seconds = (604800, 86400, 3600, 60, 1, 1 / pow(10, 3))
    period_desc = ('weeks', 'days', 'hours', 'mins', 'secs', 'msecs')
    round_i = period_names.index(round_period)

    s = ''
    remainder = tdelta.total_seconds()
    for i in range(len(period_names)):
        q, remainder = divmod(remainder, period_seconds[i])
        if int(q) > 0:
            if not len(s) == 0:
                s += ' '
            if q > 1:
                s += f'{q:.0f} {period_desc[i]}'
            else:
                s += f'{q:.0f} {period_desc[i][:-1]}'
        if i == round_i:
            break
        if i == round_i + 1:
            if remainder > 1:
                s += f'{remainder} {period_desc[round_i]}'
            else:
                s += f'{remainder} {period_desc[round_i][:-1]}'
            break

    return s


def is_valid_name(
    name: str,
    min_length: int = 1,
    max_length: int = 50,
) -> Tuple[bool, str]:
    """
    Validates if a name meets security and usability requirements,
    supporting international characters.

    Args:
        name: The name to validate
        min_length: Minimum acceptable length
        max_length: Maximum acceptable length

    Returns:
        A tuple containing (is_valid, reason_if_invalid)
    """

    # Check if name is None or empty
    if not name or name.strip() == "":
        return False, "name cannot be empty"

    # Trim whitespace
    name = name.strip()

    # Check length
    if len(name) < min_length:
        return (
            False,
            f"name must be at least {min_length} character(s) long",
        )
    if len(name) > max_length:
        return False, f"name cannot exceed {max_length} characters"

    # Normalize unicode characters
    name = unicodedata.normalize('NFC', name)

    # Check for invisible/control characters
    if any(unicodedata.category(char).startswith('C') for char in name):
        return (
            False,
            f"name contains invisible or control characters",
        )

    # Allow letters from any language, spaces, hyphens, apostrophes
    # Common in names across cultures: spaces, hyphens, apostrophes, periods
    valid_chars: str = r'^[\p{L}\s\'\-\.]+$'

    if not regex.match(valid_chars, name, regex.UNICODE):
        return (
            False,
            f"name can only contain letters, spaces, hyphens, apostrophes, and periods",
        )

    # Check for reasonable spacing (no double spaces, etc.)
    if '  ' in name:
        return False, f"name cannot contain consecutive spaces"

    # Check for reasonable use of special characters
    if re.search(r'[\'\-\.]{2,}', name):
        return (
            False,
            f"name cannot contain consecutive special characters",
        )

    # Check for names that are just special characters
    if regex.match(r'^[\s\'\-\.]+$', name):
        return False, f"name must contain at least one letter"

    # Check for names that are suspiciously repetitive
    if re.search(r'(.)\1{4,}', name):
        return (
            False,
            f"name contains too many consecutive repeated characters",
        )

    # Check for common placeholder names
    placeholder_names: list[str] = [
        "test",
        "user",
        "name",
        "firstname",
        "lastname",
        "first",
        "last",
        "none",
        "nil",
        "null",
        "undefined",
        "anonymous",
        "unknown",
    ]
    if name.lower() in placeholder_names:
        return False, f"name appears to be a placeholder"

    # Check for names with excessive capitalization
    if name.isupper() and len(name) > 2:
        return False, f"name should not be all uppercase"

    return True, f"name is valid"


def unquote_git_path(s: str) -> str:
    # with git `config core.quotepath = True` converts "unusual" utf-8 with bytes > 0x80 to octcal e.g. \302\265
    # see https://git-scm.com/docs/git-config#Documentation/git-config.txt-corequotePath
    # We want to have utf-8, so we do
    # 1. encode in bytes, 2. decode and interpret the byte values, 3. encode back in bytes and 4. finally to a proper utf-8 string
    return s.encode().decode("unicode_escape").encode("latin1").decode("utf-8")


def get_PatchSet(s: str) -> PatchSet:
    """
    Proxy as workaround for unidiff.PatchSet not supporting quotes in filenames (yet).
    """

    RE_DIFF_HEAD_WITH_QUOTED_FILENAMES = re.compile(
        r'^diff --git (\"(?P<source>a/[^\t\n]+)\") (\"(?P<target>b/[^\t\n]+)\")$',
        flags=re.M,
    )

    m = RE_DIFF_HEAD_WITH_QUOTED_FILENAMES.search(s)

    while m is not None:
        source = m.group('source')
        target = m.group('target')
        # remove escaping from the quotes
        source_n = source.replace('\\"', '"')
        target_n = target.replace('\\"', '"')
        source_n = unquote_git_path(source_n)
        target_n = unquote_git_path(target_n)
        s = s.replace(m.group(0), f"diff --git {source_n} {target_n}")
        s = re.sub(
            r'^--- "' + re.escape(source) + '"', source_n, s, flags=re.M
        )
        s = re.sub(
            r'^\+\+\+ "' + re.escape(target) + '"', target_n, s, flags=re.M
        )
        m = RE_DIFF_HEAD_WITH_QUOTED_FILENAMES.search(s)

    return PatchSet(s)


def sha256sum(s: str) -> str:
    hash = sha256()
    hash.update(s.encode())
    return hash.hexdigest()


def compute_webhook_hash(secret_key: str, remote_url: str) -> str:
    import hmac

    return hmac.new(
        secret_key.encode(),
        remote_url.encode(),
        sha256,
    ).hexdigest()


def compute_webhook_hash_legacy(remote_url: str) -> str:
    return sha256((remote_url + 'otterwiki').encode()).hexdigest()
