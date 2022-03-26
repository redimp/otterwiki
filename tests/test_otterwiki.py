#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import re
import pytest
import otterwiki
import otterwiki.util
import otterwiki.gitstorage

from pprint import pprint


@pytest.fixture
def create_app(tmpdir):
    tmpdir.mkdir("repo")
    storage = otterwiki.gitstorage.GitStorage(
        path=str(tmpdir.join("repo")), initialize=True
    )
    settings_cfg = str(tmpdir.join("settings.cfg"))
    # write config file
    with open(settings_cfg, "w") as f:
        f.writelines(
            [
                "REPOSITORY = '{}'\n".format(str(tmpdir.join("repo"))),
                "SITE_NAME = 'TEST WIKI'\n",
            ]
        )
    # configure environment
    os.environ["OTTERWIKI_SETTINGS"] = settings_cfg
    # get app
    from otterwiki.server import app

    # configure permissions
    app.config["READ_ACCESS"] = "ANONYMOUS"
    app.config["WRITE_ACCESS"] = "ANONYMOUS"
    app.config["ATTACHMENT_ACCESS"] = "ANONYMOUS"
    # enable test and debug settings
    app.config["TESTING"] = True
    app.config["DEBUG"] = True
    # for debugging
    app._otterwiki_tempdir = storage.path
    # for other tests
    app.storage = storage
    yield app


@pytest.fixture
def test_client(create_app):
    yield create_app.test_client()


@pytest.fixture
def req_ctx(create_app):
    with create_app.test_request_context() as ctx:
        yield ctx


def test_html(test_client):
    result = test_client.get("/")
    assert "<!DOCTYPE html>" in result.data.decode()
    assert "<title>" in result.data.decode()
    assert "</html>" in result.data.decode()


def test_create_form(test_client):
    result = test_client.get("/-/create")
    html = result.data.decode()
    assert "Create Page</h2>" in html
    assert '<form action="/-/create" method="POST"' in html


def test_create_page_sanitized(test_client):
    pagename = "CreateTest?"
    html = test_client.post(
        "/-/create",
        data={
            "pagename": pagename,
        },
        follow_redirects=True,
    ).data.decode()
    assert "Please check the pagename" in html


def test_create_page(test_client):
    pagename = "CreateTest"
    html = test_client.post(
        "/-/create",
        data={
            "pagename": pagename,
        },
        follow_redirects=True,
    ).data.decode()
    # check form
    assert 'action="/{}/preview"'.format(pagename) in html
    assert "<textarea" in html
    assert 'name="content_editor"' in html
    # test save
    html = test_client.post(
        "/{}/save".format(pagename),
        data={
            "content_update": "Test test 12345678\n\n**strong**",
            "commit": "Initial commit",
        },
        follow_redirects=True,
    ).data.decode()
    assert "Test test 12345678" in html
    assert "<title>{}".format(pagename) in html
    assert "<p><strong>strong</strong></p>" in html
    # check exisiting page
    html = test_client.post(
        "/-/create",
        data={
            "pagename": pagename,
        },
        follow_redirects=True,
    ).data.decode()
    assert "exists already" in html


