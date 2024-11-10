#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import pytest
import tempfile
from pprint import pprint

from otterwiki import gitstorage


@pytest.fixture
def storage(tmpdir):
    storage = gitstorage.GitStorage(path=str(tmpdir), initialize=True)
    yield storage


def test_store_and_load(storage):
    content = "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad\n"
    message = "Test commit"
    filename = "test.md"
    author = ("Example Author", "mail@example.com")
    assert True == storage.store(
        filename, content=content, author=author, message=message
    )
    # check content
    assert storage.load(filename) == content
    # check metadata
    metadata = storage.metadata(filename)
    assert metadata["author_name"] == author[0]
    assert metadata["author_email"] == author[1]
    assert metadata["message"] == message
    # check if file is listed
    assert filename, _ in storage.list()
    # check if storing the same content changes nothing
    assert False == storage.store(filename, content=content, author=author)


def test_load_fail(storage):
    with pytest.raises(gitstorage.StorageNotFound):
        storage.load("non-existent.md")
    with pytest.raises(gitstorage.StorageNotFound):
        storage.metadata("non-existent.md")
    with pytest.raises(gitstorage.StorageNotFound):
        storage.metadata("non-existent.md", revision="xxx")
    with pytest.raises(gitstorage.StorageNotFound):
        storage.log("non-existent.md")


def test_broken_author(storage):
    content = "This is test content.\n"
    message = "Test commit"
    filename = "test_broken_author.md"
    author = ("Example Author", "")
    assert True == storage.store(
        filename, content=content, author=author, message=message
    )
    metadata = storage.metadata(filename)
    assert metadata["author_name"] == author[0]


def test_broken_message(storage):
    content = "This is test content.\n"
    message = None
    filename = "test_broken_message.md"
    author = ("Example Author", "mail@example.org")
    assert True == storage.store(
        filename, content=content, author=author, message=message
    )
    metadata = storage.metadata(filename)
    assert metadata["message"] == ""


def test_log_empty(storage):
    assert [] == storage.log(fail_on_git_error=False)
    with pytest.raises(gitstorage.StorageNotFound):
        log = storage.log(fail_on_git_error=True)


def test_log(storage):
    content = "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad\n"
    message = "Test commit"
    filename = "test_log.md"
    author = ("Example Author", "mail@example.com")
    assert True == storage.store(
        filename, content=content, author=author, message=message
    )
    # test log for filename
    log = storage.log(filename)
    msg = log[-1]
    assert msg["message"] == message
    # test global log
    log = storage.log()
    msg = log[-1]
    assert msg["message"] == message


def test_revert(storage):
    author = ("Example Author", "mail@example.com")
    filename = "test_revert.md"
    content1 = "aaa"
    message1 = "added {}".format(content1)
    content2 = "bbb"
    message2 = "added {}".format(content2)
    assert True == storage.store(
        filename, content=content1, author=author, message=message1
    )
    # check content
    assert storage.load(filename) == content1
    # change content
    assert True == storage.store(
        filename, content=content2, author=author, message=message2
    )
    # check content
    assert storage.load(filename) == content2
    # get revision
    log = storage.log(filename)
    revision = log[0]["revision"]
    storage.revert(
        revision, message="reverted {}".format(revision), author=author
    )
    # check that the file is in the old state
    assert storage.load(filename) == content1


def test_revert_fail(storage):
    author = ("Example Author", "mail@example.com")
    filename = "test_revert_fail.md"
    content1 = "aaa"
    message1 = "added {}".format(content1)
    assert True == storage.store(
        filename, content=content1, author=author, message=message1
    )
    # file found?
    files, _ = storage.list()
    assert filename in files
    # get revision
    log = storage.log(filename)
    revision = log[0]["revision"]
    # revert
    storage.revert(
        revision, message="reverted {}".format(revision), author=author
    )
    files, _ = storage.list()
    assert filename not in files


def test_ascii_binary(storage):
    content = "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad"
    message = "Test commit"
    filename = "test_binary.md"
    author = ("Example Author", "mail@example.com")
    assert True == storage.store(
        filename, content=content, author=author, message=message
    )
    content_rb = storage.load(filename, mode="rb")
    content_r = storage.load(filename, mode="r")
    # check types
    assert type(content_rb) is bytes
    assert type(content_r) is str
    # convert into str
    content_utf8 = content_rb.decode("utf-8")
    assert type(content_utf8) is str
    assert content_utf8 == content_r


