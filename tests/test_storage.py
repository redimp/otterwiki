#!/usr/bin/env python

import tempfile
import unittest
from pprint import pprint

import otterwiki.storage

class TestStorage(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = '/tmp/xxx' # self.tempdir.name
        self.path = self.tempdir.name
        self.storage = otterwiki.storage.GitStorage(path=self.path, initialize=True)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_store_and_load(self):
        content = "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad\n"
        message = "Test commit"
        filename = "test.md"
        author = ("Example Author", "mail@example.com")
        self.assertTrue( self.storage.store(filename, content=content, author=author, message=message) )
        # check content
        self.assertEqual( self.storage.load(filename), content )
        # check metadata
        metadata = self.storage.metadata(filename)
        self.assertEqual( metadata['author_name'], author[0] )
        self.assertEqual( metadata['author_email'], author[1] )
        self.assertEqual( metadata['message'], message )
        # check if file is listed
        self.assertIn( filename, self.storage.list_files() )
        # check if storing the same content changes nothing
        self.assertFalse( self.storage.store(filename, content=content, author=author) )

    def test_load_fail(self):
        with self.assertRaises(otterwiki.storage.StorageNotFound):
            self.storage.load("non-existent.md")
        with self.assertRaises(otterwiki.storage.StorageNotFound):
            self.storage.metadata("non-existent.md")
        with self.assertRaises(otterwiki.storage.StorageNotFound):
            self.storage.metadata("non-existent.md", revision="xxx")
        with self.assertRaises(otterwiki.storage.StorageNotFound):
            self.storage.log("non-existent.md")

    def test_broken_author(self):
        content = "This is test content.\n"
        message = "Test commit"
        filename = "test_broken_author.md"
        author = ("Example Author", "")
        self.assertTrue( self.storage.store(filename, content=content, author=author, message=message) )
        metadata = self.storage.metadata(filename)
        self.assertEqual( metadata['author_name'], author[0] )

    def test_broken_message(self):
        content = "This is test content.\n"
        message = None
        filename = "test_broken_message.md"
        author = ("Example Author", "mail@example.org")
        self.assertTrue( self.storage.store(filename, content=content, author=author, message=message) )
        metadata = self.storage.metadata(filename)
        self.assertEqual( metadata['message'], '' )

    def test_log(self):
        content = "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad\n"
        message = "Test commit"
        filename = "test_log.md"
        author = ("Example Author", "mail@example.com")
        self.assertTrue( self.storage.store(filename, content=content, author=author, message=message) )
        # test log for filename
        log = self.storage.log(filename)
        msg = log[-1]
        self.assertEqual(msg['message'], message)
        # test global log
        log = self.storage.log()
        msg = log[-1]
        self.assertEqual(msg['message'], message)

    def test_revert(self):
        author = ("Example Author", "mail@example.com")
        filename = "test_revert.md"
        content1 = "aaa"
        message1 = "added {}".format(content1)
        content2 = "bbb"
        message2 = "added {}".format(content2)
        self.assertTrue( self.storage.store(filename, content=content1, author=author, message=message1) )
        # check content
        self.assertEqual( self.storage.load(filename), content1 )
        # change content
        self.assertTrue( self.storage.store(filename, content=content2, author=author, message=message2) )
        # check content
        self.assertEqual( self.storage.load(filename), content2 )
        # get revision
        log = self.storage.log(filename)
        revision = log[0]['revision']
        self.storage.revert(revision, message="reverted {}".format(revision), author=author)
        # check that the file is in the old state
        self.assertEqual( self.storage.load(filename), content1 )

    def test_revert_fail(self):
        author = ("Example Author", "mail@example.com")
        filename = "test_revert_fail.md"
        content1 = "aaa"
        message1 = "added {}".format(content1)
        self.assertTrue( self.storage.store(filename, content=content1, author=author, message=message1) )
        # get revision
        log = self.storage.log(filename)
        revision = log[0]['revision']
        # revert
        self.storage.revert(revision, message="reverted {}".format(revision), author=author)
        files = self.storage.list_files()
        self.assertNotIn(filename, files)

    def test_ascii_binary(self):
        content = u"kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad"
        message = "Test commit"
        filename = "test_binary.md"
        author = ("Example Author", "mail@example.com")
        self.assertTrue( self.storage.store(filename, content=content, author=author, message=message) )
        content_rb = self.storage.load(filename, mode="rb")
        content_r = self.storage.load(filename, mode="r")
        # check types
        self.assertIs(type(content_rb), bytes)
        self.assertIs(type(content_r), str)
        # convert into str
        content_utf8 = content_rb.decode("utf-8")
        self.assertIs(type(content_utf8), str)
        self.assertEqual(content_utf8, content_r)

    def test_binary(self):
        content = b"GIF89a\x01\x00\x01\x00\x80\x01\x00\xff\xff"\
                  b"\xff\x00\x00\x00!\xf9\x04\x01\n\x00\x01\x00,"\
                  b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;"
        message = "Test commit"
        filename = "test_binary.gif"
        author = ("Example Author", "mail@example.com")
        self.assertTrue( self.storage.store(filename, content=content, author=author, message=message, mode='wb') )
        content_rb = self.storage.load(filename, mode="rb")
        self.assertEqual(content, content_rb)
        # get log
        log = self.storage.log()
        # get revisions
        revision = log[0]['revision']
        content_rb2 = self.storage.load(filename, mode="rb", revision=revision)
        self.assertEqual(content_rb2, content_rb)


    def test_revision(self):
        content = "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad"
        message = "Test commit"
        filename = "test_revision.md"
        author = ("Example Author", "mail@example.com")
        self.assertTrue( self.storage.store(filename, content=content, author=author, message=message) )
        metadata = self.storage.metadata(filename)
        revision = metadata['revision-full']
        self.assertEqual( self.storage.load(filename, revision=revision), content )
        metadata2 = self.storage.metadata(filename, revision=revision)
        self.assertEqual( metadata, metadata2)
        # check broken revision
        revision3 = "xxx{}".format(revision)
        with self.assertRaises(otterwiki.storage.StorageNotFound):
            self.storage.metadata(filename, revision=revision3)
        with self.assertRaises(otterwiki.storage.StorageNotFound):
            self.storage.load(filename, revision=revision3)

    def test_store_subdir(self):
        content = "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad\n"
        message = "Test commit"
        filename = "test_subdir/test_subdir.md"
        author = ("Example Author", "mail@example.com")
        self.assertTrue( self.storage.store(filename, content=content, author=author, message=message) )
        # check if file exists
        self.assertTrue( self.storage.exists(filename) )
        # check via file list
        files = self.storage.list_files()
        self.assertIn(filename, files)
        dn, fn = filename.split('/')
        files = self.storage.list_files(dn)
        self.assertIn(fn, files)

    def test_diff(self):
        author = ("Example Author", "mail@example.com")
        filename = "test_revert.md"
        content1 = "aaa"
        message1 = "added {}".format(content1)
        content2 = "bbb"
        message2 = "added {}".format(content2)
        self.assertTrue( self.storage.store(filename, content=content1, author=author, message=message1) )
        # check content
        self.assertEqual( self.storage.load(filename), content1 )
        # change content
        self.assertTrue( self.storage.store(filename, content=content2, author=author, message=message2) )
        # check content
        self.assertEqual( self.storage.load(filename), content2 )
        # get log
        log = self.storage.log()
        # get revisions
        rev_b, rev_a= log[0]['revision'], log[1]['revision']
        # get diff
        diff = self.storage.diff(filename, rev_a, rev_b)
        # check -/+ strings
        self.assertIn("-aaa", diff)
        self.assertIn("+bbb", diff)

    def test_rename(self):
        content = "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad\n"
        message = "Test commit"
        filename1 = "test_rename1.md"
        filename2 = "test_rename2.md"
        author = ("Example Author", "mail@example.com")
        self.assertTrue( self.storage.store(filename1, content=content, author=author, message=message) )
        # rename
        self.storage.rename( filename1, filename2, author=author )
        # check if file exists
        self.assertFalse( self.storage.exists(filename1) )
        self.assertTrue( self.storage.exists(filename2) )
        # check if file exists via list_files
        files = self.storage.list_files()
        self.assertNotIn(filename1, files)
        self.assertIn(filename2, files)
        # check content
        self.assertEqual( self.storage.load(filename2), content )
        # test rename fail
        with self.assertRaises(otterwiki.storage.StorageError):
            self.storage.rename( filename1, "", author=author )

    def test_delete(self):
        content = "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad"
        message = "Test commit"
        filename = "test_revision.md"
        author = ("Example Author", "mail@example.com")
        self.assertTrue( self.storage.store(filename, content=content, author=author, message=message) )
        # check if file exists
        files = self.storage.list_files()
        self.assertIn(filename, files)
        # remove file
        self.storage.delete(filename, author=author)
        # check that file doesn't exist anymore
        files = self.storage.list_files()
        self.assertNotIn(filename, files)


class TestEmptyStorage(unittest.TestCase):

    def test_log(self):
        with tempfile.TemporaryDirectory() as path:
            storage = otterwiki.storage.GitStorage(path=path, initialize=True)
            self.assertEqual(storage.log(), [])

    def test_load_fail(self):
        with tempfile.TemporaryDirectory() as path:
            storage = otterwiki.storage.GitStorage(path=path, initialize=True)
            with self.assertRaises(otterwiki.storage.StorageNotFound):
                storage.load("non-existent.md")
            with self.assertRaises(otterwiki.storage.StorageNotFound):
                storage.log("non-existent.md")

    def test_init_fail(self):
        with tempfile.TemporaryDirectory() as path:
            with self.assertRaises(otterwiki.storage.StorageError):
                storage = otterwiki.storage.GitStorage(path=path)

if __name__ == '__main__':
    unittest.main()
