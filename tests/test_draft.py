# /usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:
from test_auth import login


def create_draft(test_client, pagepath, content):
    cursor_line = "1"
    cursor_ch = "2"
    rv = test_client.post(
        "/{}/draft".format(pagepath),
        data={
            "content": content,
            "cursor_line": cursor_line,
            "cursor_ch": cursor_ch,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert rv.json["status"] == "draft saved"


def test_create_draft(app_with_user, test_client):
    assert app_with_user
    from otterwiki.models import Drafts

    # login the client
    login(test_client)

    pagepath = "test_create_draft"
    content = "test\ntest\n"

    assert len(Drafts.query.filter_by(pagepath=pagepath).all()) == 0
    create_draft(test_client, pagepath, content)

    assert len(Drafts.query.filter_by(pagepath=pagepath).all()) == 1
    d = Drafts.query.filter_by(pagepath=pagepath).first()
    assert d is not None
    assert d.content == content
    assert d.datetime.tzinfo is not None
    # clean up
    Drafts.query.filter_by(pagepath=pagepath).delete()


def test_draft_warning(app_with_user, test_client):
    assert app_with_user
    from otterwiki.models import Drafts

    # login the client
    login(test_client)

    pagepath = "test_draft_warning"
    content = "test\ntest\n"

    # assert no drafts there
    assert len(Drafts.query.filter_by(pagepath=pagepath).all()) == 0

    create_draft(test_client, pagepath, content)

    # open up editor, should see a draft warning
    rv = test_client.get(
        "/{}/edit".format(pagepath),
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Continue editing draft?".lower() in html.lower()

    # open up editor with the draft
    rv = test_client.post(
        "/{}/edit".format(pagepath),
        data={'draft': 'edit'},
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    # check that the draft content is to be found
    assert content in html


def test_draft_discard(app_with_user, test_client):
    assert app_with_user
    from otterwiki.models import Drafts

    # login the client
    login(test_client)

    pagepath = "test_draft_discard"
    content = "test\ntest\n"

    # assert no drafts there
    assert len(Drafts.query.filter_by(pagepath=pagepath).all()) == 0

    create_draft(test_client, pagepath, content)

    # open up editor, should see a draft warning
    rv = test_client.get(
        "/{}/edit".format(pagepath),
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Continue editing draft?".lower() in html.lower()

    # discard draft
    rv = test_client.post(
        "/{}/edit".format(pagepath),
        data={'draft': 'discard'},
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert len(Drafts.query.filter_by(pagepath=pagepath).all()) == 0
    html = rv.data.decode()
    # check that the page content is back to the default for new pages
    assert "# Test_Draft_Discard" in html


def test_draft_unchanged_is_discarded(app_with_user, test_client):
    assert app_with_user
    from otterwiki.models import Drafts

    # login the client
    login(test_client)

    pagepath = "test_draft_unchanged"
    content = "# Unchanged\n\nfirst line\n"
    rv = test_client.post(
        "/{}/save".format(pagepath),
        data={"content": content, "commit": "initial commit"},
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # store a draft with changes
    create_draft(test_client, pagepath, content + "second line\n")
    assert len(Drafts.query.filter_by(pagepath=pagepath).all()) == 1

    # revert the changes, the draft is identical to the stored page
    rv = test_client.post(
        "/{}/draft".format(pagepath),
        data={"content": content.replace("\n", "\r\n") + "\r\n"},
    )
    assert rv.status_code == 200
    assert rv.json["status"] == "draft discarded"
    assert len(Drafts.query.filter_by(pagepath=pagepath).all()) == 0

    # the editor opens without the draft warning
    rv = test_client.get("/{}/edit".format(pagepath))
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Continue editing draft?".lower() not in html.lower()


def test_draft_unchanged_new_page_is_discarded(app_with_user, test_client):
    assert app_with_user
    from otterwiki.models import Drafts

    # login the client
    login(test_client)

    pagepath = "test_draft_unchanged_new_page"
    # the content the editor starts with for new pages
    rv = test_client.post(
        "/{}/draft".format(pagepath),
        data={"content": "# Test_Draft_Unchanged_New_Page\n\n"},
    )
    assert rv.status_code == 200
    assert rv.json["status"] == "draft discarded"
    assert len(Drafts.query.filter_by(pagepath=pagepath).all()) == 0

    create_draft(test_client, pagepath, "# Test_Draft_Unchanged_New_Page\n\nX")
    assert len(Drafts.query.filter_by(pagepath=pagepath).all()) == 1
    # clean up
    Drafts.query.filter_by(pagepath=pagepath).delete()


def test_discard_draft(app_with_user, test_client):
    assert app_with_user
    from otterwiki.models import Drafts

    # login the client
    login(test_client)

    pagepath = "test_discard_draft"
    create_draft(test_client, pagepath, "test\ntest\n")
    assert len(Drafts.query.filter_by(pagepath=pagepath).all()) == 1

    rv = test_client.post("/{}/draft/discard".format(pagepath))
    assert rv.status_code == 200
    assert rv.json["status"] == "draft discarded"
    assert len(Drafts.query.filter_by(pagepath=pagepath).all()) == 0

    # discarding a non existing draft is fine
    rv = test_client.post("/{}/draft/discard".format(pagepath))
    assert rv.status_code == 200


def save_page(test_client, pagepath, content, commit="commit"):
    rv = test_client.post(
        "/{}/save".format(pagepath),
        data={"content": content, "commit": commit},
        follow_redirects=True,
    )
    assert rv.status_code == 200


def page_revision(pagepath):
    from otterwiki.server import storage
    from otterwiki.helper import get_filename

    return storage.metadata(get_filename(pagepath))["revision"]


def store_as_someone_else(pagepath, content, message):
    from otterwiki.server import storage
    from otterwiki.helper import get_filename

    assert storage.store(
        filename=get_filename(pagepath),
        content=content,
        message=message,
        author=("Someone Else", "someone@example.org"),
    )


def post_draft(test_client, pagepath, content, revision):
    rv = test_client.post(
        "/{}/draft".format(pagepath),
        data={"content": content, "revision": revision},
    )
    assert rv.status_code == 200
    assert rv.json["status"] == "draft saved"


def test_draft_diff(app_with_user, test_client):
    assert app_with_user
    login(test_client)

    pagepath = "test_draft_diff"
    save_page(test_client, pagepath, "# Diff\n\nfirst line\n")
    post_draft(
        test_client,
        pagepath,
        "# Diff\n\nfirst line\nline from the draft\n",
        page_revision(pagepath),
    )

    rv = test_client.get("/{}/edit".format(pagepath))
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Continue editing draft?" in html
    assert 'id="draft-diff"' in html
    assert '<tr class="added">' in html
    assert "line from the draft" in html
    assert 'id="draft-outdated"' not in html


def test_draft_outdated(app_with_user, test_client):
    assert app_with_user
    login(test_client)

    pagepath = "test_draft_outdated"
    save_page(test_client, pagepath, "# Outdated\n\nfirst line\n")
    base_revision = page_revision(pagepath)
    post_draft(
        test_client,
        pagepath,
        "# Outdated\n\nfirst line\nline from the draft\n",
        base_revision,
    )
    # someone else changes the page
    store_as_someone_else(
        pagepath,
        "# Outdated\n\nfirst line\nline from someone else\n",
        "change by someone else",
    )
    current_revision = page_revision(pagepath)
    assert current_revision != base_revision

    rv = test_client.get("/{}/edit".format(pagepath))
    assert rv.status_code == 200
    html = rv.data.decode()
    assert 'id="draft-outdated"' in html
    assert "has been changed since the draft was started" in html
    assert "change by someone else" in html
    assert (
        "/{}/diff/{}/{}".format(pagepath, base_revision, current_revision)
        in html
    )
    # the diff shows only the changes made in the draft
    diff = html.split('id="draft-diff"')[1].split("</table>")[0]
    assert "line from the draft" in diff
    assert "line from someone else" not in diff

    # continuing the draft keeps the revision the draft is based on
    rv = test_client.post(
        "/{}/edit".format(pagepath),
        data={"draft": "edit"},
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert 'formData.append("revision", "{}")'.format(base_revision) in html
    assert "has been changed since the draft was started" in html


def test_draft_outdated_new_page(app_with_user, test_client):
    assert app_with_user
    login(test_client)

    pagepath = "test_draft_outdated_new_page"
    # draft of a page that doesn't exist yet
    post_draft(test_client, pagepath, "# New\n\nfrom the draft\n", "")
    # someone else creates the page
    store_as_someone_else(
        pagepath, "# New\n\ncreated meanwhile\n", "create page"
    )

    rv = test_client.get("/{}/edit".format(pagepath))
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "has been changed since the draft was started" in html
    diff = html.split('id="draft-diff"')[1].split("</table>")[0]
    assert "from the draft" in diff
    assert "created meanwhile" not in diff


def test_draft_outdated_deleted_page(app_with_user, test_client):
    assert app_with_user
    login(test_client)

    pagepath = "test_draft_outdated_deleted"
    save_page(test_client, pagepath, "# Deleted\n\nfirst line\n")
    post_draft(
        test_client,
        pagepath,
        "# Deleted\n\nfirst line\nfrom the draft\n",
        page_revision(pagepath),
    )
    rv = test_client.post(
        "/{}/delete".format(pagepath),
        data={"message": "delete page"},
        follow_redirects=True,
    )
    assert rv.status_code == 200

    rv = test_client.get("/{}/edit".format(pagepath))
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "has been deleted since the draft was started" in html
    diff = html.split('id="draft-diff"')[1].split("</table>")[0]
    assert "from the draft" in diff


def test_draft_unknown_revision(app_with_user, test_client):
    assert app_with_user
    login(test_client)

    pagepath = "test_draft_unknown_revision"
    save_page(test_client, pagepath, "# Unknown\n\nfirst line\n")
    post_draft(
        test_client, pagepath, "# Unknown\n\nfrom the draft\n", "abcdef"
    )

    rv = test_client.get("/{}/edit".format(pagepath))
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "can not be found in the history" in html
    assert "Compared to the stored version" in html
    assert "from the draft" in html
