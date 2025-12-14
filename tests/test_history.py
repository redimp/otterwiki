#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import re
from flask import url_for


def save_shortcut(test_client, pagename, content, commit_message):
    """Helper function to save a page"""
    rv = test_client.post(
        "/{}/save".format(pagename),
        data={
            "content": content,
            "commit": commit_message,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200


def test_page_history_links_after_rename(test_client, req_ctx):
    """Test that history page links work correctly after a page has been renamed"""

    # create a page with initial content
    original_pagename = "OriginalPageName"
    initial_content = "# Original Page\n\nThis is the initial content."
    save_shortcut(
        test_client, original_pagename, initial_content, "Initial commit"
    )

    # edit the page
    updated_content = "# Original Page\n\nThis is updated content."
    save_shortcut(
        test_client, original_pagename, updated_content, "Updated content"
    )

    # rename the page (first rename)
    first_rename = "FirstRenamedPage"
    rv = test_client.post(
        "/{}/rename".format(original_pagename),
        data={"new_pagename": first_rename, "message": "First rename"},
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # edit the page after first rename
    after_first_rename_content = (
        "# First Renamed Page\n\nContent after first rename."
    )
    save_shortcut(
        test_client,
        first_rename,
        after_first_rename_content,
        "Content after first rename",
    )

    # rename the page again (second rename)
    final_pagename = "FinalRenamedPage"
    rv = test_client.post(
        "/{}/rename".format(first_rename),
        data={"new_pagename": final_pagename, "message": "Second rename"},
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # edit the page after second rename
    final_content = (
        "# Final Renamed Page\n\nThis is content after second rename."
    )
    save_shortcut(
        test_client,
        final_pagename,
        final_content,
        "Content after second rename",
    )

    # get the history page
    history_response = test_client.get("/{}/history".format(final_pagename))
    assert history_response.status_code == 200
    history_html = history_response.data.decode()

    # extract all revision links from the history page
    revision_links = re.findall(
        r'<a href="([^"]*\?revision=[^"]*)">', history_html
    )

    # test that all revision links work (should return 200, not 404)
    failed_links = []
    for link in revision_links:
        if link.startswith('/'):
            link = link[1:]

        print(f"Testing revision link: /{link}")
        revision_response = test_client.get("/" + link)

        if revision_response.status_code == 404:
            failed_links.append(link)
            print(f"FAILED: Link /{link} returned 404")

    # verify we have 6 revisions (initial, update, first rename, content after first rename, second rename, final content)
    assert (
        len(revision_links) == 6
    ), f"Expected 6 revision links, got {len(revision_links)}"

    if failed_links:
        print(f"Failed links: {failed_links}")
        print(f"History HTML snippet: {history_html[:1000]}...")
        assert (
            False
        ), f"The following revision links returned 404: {failed_links}"

    print(f"All {len(revision_links)} revision links work correctly!")


def test_page_history_links_after_single_rename(test_client, req_ctx):
    """Test that history page links work correctly after a single page rename"""

    # create a page with initial content
    original_pagename = "SingleRenameTest"
    initial_content = "# Single Rename Test\n\nThis is the initial content."
    save_shortcut(
        test_client, original_pagename, initial_content, "Initial commit"
    )

    # edit the page
    updated_content = "# Single Rename Test\n\nThis is updated content."
    save_shortcut(
        test_client, original_pagename, updated_content, "Updated content"
    )

    # rename the page
    new_pagename = "SingleRenameTestRenamed"
    rv = test_client.post(
        "/{}/rename".format(original_pagename),
        data={"new_pagename": new_pagename, "message": "Renamed page"},
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # edit the page again after rename
    final_content = (
        "# Single Rename Test Renamed\n\nThis is content after rename."
    )
    save_shortcut(
        test_client, new_pagename, final_content, "Content after rename"
    )

    # get the history page
    history_response = test_client.get("/{}/history".format(new_pagename))
    assert history_response.status_code == 200
    history_html = history_response.data.decode()

    # extract all revision links from the history page
    revision_links = re.findall(
        r'<a href="([^"]*\?revision=[^"]*)">', history_html
    )

    # test that all revision links work (should return 200, not 404)
    failed_links = []
    for link in revision_links:
        if link.startswith('/'):
            link = link[1:]

        print(f"Testing revision link: /{link}")
        revision_response = test_client.get("/" + link)

        if revision_response.status_code == 404:
            failed_links.append(link)
            print(f"FAILED: Link /{link} returned 404")

    # verify we have 4 revisions
    assert (
        len(revision_links) == 4
    ), f"Expected 4 revision links, got {len(revision_links)}"

    if failed_links:
        print(f"Failed links: {failed_links}")
        print(f"History HTML snippet: {history_html[:1000]}...")
        assert (
            False
        ), f"The following revision links returned 404: {failed_links}"

    print(f"All {len(revision_links)} revision links work correctly!")
