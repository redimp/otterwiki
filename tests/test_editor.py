#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import re
import bs4
import json
from urllib.parse import unquote


def test_urlquote(test_client):
    for pagename in [
        "Example",
        "Example with space",
        "ExampleWith\"Doublequote",
        "Example'SingleQuote'",
        "Example_",
        "Example-Example",
        "Example_Example",
        "🙂",
        "Example '\"🙂",
    ]:
        html = test_client.get("/{}/edit".format(pagename)).data.decode()
        soup = bs4.BeautifulSoup(html, "html.parser")
        uploadUrl_found, fetchUrl_found = False, False
        for javascript in soup.find_all(
            "script", type="text/javascript", src=""
        ):
            js = javascript.text
            if "uploadUrl" not in js:
                continue
            # check uploadUrl - now using tojson filter which produces JSON strings
            m = re.search(r'uploadUrl: ("(?:[^"\\]|\\.)*"),', js)
            assert m, f"Could not find uploadUrl in JavaScript for {pagename}"
            uploadUrl_found = True
            # parse the JSON string and unquote to check if the url matches the pagename
            uploadUrl_json = json.loads(m.group(1))
            uploadUrl_path = uploadUrl_json.rsplit('/inline_attachment', 1)[0]
            uploadUrl = unquote(uploadUrl_path.lstrip('/'))
            assert (
                uploadUrl == pagename
            ), f"uploadUrl mismatch: {uploadUrl} != {pagename}"

            # check fetchUrl preview - also using tojson filter
            m = re.search(r'fetch\(("(?:[^"\\]|\\.)*"),', js)
            assert m, f"Could not find fetch URL in JavaScript for {pagename}"
            fetchUrl_found = True
            # parse the JSON string and unquote to check if the url matches the pagename
            fetchUrl_json = json.loads(m.group(1))
            fetchUrl_path = fetchUrl_json.rsplit('/preview', 1)[0].rsplit(
                '/draft', 1
            )[0]
            fetchUrl = unquote(fetchUrl_path.lstrip('/'))
            assert (
                fetchUrl == pagename
            ), f"fetchUrl mismatch: {fetchUrl} != {pagename}"

        # make sure the right block has been found and checked
        assert uploadUrl_found
        assert fetchUrl_found