def test_binary(storage):
    content = (
        b"GIF89a\x01\x00\x01\x00\x80\x01\x00\xff\xff"
        b"\xff\x00\x00\x00!\xf9\x04\x01\n\x00\x01\x00,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;"
    )
    message = "Test commit"
    filename = "test_binary.gif"
    author = ("Example Author", "mail@example.com")
    assert True == storage.store(
        filename, content=content, author=author, message=message, mode="wb"
    )
    content_rb = storage.load(filename, mode="rb")
    assert content == content_rb
    # get log
    log = storage.log()
    # get revisions
    revision = log[0]["revision"]
    content_rb2 = storage.load(filename, mode="rb", revision=revision)
    assert content_rb2 == content_rb


def test_revision(storage):
    content = ["aaa", "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad"]
    message = "Test commit"
    filename = "test_revision.md"
    author = ("Example Author", "mail@example.com")
    assert True == storage.store(
        filename, content=content[0], author=author, message=message
    )
    metadata = storage.metadata(filename)
    revision = metadata["revision-full"]
    assert storage.load(filename, revision=revision) == content[0]
    metadata2 = storage.metadata(filename, revision=revision)
    assert metadata == metadata2
    # check broken revision
    revision3 = "xxx{}".format(revision)
    with pytest.raises(gitstorage.StorageNotFound):
        storage.metadata(filename, revision=revision3)
    with pytest.raises(gitstorage.StorageNotFound):
        storage.load(filename, revision=revision3)
    # add commit
    assert True == storage.store(
        filename, content=content[1], author=author, message=message
    )
    # fetch last commit
    assert storage.load(filename) == content[1]
    # fetch first commit
    assert storage.load(filename, revision=revision) == content[0]


def test_store_subdir(storage):
    content = "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad\n"
    message = "Test commit"
    subdir = "test_subdir"
    filename = os.path.join(subdir, "test_subdir.md")
    author = ("Example Author", "mail@example.com")
    assert True == storage.store(
        filename, content=content, author=author, message=message
    )
    # check if file exists
    assert True == storage.exists(filename)
    # check if file is not a directory
    assert False == storage.isdir(filename)
    # check if the subdir is a directory
    assert True == storage.isdir(subdir)
    # check via file list
    files, directories = storage.list()
    assert filename in files
    assert "test_subdir" in directories


def test_list(storage):
    msg, content = "Test commit", "Lore ipsum"
    author = ("Example Author", "mail@example.com")
    all_files = ["a", "b/c", "d/e/f"]
    for f in all_files:
        assert True == storage.store(
            f, content=content, author=author, message=msg
        )
    files, directories = storage.list()
    # check that all files are there
    assert files == all_files
    # check that all files are there
    assert files == all_files
    # check if depth=1 works
    files, directories = storage.list(depth=0)
    assert files == ["a"]
    # check if depth=1 works
    files, directories = storage.list(depth=1)
    assert files == ["a", "b/c"]
    # check if depth=2 works
    files, directories = storage.list(depth=2)
    assert files == ["a", "b/c", "d/e/f"]
    # check for given path /b
    files, directories = storage.list("b")
    # check that all files are there
    assert files == ["c"]
    # check if abspath raises an Exception
    with pytest.raises(ValueError) as e_info:
        # check for given path /
        files, directories = storage.list("/")


def test_list_path(storage):
    msg, content = "Test commit", "Lore ipsum"
    author = ("Example Author", "mail@example.com")
    all_files = ["a", "b/c", "b/d"]
    for f in all_files:
        assert True == storage.store(
            f, content=content, author=author, message=msg
        )
    files, directories = storage.list()
    assert files == ["a", "b/c", "b/d"]
    # check if depth=2 works
    files, directories = storage.list(depth=2)
    assert files == ["a", "b/c", "b/d"]
    # check if path works
    files, directories = storage.list("b")
    assert files == ["c", "d"]
    # check if path works
    files, directories = storage.list("b", depth=1)
    assert files == ["c", "d"]


def test_diff(storage):
    author = ("Example Author", "mail@example.com")
    filename = "test_revert.md"
    content1 = "aaa"
    message1 = "added {}".format(content1)
    content2 = "bbb"
    message2 = "added {}".format(content2)
    assert True == storage.store(
        filename, content=content1, author=author, message=message1
    )
    # check content
    assert storage.load(filename) == content1
    # change content
    assert True == storage.store(
        filename, content=content2, author=author, message=message2
    )
    # check content
    assert storage.load(filename) == content2
    # get log
    log = storage.log()
    # get revisions
    rev_b, rev_a = log[0]["revision"], log[1]["revision"]
    # get diff
    diff = storage.diff(rev_a, rev_b)
    # check -/+ strings
    assert "-aaa" in diff
    assert "+bbb" in diff


