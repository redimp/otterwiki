import unittest

import otterwiki
import otterwiki.views
import otterwiki.formatter
import tempfile
from pprint import pprint

class TestViews(unittest.TestCase):
    def setUp(self):
        self.app = otterwiki.app
        self.app.config['SERVER_NAME'] = 'localhost.localdomain'
        self.test_client = self.app.test_client()

        self.tempdir = tempfile.TemporaryDirectory()
        self.path = self.tempdir.name
        # create storage
        self.storage = otterwiki.storage.GitStorage(path=self.path, initialize=True)
        # update storage in the otterwiki
        otterwiki.storage.storage = self.storage
        otterwiki.views.storage = self.storage
        otterwiki.formatter.storage = self.storage

    def tearDown(self):
        self.tempdir.cleanup()

    def test_about(self):
        result = self.test_client.get('/wiki/about')
        self.assertEqual(200, result.status_code)
        self.assertIn('About an Otter Wiki',result.data.decode())

    def test_home(self):
        result = self.test_client.get('/')
        # check title
        self.assertIn('<title> 404',result.data.decode())
        # check header
        self.assertIn('<h1>404</h1>',result.data.decode())
        # check for error text
        self.assertIn('Page Home not found',result.data.decode())
        # check if create link exists
        self.assertIn('/wiki/create/Home',result.data.decode())
        # create /Home
        content="# Home\nTesting the wiki homepage."
        author = ("Example Author", "mail@example.com")
        self.assertTrue( self.storage.store("home.md",
            content=content,
            author=author,
            message="added Home") )
        result = self.test_client.get('/')
        # check header
        self.assertIn('<h1>Home</h1>',result.data.decode())
        # check text
        self.assertIn('<p>Testing the wiki homepage.</p>',result.data.decode())

    def test_not_found(self):
        result = self.test_client.get('/NotFound')
        # check title
        self.assertIn('<title> 404',result.data.decode())
        # check header
        self.assertIn('<h1>404</h1>',result.data.decode())
        # check for error text
        self.assertIn('Page NotFound not found',result.data.decode())
        # check if create link exists
        self.assertIn('/wiki/create/NotFound',result.data.decode())

    def test_save(self):
        result = self.test_client.post(
            '/TestSave/save',
            data=dict(content="# Test Save\nTestSave test content.", message=""),
            follow_redirects=True,
            )
        # check text
        self.assertIn('<p>TestSave test content.</p>',result.data.decode())

    def test_create(self):
        result = self.test_client.get('/wiki/create')
        # check header
        self.assertIn('<h1>Create Page</h1>',result.data.decode())
        # check text
        self.assertIn('action="/wiki/create"',result.data.decode())

    def test_create2(self):
        result = self.test_client.get('/wiki/create/CreateTest')
        # check header
        self.assertIn('<h1>Create Page</h1>',result.data.decode())
        # check text
        self.assertIn('action="/wiki/create"',result.data.decode())
        # check post
        result = self.test_client.post(
            '/wiki/create',
            data=dict(pagename="CreateTest"),
            follow_redirects=True,
            )
        self.assertIn('action="/CreateTest/save"',result.data.decode())
        self.assertIn('<textarea name="content"',result.data.decode())
        # create page
        result = self.test_client.post(
            '/CreateTest/save',
            data=dict(content="# Create Test\nCreate Test content.", message=""),
            follow_redirects=True,
            )
        # check existing page
        result = self.test_client.post(
            '/wiki/create',
            data=dict(pagename="CreateTest"),
            follow_redirects=True,
            )
        self.assertIn('Page CreateTest exists already.',result.data.decode())

    def test_edit(self):
        result = self.test_client.post(
            '/TestEdit/save',
            data=dict(content="# Test Edit\nTestEdit test content.", message=""),
            follow_redirects=True,
            )
        # check header
        self.assertIn('<h1 id="toc-0"><a id="test-edit" href="#test-edit">Test Edit<span class="anchor">&nbsp;</span></a></h1>',result.data.decode())
        # check text
        self.assertIn('<p>TestEdit test content.</p>',result.data.decode())

        result = self.test_client.get('/TestEdit/edit',follow_redirects=True,)

        self.assertIn('action="/TestEdit/save"',result.data.decode())
        self.assertIn('<textarea name="content"',result.data.decode())
        self.assertIn('<button type="submit"',result.data.decode())

    def test_wikilink(self):
        result = self.test_client.post(
            '/TestWikiLink/save',
            data=dict(content="# Test Wiki Link\n[[TestWikiLink]]\n[[NotFound]].", message=""),
            follow_redirects=True,
            )
        # check header
        self.assertIn('<a href="/NotFound" class="notfound">NotFound</a>',result.data.decode())
        self.assertIn('<a href="/TestWikiLink">TestWikiLink</a>',result.data.decode())

    def test_formatter_markdown(self):
        with self.app.app_context():
            md = "**bold** *italic*"
            html = otterwiki.formatter.render_markdown(md)
        # check html
        self.assertEqual("<p><strong>bold</strong> <em>italic</em></p>\n",html)

    def test_formatter_wikilink(self):
        with self.app.app_context():
            md = "[[abc]]"
            html = otterwiki.formatter.render_markdown(md)
        # check html
        self.assertEqual(html,
                '<p><a href="http://localhost.localdomain/abc" class="notfound">abc</a></p>\n'
                )

    def test_formatter_wikilink_escaped(self):
        with self.app.app_context():
            md = "`[[abc]]`"
            html = otterwiki.formatter.render_markdown(md)
        # check html
        self.assertEqual(html,
                '<p><code>[[abc]]</code></p>\n'
                )

    def test_codeblock(self):
        result = self.test_client.post(
            '/TestCodeblock/save',
            data=dict(content="# Test Codeblock\n```\ni = 42\n```\nabc\n`somecode`\n```notalanguage\nj = 23\n```", message=""),
            follow_redirects=True,
            )
        # check header
        self.assertIn('<code>i = 42</code>',result.data.decode())
        self.assertIn('<code>notalanguage\nj = 23</code>',result.data.decode())
        self.assertIn('<code>somecode</code>',result.data.decode())

    def test_codeblock_python(self):
        result = self.test_client.post(
            '/TestCodeblockPython/save',
            data=dict(content="# Test Codeblock Python\n```python\ni = 42\n```\n", message=""),
            follow_redirects=True,
            )
        # check header
        self.assertIn('<div class="highlight"><pre>',result.data.decode())
        self.assertIn('<span class=".highlight mi">42</span>',result.data.decode())

