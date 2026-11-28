# vim: set et ts=8 sts=4 sw=4 ai:

import os


def test_pageindex_with_invalid_utf8(create_app, req_ctx):
    """Page index renders valid pages even when one file has invalid UTF-8."""
    storage = create_app.storage

    # create valid pages
    storage.store(
        "ValidPage.md",
        "# Valid Page\n\nSome content.",
        author=("Test", "test@example.org"),
    )
    storage.store(
        "AnotherPage.md",
        "# Another Page\n\nMore content.",
        author=("Test", "test@example.org"),
    )

    # write a file with invalid UTF-8 bytes directly to the repo
    broken_path = os.path.join(storage.path, "BrokenPage.md")
    with open(broken_path, "wb") as f:
        f.write(b"# Broken\n\xff\xfe invalid utf8 sequence")
    # add and commit so it shows up in storage.list()
    storage.commit(
        ["BrokenPage.md"],
        message="add broken page",
        author=("Test", "test@example.org"),
    )

    from otterwiki.pageindex import PageIndex

    page_index = PageIndex()

    # collect all page titles from the index
    titles = [title for title, _, _ in page_index.pages()]

    assert "Validpage" in titles
    assert "Anotherpage" in titles
    # the broken page should still appear (by filename-derived name),
    # it just won't have a parsed TOC
    assert "BrokenPage" in titles


def test_pageindex_natural_sort(create_app, req_ctx):
    from otterwiki.pageindex import PageIndex

    storage = create_app.storage
    for n in [1, 2, 9, 10, 11]:
        storage.store(
            f"stages/stage {n}.md",
            f"# Stage {n}\n\nContent.",
            author=("Test", "test@example.org"),
        )

    def titles():
        return [title for title, _, _ in PageIndex("stages").pages()]

    create_app.config["SIDEBAR_MENUTREE_NATURAL_SORT"] = False
    assert titles() == [
        "Stage 1",
        "Stage 10",
        "Stage 11",
        "Stage 2",
        "Stage 9",
    ]

    create_app.config["SIDEBAR_MENUTREE_NATURAL_SORT"] = True
    try:
        assert titles() == [
            "Stage 1",
            "Stage 2",
            "Stage 9",
            "Stage 10",
            "Stage 11",
        ]
    finally:
        create_app.config["SIDEBAR_MENUTREE_NATURAL_SORT"] = False
