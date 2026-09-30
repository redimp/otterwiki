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
