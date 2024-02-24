import pytest
from base64 import b64encode


@pytest.fixture
def create_app_with_git(create_app):
    create_app.config["GIT_WEB_SERVER"] = True
    yield create_app
    create_app.config["GIT_WEB_SERVER"] = False


@pytest.fixture
def test_client_with_git(create_app_with_git):
    client = create_app_with_git.test_client()
    return client


def test_git_info_refs_404(create_app, test_client):
    rv = test_client.get(
        "/.git/info/refs?service=git-upload-pack",
        follow_redirects=True,
    )
    assert rv.status_code == 404

    rv = test_client.get(
        "/.git/info/refs?service=git-receive-pack",
        follow_redirects=True,
    )
    assert rv.status_code == 404

    rv = test_client.post(
        "/.git/git-upload-pack"
    )
    assert rv.status_code == 404

    rv = test_client.post(
        "/.git/git-receive-pack"
    )
    assert rv.status_code == 404


def test_git_info_refs(create_app_with_git, test_client_with_git):
    create_app_with_git.config["READ_ACCESS"] = "ANONYMOUS"
    create_app_with_git.config["WRITE_ACCESS"] = "ANONYMOUS"
    rv = test_client_with_git.get(
        "/.git/info/refs?service=git-upload-pack",
        follow_redirects=True,
    )
    assert rv.status_code == 200
    rv = test_client_with_git.get(
        "/.git/info/refs?service=git-receive-pack",
        follow_redirects=True,
    )
    assert rv.status_code == 200

    rv = test_client_with_git.get(
        "/.git/info/refs?service=git-random-service",
        follow_redirects=True,
    )
    assert rv.status_code == 400

def test_git_info_refs_permissions(create_app_with_git, test_client_with_git):
    create_app_with_git.config["READ_ACCESS"] = "ANONYMOUS"
    create_app_with_git.config["WRITE_ACCESS"] = "ANONYMOUS"
    rv = test_client_with_git.get(
        "/.git/info/refs?service=git-upload-pack",
        follow_redirects=True,
    )
    assert rv.status_code == 200
    rv = test_client_with_git.get(
        "/.git/info/refs?service=git-receive-pack",
        follow_redirects=True,
    )
    assert rv.status_code == 200
    create_app_with_git.config["WRITE_ACCESS"] = "ADMIN"

    rv = test_client_with_git.get(
        "/.git/info/refs?service=git-upload-pack",
        follow_redirects=True,
    )
    assert rv.status_code == 200
    rv = test_client_with_git.get(
        "/.git/info/refs?service=git-receive-pack",
        follow_redirects=True,
    )
    assert rv.status_code == 401

    create_app_with_git.config["READ_ACCESS"] = "ADMIN"

    rv = test_client_with_git.get(
        "/.git/info/refs?service=git-upload-pack",
        follow_redirects=True,
    )
    assert rv.status_code == 401
    rv = test_client_with_git.get(
        "/.git/info/refs?service=git-receive-pack",
        follow_redirects=True,
    )
    assert rv.status_code == 401

def test_git_pack(create_app_with_git, test_client_with_git):
    create_app_with_git.config["READ_ACCESS"] = "ANONYMOUS"
    create_app_with_git.config["WRITE_ACCESS"] = "ANONYMOUS"
    rv = test_client_with_git.get(
        "/.git/info/refs?service=git-upload-pack",
        follow_redirects=True,
    )
    rv = test_client_with_git.post(
        "/.git/git-upload-pack",
    )
    # We expect 500 here, since we are not providing the correct data=b'00a8want ... multi_ack_detailed no-done side-band-64k thin-pack ofs-delta deepen-since deepen-not ...'
    assert rv.status_code == 500

    rv = test_client_with_git.post(
        "/.git/git-receive-pack"
    )
    assert rv.status_code == 500

    create_app_with_git.config["WRITE_ACCESS"] = "ADMIN"
    rv = test_client_with_git.post(
        "/.git/git-upload-pack"
    )
    assert rv.status_code == 500

    rv = test_client_with_git.post(
        "/.git/git-receive-pack"
    )
    assert rv.status_code == 401

def test_git_pack_auth(app_with_user):
    test_client = app_with_user.test_client()
    app_with_user.config["GIT_WEB_SERVER"] = True
    app_with_user.config["READ_ACCESS"] = "APPROVED"
    app_with_user.config["WRITE_ACCESS"] = "APPROVED"

    rv = test_client.get(
        "/.git/info/refs?service=git-upload-pack",
        follow_redirects=True,
    )
    assert rv.status_code == 401

    rv = test_client.get(
        "/.git/info/refs?service=git-upload-pack",
        follow_redirects=True,
        headers={"Authorization": "Basic {}".format(b64encode(b"test_user:test_password"))},
    )
    assert rv.status_code == 401

    credentials = b64encode(b"mail@example.org:password1234").decode('utf-8')

    rv = test_client.get(
        "/.git/info/refs?service=git-upload-pack",
        headers={"Authorization": f"Basic {credentials}"},
    )
    assert rv.status_code == 200

    app_with_user.config["GIT_WEB_SERVER"] = False
    app_with_user.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_user.config["WRITE_ACCESS"] = "ANONYMOUS"