def save_shortcut(test_client, pagename, content, commit_message):
    rv = test_client.post(
        "/{}/save".format(pagename),
        data={
            "content_update": content,
            "commit": commit_message,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200


def test_page_save(test_client):
    from otterwiki.server import storage

    pagename = "Save Test"
    content = "*em*\n\n**strong**\n"
    commit_message = "Save test commit message"
    save_shortcut(test_client, pagename, content, commit_message)
    # check file content
    assert content == storage.load("{}.md".format(pagename.lower()))
    # check history
    html = test_client.get("/{}/history".format(pagename)).data.decode()
    assert "History" in html
    assert commit_message in html


def test_blame_and_history_and_diff(test_client):
    pagename = "Blame Test"
    content = "Blame Test\naaa_aaa_aaa"
    commit_messages = ["initial commit", "update"]
    save_shortcut(test_client, pagename, content, commit_messages[0])
    # check history
    html = test_client.get("/{}/history".format(pagename)).data.decode()
    assert commit_messages[0] in html
    # check blame
    html = test_client.get("/{}/blame".format(pagename)).data.decode()
    for line in content.splitlines():
        assert line in html
    # update content
    content = "Blame Test\nbbb\nccc\nddd"
    save_shortcut(test_client, pagename, content, commit_messages[1])
    # check history
    html = test_client.get("/{}/history".format(pagename)).data.decode()
    # find revision
    revision = re.findall(r"class=\"btn revision-small\">([A-z0-9]+)</a>", html)
    assert len(revision) == 2
    for line in commit_messages:
        assert line in html
    # check blame
    html = test_client.get("/{}/blame".format(pagename)).data.decode()
    for line in content.splitlines():
        assert line in html
    assert "aaa_aaa_aaa" not in html
    # fetch diff
    rv = test_client.post(
        "/{}/history".format(pagename),
        data={"rev_a": revision[1], "rev_b": revision[0]},
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert pagename in html
    assert revision[0] in html
    assert revision[1] in html


def test_blame_and_history_404(test_client):
    pagename = "Doe's not exist"
    # check blame
    rv = test_client.get("/{}/blame".format(pagename), follow_redirects=True)
    assert "Page not found" in rv.data.decode()
    assert rv.status_code == 404
    # check history
    rv = test_client.get("/{}/history".format(pagename), follow_redirects=True)
    assert "Page not found" in rv.data.decode()
    assert rv.status_code == 404


def test_search(test_client):
    # create additional haystacks
    save_shortcut(test_client, "HayStack 0", "Needle 0", "initial commit")
    save_shortcut(test_client, "HayStack 1", "Needle 1", "initial commit")
    save_shortcut(test_client, "Haystack 1a", "NeEdle 1", "initial commit")
    save_shortcut(test_client, "Haystack 2", "NeEdle 2\nNeEdle 2", "initial commit")
    # search 1
    rv = test_client.get("/-/search/{}".format("Haystack"))
    assert "Search matched 4 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search 2
    rv = test_client.get("/-/search/{}".format("Needle"))
    assert "Search matched 4 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search 3
    rv = test_client.get("/-/search/{}".format("Needle 1"))
    assert "Search matched 2 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search 4
    rv = test_client.get("/-/search/{}".format("Haystack 1"))
    assert "Search matched 2 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search via post 1
    rv = test_client.post("/-/search", data={"query": "Haystack"})
    assert "Search matched 4 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search via post 2: case sensitive
    rv = test_client.post(
        "/-/search", data={"query": "HayStack", "is_casesensitive": "y"}
    )
    assert "Search matched 4 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search via post 3: case sensitive
    rv = test_client.post(
        "/-/search", data={"query": "NeEdle", "is_casesensitive": "y"}
    )
    assert "Search matched 2 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search via post 4: regex
    rv = test_client.post(
        "/-/search", data={"query": "NeEdle", "is_regexp": "y", "is_casesensitive": "y"}
    )
    assert "Search matched 2 pages" in rv.data.decode()
    assert rv.status_code == 200
    # search via post 4: regex
    rv = test_client.post("/-/search", data={"query": "N[eE]+dle", "is_regexp": "y"})
    assert "Search matched 4 pages" in rv.data.decode()
    assert rv.status_code == 200


def test_rename(test_client):
    old_pagename = "RenameTest"
    new_pagename = "RenameTestNew"
    content = "# Rename content\nabc abc abc def def def."
    # create page
    save_shortcut(
        test_client,
        pagename=old_pagename,
        content=content,
        commit_message="initial commit",
    )
    # check content
    rv = test_client.get("/{}/view".format(old_pagename))
    assert rv.status_code == 200
    # check new page doesn't exist
    rv = test_client.get("/{}/view".format(new_pagename))
    assert rv.status_code == 404
    # rename form
    rv = test_client.get("/{}/rename".format(old_pagename))
    assert (
        'form action="/{}/rename" method="POST"'.format(old_pagename)
        in rv.data.decode()
    )
    assert rv.status_code == 200
    # rename page
    rv = test_client.post(
        "/{}/rename".format(old_pagename),
        data={"new_pagename": new_pagename, "message": ""},
        follow_redirects=True,
    )
    # check old page doesn't exist
    rv = test_client.get("/{}/view".format(old_pagename))
    assert rv.status_code == 404
    # check new page exists
    rv = test_client.get("/{}/view".format(new_pagename))
    assert rv.status_code == 200


def test_delete(test_client):
    pagename = "DeleteTest"
    content = "# Delete content\nabc abc abc def def def."
    # create page
    save_shortcut(
        test_client, pagename=pagename, content=content, commit_message="initial commit"
    )
    # check content
    rv = test_client.get("/{}/view".format(pagename))
    assert rv.status_code == 200
    # delete form
    rv = test_client.get("/{}/delete".format(pagename))
    assert rv.status_code == 200
    assert 'form action="/{}/delete" method="POST"'.format(pagename) in rv.data.decode()
    # delete page
    rv = test_client.post(
        "/{}/delete".format(pagename),
        data={"message": "deleted ..."},
        follow_redirects=True,
    )
    assert rv.status_code == 200
    # check deletion
    rv = test_client.get("/{}/view".format(pagename))
    assert rv.status_code == 404


# class TestViews(unittest.TestCase):
#     def setUp(self):
#         self.app = otterwiki.app
#         self.app.config['SERVER_NAME'] = 'localhost.localdomain'
#         self.test_client = self.app.test_client()
#
#         self.tempdir = tempfile.TemporaryDirectory()
#         self.path = self.tempdir.name
#         # create storage
#         self.storage = otterwiki.storage.GitStorage(path=self.path, initialize=True)
#         # update storage in the otterwiki
#         otterwiki.storage.storage = self.storage
#         otterwiki.views.storage = self.storage
#         otterwiki.formatter.storage = self.storage
#
#     def tearDown(self):
#         self.tempdir.cleanup()
#
#     def test_about(self):
#         result = self.test_client.get('/wiki/about')
#         self.assertEqual(200, result.status_code)
#         self.assertIn('About an Otter Wiki',result.data.decode())
#
#     def test_home(self):
#         result = self.test_client.get('/')
#         # check title
#         self.assertIn('<title> 404',result.data.decode())
#         # check header
#         self.assertIn('<h1>404</h1>',result.data.decode())
#         # check for error text
#         self.assertIn('Page Home not found',result.data.decode())
#         # check if create link exists
#         self.assertIn('/wiki/create/Home',result.data.decode())
#         # create /Home
#         content="# Home\nTesting the wiki homepage."
#         author = ("Example Author", "mail@example.com")
#         self.assertTrue( self.storage.store("home.md",
#             content=content,
#             author=author,
#             message="added Home") )
#         result = self.test_client.get('/')
#         # check header
#         self.assertIn('<h1>Home</h1>',result.data.decode())
#         # check text
#         self.assertIn('<p>Testing the wiki homepage.</p>',result.data.decode())
#
#     def test_not_found(self):
#         result = self.test_client.get('/NotFound')
#         # check title
#         self.assertIn('<title> 404',result.data.decode())
#         # check header
#         self.assertIn('<h1>404</h1>',result.data.decode())
#         # check for error text
#         self.assertIn('Page NotFound not found',result.data.decode())
#         # check if create link exists
#         self.assertIn('/wiki/create/NotFound',result.data.decode())
#
#     def test_save(self):
#         result = self.test_client.post(
#             '/TestSave/save',
#             data=dict(content="# Test Save\nTestSave test content.", message=""),
#             follow_redirects=True,
#             )
#         # check text
#         self.assertIn('<p>TestSave test content.</p>',result.data.decode())
#
#     def test_create(self):
#         result = self.test_client.get('/wiki/create')
#         # check header
#         self.assertIn('<h1>Create Page</h1>',result.data.decode())
#         # check text
#         self.assertIn('action="/wiki/create"',result.data.decode())
#
#     def test_create2(self):
#         result = self.test_client.get('/wiki/create/CreateTest')
#         # check header
#         self.assertIn('<h1>Create Page</h1>',result.data.decode())
#         # check text
#         self.assertIn('action="/wiki/create"',result.data.decode())
#         # check post
#         result = self.test_client.post(
#             '/wiki/create',
#             data=dict(pagename="CreateTest"),
#             follow_redirects=True,
#             )
#         self.assertIn('action="/CreateTest/save"',result.data.decode())
#         self.assertIn('<textarea name="content"',result.data.decode())
#         # create page
#         result = self.test_client.post(
#             '/CreateTest/save',
#             data=dict(content="# Create Test\nCreate Test content.", message=""),
#             follow_redirects=True,
#             )
#         # check existing page
#         result = self.test_client.post(
#             '/wiki/create',
#             data=dict(pagename="CreateTest"),
#             follow_redirects=True,
#             )
#         self.assertIn('Page CreateTest exists already.',result.data.decode())
#
#     def test_edit(self):
#         result = self.test_client.post(
#             '/TestEdit/save',
#             data=dict(content="# Test Edit\nTestEdit test content.", message=""),
#             follow_redirects=True,
#             )
#         # check header
#         self.assertIn('<h1 id="toc-0"><a id="test-edit" href="#test-edit">Test Edit<span class="anchor">&nbsp;</span></a></h1>',result.data.decode())
#         # check text
#         self.assertIn('<p>TestEdit test content.</p>',result.data.decode())
#
#         result = self.test_client.get('/TestEdit/edit',follow_redirects=True,)
#
#         self.assertIn('action="/TestEdit/save"',result.data.decode())
#         self.assertIn('<textarea name="content"',result.data.decode())
#         self.assertIn('<button type="submit"',result.data.decode())
#
#     def test_wikilink(self):
#         result = self.test_client.post(
#             '/TestWikiLink/save',
#             data=dict(content="# Test Wiki Link\n[[TestWikiLink]]\n[[NotFound]].", message=""),
#             follow_redirects=True,
#             )
#         # check header
#         self.assertIn('<a href="/NotFound" class="notfound">NotFound</a>',result.data.decode())
#         self.assertIn('<a href="/TestWikiLink">TestWikiLink</a>',result.data.decode())
#
#     def test_formatter_markdown(self):
#         with self.app.app_context():
#             md = "**bold** *italic*"
#             html = otterwiki.formatter.render_markdown(md)
#         # check html
#         self.assertEqual("<p><strong>bold</strong> <em>italic</em></p>\n",html)
#
#     def test_formatter_wikilink(self):
#         with self.app.app_context():
#             md = "[[abc]]"
#             html = otterwiki.formatter.render_markdown(md)
#         # check html
#         self.assertEqual(html,
#                 '<p><a href="http://localhost.localdomain/abc" class="notfound">abc</a></p>\n'
#                 )
#
#     def test_formatter_wikilink_escaped(self):
#         with self.app.app_context():
#             md = "`[[abc]]`"
#             html = otterwiki.formatter.render_markdown(md)
#         # check html
#         self.assertEqual(html,
#                 '<p><code>[[abc]]</code></p>\n'
#                 )
#
#     def test_codeblock(self):
#         result = self.test_client.post(
#             '/TestCodeblock/save',
#             data=dict(content="# Test Codeblock\n```\ni = 42\n```\nabc\n`somecode`\n```notalanguage\nj = 23\n```", message=""),
#             follow_redirects=True,
#             )
#         # check header
#         self.assertIn('<code>i = 42</code>',result.data.decode())
#         self.assertIn('<code>notalanguage\nj = 23</code>',result.data.decode())
#         self.assertIn('<code>somecode</code>',result.data.decode())
#
#     def test_codeblock_python(self):
#         result = self.test_client.post(
#             '/TestCodeblockPython/save',
#             data=dict(content="# Test Codeblock Python\n```python\ni = 42\n```\n", message=""),
#             follow_redirects=True,
#             )
#         # check header
#         self.assertIn('<div class="highlight"><pre>',result.data.decode())
#         self.assertIn('<span class=".highlight mi">42</span>',result.data.decode())
#
# class TestViewsAccess(unittest.TestCase):
#     def setUp(self):
#         self.test_client = otterwiki.app.test_client()
#         # set permissions
#         otterwiki.app.config['WRITE_ACCESS'] = 'REGISTERED'
#         otterwiki.app.config['ATTACHMENT_ACCESS'] = 'REGISTERED'
#         # handle storage
#         self.tempdir = tempfile.TemporaryDirectory()
#         self.path = self.tempdir.name
#         # create storage
#         self.storage = otterwiki.storage.GitStorage(path=self.path, initialize=True)
#         # update storage in the otterwiki
#         otterwiki.storage.storage = self.storage
#         otterwiki.views.storage = self.storage
#         otterwiki.formatter.storage = self.storage
#         # create Test User
#         from otterwiki.views import User, db, generate_password_hash, datetime
#         self.user = User(name="Test User", email="mail@example.org",
#                 password_hash=generate_password_hash("password1234", method='sha256'),
#                 first_seen=datetime.now(),
#                 last_seen=datetime.now())
#         db.session.add(self.user)
#         db.session.commit()
#
#     def tearDown(self):
#         self.tempdir.cleanup()
#         from otterwiki.views import User, db, generate_password_hash, datetime
#         db.session.delete(self.user)
#         db.session.commit()
#
#     def _login(self):
#         return self.test_client.post(
#                 '/wiki/login',
#                 data=dict(email="mail@example.org",password="password1234",loginorregister="login",name=""),
#                 follow_redirects=True,
#             )
#
#     def test_save_denied(self):
#         result = self.test_client.post(
#             '/TestSave/save',
#             data=dict(content="# Test Save\nTestSave test content.", message=""),
#             follow_redirects=True,
#             )
#         # check header
#         self.assertIn('<title>403 Forbidden</title>',result.data.decode())
#         # check code
#         self.assertEqual(403, result.status_code)
#
#     def test_login(self):
#         result = self._login()
#         self.assertIn('You logged in successfully.', result.data.decode())
#
#     def test_save_allowed(self):
#         # login
#         result = self._login()
#         # and save
#         result = self.test_client.post(
#             '/TestSave/save',
#             data=dict(content="# Test Save\nTestSave test content.", message=""),
#             follow_redirects=True,
#             )
#         p = '<p>TestSave test content.</p>'
#         result_content = result.data.decode()
#         # check text
#         self.assertIn(p ,result_content)
#
# if __name__ == '__main__':
#     unittest.main()
