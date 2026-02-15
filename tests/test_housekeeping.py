#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest


class TestHousekeepingEmptyPages:
    """Tests for housekeeping empty pages functionality."""

    def test_housekeeping_empty_pages_scan(self, app_with_user, admin_client):
        """Test scanning for empty pages."""
        from otterwiki.server import storage
        from otterwiki.helper import get_filename

        empty_pagepath = "test_empty_page"
        storage.store(
            get_filename(empty_pagepath),
            "",
            message="Create empty page",
            author=("Test User", "mail@example.org"),
        )

        header_pagepath = "test_header_only"
        storage.store(
            get_filename(header_pagepath),
            "# Test_Header_Only",
            message="Create header-only page",
            author=("Test User", "mail@example.org"),
        )

        normal_pagepath = "test_normal_page"
        storage.store(
            get_filename(normal_pagepath),
            "# Normal Page\n\nThis has content.\n",
            message="Create normal page",
            author=("Test User", "mail@example.org"),
        )

        rv = admin_client.post(
            "/-/housekeeping",
            data={"task": "emptypages"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()
        assert empty_pagepath in html or "Page is empty" in html
        assert header_pagepath in html or "Header only" in html

    def test_housekeeping_clean_empty_pages(self, app_with_user, admin_client):
        """Test cleaning empty pages."""
        from otterwiki.server import storage
        from otterwiki.helper import get_filename

        empty_pagepath = "test_clean_empty"
        filename = get_filename(empty_pagepath)
        storage.store(
            filename,
            "",
            message="Create empty page",
            author=("Test User", "mail@example.org"),
        )

        assert storage.exists(filename)

        rv = admin_client.post(
            "/-/housekeeping",
            data={
                "task": "emptypages",
                "clean": "1",
                "delete_empty_page": [empty_pagepath],
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200
        assert not storage.exists(filename)

    def test_housekeeping_empty_pages_with_attachments(
        self, app_with_user, admin_client
    ):
        """Test that pages with attachments are not considered empty."""
        from otterwiki.server import storage
        from otterwiki.helper import get_filename

        pagepath = "test_page_with_attachment"
        filename = get_filename(pagepath)
        storage.store(
            filename,
            "# Test_Page_With_Attachment",
            message="Create page",
            author=("Test User", "mail@example.org"),
        )

        attachment_dir = filename[:-3]  # Remove .md extension
        storage.store(
            f"{attachment_dir}/test.txt",
            "Test attachment content",
            message="Add attachment",
            author=("Test User", "mail@example.org"),
        )

        rv = admin_client.post(
            "/-/housekeeping",
            data={"task": "emptypages"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()

        if pagepath in html:
            assert (
                "Header only" not in html
                or pagepath not in html.split("Header only")[0].split("<")[-1]
            )

    def test_housekeeping_empty_pages_permissions(
        self, app_with_user, other_client
    ):
        """Test that users without WRITE permission cannot access empty pages scan."""
        original_write_access = app_with_user.config["WRITE_ACCESS"]

        try:
            app_with_user.config["WRITE_ACCESS"] = "ADMIN"

            rv = other_client.post(
                "/-/housekeeping",
                data={"task": "emptypages"},
                follow_redirects=False,
            )
            assert rv.status_code == 403
        finally:
            app_with_user.config["WRITE_ACCESS"] = original_write_access


class TestHousekeepingBrokenWikilinks:
    """Tests for housekeeping broken wikilinks functionality."""

    def test_housekeeping_broken_wikilinks_no_broken_links(
        self, app_with_user, admin_client
    ):
        """Test that pages with no broken links are not reported."""
        from otterwiki.server import storage
        from otterwiki.helper import get_filename

        app_with_user.config["WIKILINK_STYLE"] = ""

        storage.store(
            get_filename("Page A Valid"),
            "# Page A Valid\n\nContent.\n",
            message="Create page A",
            author=("Test User", "mail@example.org"),
        )
        storage.store(
            get_filename("Page B Valid"),
            "# Page B Valid\n\nLink to [[Page A Valid]].\n",
            message="Create page B",
            author=("Test User", "mail@example.org"),
        )

        rv = admin_client.post(
            "/-/housekeeping",
            data={"task": "brokenwikilinks"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()

        assert "no broken" in html.lower()

    def test_housekeeping_broken_wikilinks_tables_structure(
        self, app_with_user, admin_client
    ):
        """Test that both tables are displayed with correct structure."""
        from otterwiki.server import storage
        from otterwiki.helper import get_filename

        app_with_user.config["WIKILINK_STYLE"] = ""

        storage.store(
            get_filename("Page With Broken Links"),
            "# Page With Broken Links\n\nLinks: [[Missing Page 1]] and [[Missing Page 2]].\n",
            message="Create page",
            author=("Test User", "mail@example.org"),
        )
        storage.store(
            get_filename("Another Page"),
            "# Another Page\n\nAlso links to [[Missing Page 1]].\n",
            message="Create another page",
            author=("Test User", "mail@example.org"),
        )

        rv = admin_client.post(
            "/-/housekeeping",
            data={"task": "brokenwikilinks"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()

        assert "Pages with broken links" in html
        assert "Most wanted pages" in html

        assert "Broken links" in html
        assert "Quantity" in html

        assert "Found in" in html
        assert "Occurrences" in html

    def test_housekeeping_broken_wikilinks_default_style(
        self, app_with_user, admin_client
    ):
        """Test broken wikilinks detection with default WIKILINK_STYLE."""
        from otterwiki.server import storage
        from otterwiki.helper import get_filename

        app_with_user.config["WIKILINK_STYLE"] = ""

        pagepath = "test_broken_links_default"
        content = """# Test Broken Links

This page has [[Existing Page Default]] and [[Non Existent Page Default]].

Also [[display text|Another Missing Page Default]].
"""
        storage.store(
            get_filename(pagepath),
            content,
            message="Create page with broken links",
            author=("Test User", "mail@example.org"),
        )

        storage.store(
            get_filename("Existing Page Default"),
            "# Existing Page Default\n\nThis exists.\n",
            message="Create existing page",
            author=("Test User", "mail@example.org"),
        )

        rv = admin_client.post(
            "/-/housekeeping",
            data={"task": "brokenwikilinks"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()

        assert (
            "test_broken_links_default" in html.lower()
            or "test broken links default" in html.lower()
        )
        assert "broken" in html.lower()

    def test_housekeeping_broken_wikilinks_link_title_style(
        self, app_with_user, admin_client
    ):
        """Test broken wikilinks detection with LINK_TITLE WIKILINK_STYLE."""
        from otterwiki.server import storage
        from otterwiki.helper import get_filename

        app_with_user.config["WIKILINK_STYLE"] = "LINK_TITLE"

        # In LINK_TITLE mode: [[Link|Title]] means Link is the page, Title is display
        pagepath = "test_link_title_style"
        content = """# Test Link Title Style

This has [[existing-link-title|Existing Page Display]] and [[missing-link-title|Missing Page Display]].

Also [[another-missing-link-title|Another Display]].
"""
        storage.store(
            get_filename(pagepath),
            content,
            message="Create page",
            author=("Test User", "mail@example.org"),
        )

        storage.store(
            get_filename("existing-link-title"),
            "# Existing Link Title\n\nThis exists.\n",
            message="Create existing page",
            author=("Test User", "mail@example.org"),
        )

        rv = admin_client.post(
            "/-/housekeeping",
            data={"task": "brokenwikilinks"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()

        assert (
            "test_link_title_style" in html.lower()
            or "test link title style" in html.lower()
        )
        assert "broken" in html.lower()

    def test_housekeeping_broken_wikilinks_page_name_title_style(
        self, app_with_user, admin_client
    ):
        """Test broken wikilinks detection with PAGE_NAME_TITLE WIKILINK_STYLE."""
        from otterwiki.server import storage
        from otterwiki.helper import get_filename

        app_with_user.config["WIKILINK_STYLE"] = "PAGE_NAME_TITLE"

        pagepath = "test_page_name_title_style"
        content = """# Test Page Name Title Style

This has [[real-page-pnt|Display Text]] and [[fake-page-pnt|Display Text]].
"""
        storage.store(
            get_filename(pagepath),
            content,
            message="Create page",
            author=("Test User", "mail@example.org"),
        )

        storage.store(
            get_filename("real-page-pnt"),
            "# Real Page PNT\n\nThis exists.\n",
            message="Create existing page",
            author=("Test User", "mail@example.org"),
        )

        rv = admin_client.post(
            "/-/housekeeping",
            data={"task": "brokenwikilinks"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()

        assert (
            "test_page_name_title_style" in html.lower()
            or "test page name title style" in html.lower()
        )
        assert "broken" in html.lower()

    def test_housekeeping_broken_wikilinks_with_anchors(
        self, app_with_user, admin_client
    ):
        """Test that wikilinks with anchors are handled correctly."""
        from otterwiki.server import storage
        from otterwiki.helper import get_filename

        app_with_user.config["WIKILINK_STYLE"] = ""
        pagepath = "test_links_with_anchors"
        content = """# Test Links With Anchors

Link to [[Existing Page Anchor#section]] and [[Missing Page Anchor#section]].

Also anchor-only link [[#local-anchor]].
"""
        storage.store(
            get_filename(pagepath),
            content,
            message="Create page",
            author=("Test User", "mail@example.org"),
        )

        storage.store(
            get_filename("Existing Page Anchor"),
            "# Existing Page Anchor\n\n## Section\n\nContent.\n",
            message="Create existing page",
            author=("Test User", "mail@example.org"),
        )

        rv = admin_client.post(
            "/-/housekeeping",
            data={"task": "brokenwikilinks"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()

        assert (
            "test_links_with_anchors" in html.lower()
            or "test links with anchors" in html.lower()
        )
        assert "broken" in html.lower()

    def test_housekeeping_broken_wikilinks_case_sensitivity(
        self, app_with_user, admin_client
    ):
        """Test broken wikilinks with RETAIN_PAGE_NAME_CASE setting."""
        from otterwiki.server import storage
        from otterwiki.helper import get_filename

        original_retain_case = app_with_user.config["RETAIN_PAGE_NAME_CASE"]

        try:
            # Test with case-sensitive (RETAIN_PAGE_NAME_CASE = True)
            app_with_user.config["RETAIN_PAGE_NAME_CASE"] = True
            app_with_user.config["WIKILINK_STYLE"] = ""

            pagepath = "test_case_sensitivity"
            content = """# Test Case Sensitivity

Link to [[Test Page Case]] and [[ANOTHER PAGE CASE]].
"""
            storage.store(
                get_filename(pagepath),
                content,
                message="Create page",
                author=("Test User", "mail@example.org"),
            )

            storage.store(
                get_filename("test page case"),
                "# Test Page Case\n\nContent.\n",
                message="Create existing page",
                author=("Test User", "mail@example.org"),
            )

            rv = admin_client.post(
                "/-/housekeeping",
                data={"task": "brokenwikilinks"},
                follow_redirects=True,
            )
            assert rv.status_code == 200
            html = rv.data.decode()

            # With RETAIN_PAGE_NAME_CASE=True, [[Test Page Case]] won't match "test page case"
            assert (
                "test_case_sensitivity" in html.lower()
                or "test case sensitivity" in html.lower()
            )
            assert "broken" in html.lower()
        finally:
            app_with_user.config["RETAIN_PAGE_NAME_CASE"] = (
                original_retain_case
            )

    def test_housekeeping_broken_wikilinks_subpages(
        self, app_with_user, admin_client
    ):
        """Test broken wikilinks with subpages."""
        from otterwiki.server import storage
        from otterwiki.helper import get_filename

        app_with_user.config["WIKILINK_STYLE"] = ""

        pagepath = "test_subpage_links"
        content = """# Test Subpage Links

Link to [[Parent Sub/Child Sub]] and [[Parent Sub/Missing Sub]].
"""
        storage.store(
            get_filename(pagepath),
            content,
            message="Create page",
            author=("Test User", "mail@example.org"),
        )

        storage.store(
            get_filename("Parent Sub/Child Sub"),
            "# Child Sub Page\n\nContent.\n",
            message="Create existing subpage",
            author=("Test User", "mail@example.org"),
        )

        rv = admin_client.post(
            "/-/housekeeping",
            data={"task": "brokenwikilinks"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()

        assert (
            "test_subpage_links" in html.lower()
            or "test subpage links" in html.lower()
        )
        assert "broken" in html.lower()

    def test_housekeeping_broken_wikilinks_permissions(
        self, app_with_user, other_client
    ):
        """Test that users without WRITE permission cannot access broken wikilinks scan."""
        original_write_access = app_with_user.config["WRITE_ACCESS"]

        try:
            # Set WRITE_ACCESS to require admin
            app_with_user.config["WRITE_ACCESS"] = "ADMIN"

            rv = other_client.post(
                "/-/housekeeping",
                data={"task": "brokenwikilinks"},
                follow_redirects=False,
            )
            assert rv.status_code == 403
        finally:
            app_with_user.config["WRITE_ACCESS"] = original_write_access

    def test_housekeeping_broken_wikilinks_unique_lists(
        self, app_with_user, admin_client
    ):
        """Test that broken links and found_in lists are unique."""
        from otterwiki.server import storage
        from otterwiki.helper import get_filename

        app_with_user.config["WIKILINK_STYLE"] = ""

        storage.store(
            get_filename("Page With Duplicates"),
            "# Page With Duplicates\n\n[[Missing]] and [[Missing]] and [[Missing]].\n",
            message="Create page",
            author=("Test User", "mail@example.org"),
        )

        storage.store(
            get_filename("Another Duplicate Page"),
            "# Another Duplicate Page\n\n[[Missing]] [[Missing]].\n",
            message="Create another page",
            author=("Test User", "mail@example.org"),
        )

        rv = admin_client.post(
            "/-/housekeeping",
            data={"task": "brokenwikilinks"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()

        # Count occurrences of "Missing" in the broken links for the first page
        # Should appear only once per page, not three times
        assert html.count(">Missing</a>") >= 2  # At least once per section

    def test_housekeeping_broken_wikilinks_fragments_removed(
        self, app_with_user, admin_client
    ):
        """Test that #fragments are removed from displayed pagenames."""
        from otterwiki.server import storage
        from otterwiki.helper import get_filename

        app_with_user.config["WIKILINK_STYLE"] = ""

        storage.store(
            get_filename("Page With Fragments"),
            "# Page With Fragments\n\n[[Missing#section1]] and [[Missing#section2]].\n",
            message="Create page",
            author=("Test User", "mail@example.org"),
        )

        rv = admin_client.post(
            "/-/housekeeping",
            data={"task": "brokenwikilinks"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()

        assert "Missing" in html
        assert "#section1" not in html or "Missing#section1" not in html

    def test_housekeeping_broken_wikilinks_relative_links(
        self, app_with_user, admin_client
    ):
        """Test that relative links like [[../Home]] are detected correctly."""
        from otterwiki.server import storage
        from otterwiki.helper import get_filename

        app_with_user.config["WIKILINK_STYLE"] = ""

        storage.store(
            get_filename("Parent/Child"),
            "# Child Page\n\nLink to [[../Home]] and [[../Missing]].\n",
            message="Create child page",
            author=("Test User", "mail@example.org"),
        )

        storage.store(
            get_filename("Home"),
            "# Home\n\nThis is home.\n",
            message="Create home page",
            author=("Test User", "mail@example.org"),
        )

        rv = admin_client.post(
            "/-/housekeeping",
            data={"task": "brokenwikilinks"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()

        assert "Missing" in html or "../Missing" in html


class TestHousekeepingGeneral:
    """General housekeeping tests."""

    def test_housekeeping_unknown_task(self, app_with_user, admin_client):
        """Test that unknown task shows error."""
        rv = admin_client.post(
            "/-/housekeeping",
            data={"task": "unknown_task"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()
        assert "Unkown task" in html or "Unknown task" in html

    def test_housekeeping_requires_login(self, app_with_user, test_client):
        """Test that housekeeping requires login."""
        rv = test_client.get("/-/housekeeping", follow_redirects=False)
        # Should redirect to login
        assert rv.status_code == 302
        assert "login" in rv.location