class TestViewsAccess(unittest.TestCase):
    def setUp(self):
        self.test_client = otterwiki.app.test_client()
        # set permissions
        otterwiki.app.config['WRITE_ACCESS'] = 'REGISTERED'
        otterwiki.app.config['ATTACHMENT_ACCESS'] = 'REGISTERED'
        # handle storage
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = self.tempdir.name
        # create storage
        self.storage = otterwiki.storage.GitStorage(path=self.path, initialize=True)
        # update storage in the otterwiki
        otterwiki.storage.storage = self.storage
        otterwiki.views.storage = self.storage
        otterwiki.formatter.storage = self.storage
        # create Test User
        from otterwiki.views import User, db, generate_password_hash, datetime
        self.user = User(name="Test User", email="mail@example.org",
                password_hash=generate_password_hash("password1234", method='sha256'),
                first_seen=datetime.now(),
                last_seen=datetime.now())
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        self.tempdir.cleanup()
        from otterwiki.views import User, db, generate_password_hash, datetime
        db.session.delete(self.user)
        db.session.commit()

    def _login(self):
        return self.test_client.post(
                '/wiki/login',
                data=dict(email="mail@example.org",password="password1234",loginorregister="login",name=""),
                follow_redirects=True,
            )

    def test_save_denied(self):
        result = self.test_client.post(
            '/TestSave/save',
            data=dict(content="# Test Save\nTestSave test content.", message=""),
            follow_redirects=True,
            )
        # check header
        self.assertIn('<title>403 Forbidden</title>',result.data.decode())
        # check code
        self.assertEqual(403, result.status_code)

    def test_login(self):
        result = self._login()
        self.assertIn('You logged in successfully.', result.data.decode())

    def test_save_allowed(self):
        # login
        result = self._login()
        # and save
        result = self.test_client.post(
            '/TestSave/save',
            data=dict(content="# Test Save\nTestSave test content.", message=""),
            follow_redirects=True,
            )
        p = '<p>TestSave test content.</p>'
        result_content = result.data.decode()
        # check text
        self.assertIn(p ,result_content)

if __name__ == '__main__':
    unittest.main()