def test_rename(storage):
    content = "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad\n"
    message = "Test commit"
    filename1 = "test_rename1.md"
    filename2 = "test_rename2.md"
    author = ("Example Author", "mail@example.com")
    assert True == storage.store(
        filename1, content=content, author=author, message=message
    )
    # rename
    storage.rename(filename1, filename2, author=author)
    # check if file exists
    assert False == storage.exists(filename1)
    assert True == storage.exists(filename2)
    # check if file exists via list
    files, _ = storage.list()
    assert filename1 not in files
    assert filename2 in files
    # check content
    assert storage.load(filename2) == content
    # test rename fail
    with pytest.raises(gitstorage.StorageError):
        storage.rename(filename1, "", author=author)


def test_delete(storage):
    content = "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad"
    message = "Test commit"
    filename = "test_revision.md"
    author = ("Example Author", "mail@example.com")
    assert True == storage.store(
        filename, content=content, author=author, message=message
    )
    # check if file exists
    files, _ = storage.list()
    assert filename in files
    # remove file
    storage.delete(filename, author=author)
    # check that file doesn't exist anymore
    files, _ = storage.list()
    assert filename not in files


def test_empty_log():
    with tempfile.TemporaryDirectory() as path:
        storage = gitstorage.GitStorage(path=path, initialize=True)
        assert storage.log() == []


def test_load_fail():
    with tempfile.TemporaryDirectory() as path:
        storage = gitstorage.GitStorage(path=path, initialize=True)
        with pytest.raises(gitstorage.StorageNotFound):
            storage.load("non-existent.md")
        with pytest.raises(gitstorage.StorageNotFound):
            storage.log("non-existent.md")


def test_init_fail():
    with tempfile.TemporaryDirectory() as path:
        with pytest.raises(gitstorage.StorageError):
            storage = gitstorage.GitStorage(path=path)


def test_show_commit_error(storage):
    with pytest.raises(gitstorage.StorageError):
        storage.show_commit("xxx")


def test_show_commit(storage):
    author = ("Example Author", "mail@example.com")
    filename = "test_show_commit.md"
    content1 = "aaa\n"
    message1 = "added {}".format(content1)
    content2 = "bbb\n"
    message2 = "added {}".format(content2)
    assert True == storage.store(
        filename, content=content1, author=author, message=message1
    )
    # check content
    assert storage.load(filename) == content1
    # change content
    assert True == storage.store(
        filename, content=content2, author=author, message=message2
    )
    # check content
    assert storage.load(filename) == content2
    # get log
    log = storage.log()
    # get revisions
    rev_b, rev_a = log[0]["revision"], log[1]["revision"]
    # show commit
    metadata, diff = storage.show_commit(rev_b)
    assert metadata['revision'] == rev_b
    assert "--- a/test_show_commit.md" in diff
    assert "+++ b/test_show_commit.md" in diff
    assert "\n-aaa" in diff
    assert "\n+bbb" in diff


def test_get_parent_revision(storage):
    content = "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad\n"
    filename1 = "test_parentrevision1.md"
    filename2 = "test_parentrevision_random.md"
    filename1a = "test_parentrevision2.md"
    # commit the first file, the one that will be renamed
    author = ("Example Author", "mail@example.com")
    assert True == storage.store(
        filename1, content=content, author=author, message="operation 1"
    )
    # commit another file
    assert True == storage.store(
        filename2, content=content, author=author, message="operation 2"
    )
    # rename
    storage.rename(filename1, filename1a, author=author, message="operation 3")
    # fetch the log
    log = storage.log()
    # get the revision of the commits matching the operations we did
    revision1 = [x['revision'] for x in log if x['message'] == "operation 1"][
        0
    ]
    revision3 = [x['revision'] for x in log if x['message'] == "operation 3"][
        0
    ]
    # now we check the parent revision of the renamed file, with the revison of the
    # commit that did the renaming as child
    parent_revision = storage.get_parent_revision(
        filename=filename1, revision=revision3
    )
    assert parent_revision == revision1


