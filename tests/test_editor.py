#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import re
import bs4
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
            # check uploadUrl
            m = re.search(r"uploadUrl: \"/([^\"]+)/inline_attachment\",", js)
            assert m
            uploadUrl_found = True
            # unquote to check if the url matches the pagename
            uploadUrl = unquote(m.group(1))
            assert uploadUrl == pagename
            # check fetchUrl preview
            m = re.search(r"fetch\(\"/([^\"]+)/preview\",", js)
            assert m
            fetchUrl_found = True
            # unquote to check if the url matches the pagename
            fetchUrl = unquote(m.group(1))
            assert fetchUrl == pagename

        # make sure the right block has been found and checked
        assert uploadUrl_found
        assert fetchUrl_found
