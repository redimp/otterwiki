#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import tempfile
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup


def test_repository_management_form_access(admin_client):
    """Test that the repository management form is accessible to admin users."""
    rv = admin_client.get("/-/admin/repository_management")
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Repository Management" in html
    assert "Enable Git Web server" in html
    assert "Enable automatic pushing to SSH remote" in html


def test_repository_management_form_403(app_with_user, other_client):
    """Test that non-admin users get 403 when accessing repository management."""
    rv = other_client.get(
        "/-/admin/repository_management", follow_redirects=True
    )
    assert rv.status_code == 403
    rv = other_client.post(
        "/-/admin/repository_management", follow_redirects=True
    )
    assert rv.status_code == 403


def test_repository_management_menu_item(admin_client):
    """Test that the Repository Management menu item appears in the admin menu."""
    rv = admin_client.get("/-/settings")
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Repository Management" in html
    assert "fa-code-branch" in html


def test_enable_git_remote_push_basic(app_with_user, admin_client):
    """Test enabling git remote push with basic settings."""
    test_remote_url = "git@github.com:test/repo.git"
    test_private_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key_content\n-----END OPENSSH PRIVATE KEY-----"

    # Initially disabled
    assert not app_with_user.config.get('GIT_REMOTE_PUSH_ENABLED')
    assert not app_with_user.config.get('GIT_REMOTE_URL')
    assert not app_with_user.config.get('GIT_REMOTE_PRIVATE_KEY')

    # Enable the feature with URL and key
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_url": test_remote_url,
            "git_remote_private_key": test_private_key,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Repository Management Preferences updated" in html

    # Check that settings were saved (config values are now properly converted to boolean)
    assert app_with_user.config['GIT_REMOTE_PUSH_ENABLED'] == True
    assert app_with_user.config['GIT_REMOTE_URL'] == test_remote_url
    assert app_with_user.config['GIT_REMOTE_PRIVATE_KEY'] == test_private_key


def test_ssh_key_masking_in_form(app_with_user, admin_client):
    """Test that SSH private key is masked with asterisks after saving."""
    test_remote_url = "git@github.com:test/repo.git"
    test_private_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key_content\n-----END OPENSSH PRIVATE KEY-----"

    # Save settings with SSH key
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_url": test_remote_url,
            "git_remote_private_key": test_private_key,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Get the form again and check that key is masked
    rv = admin_client.get("/-/admin/repository_management")
    assert rv.status_code == 200
    html = rv.data.decode()
    soup = BeautifulSoup(html, 'html.parser')
    key_textarea = soup.find('textarea', {'name': 'git_remote_private_key'})
    assert key_textarea is not None
    # Should show asterisks, not the actual key
    assert "**********" in key_textarea.get_text()
    assert test_private_key not in html


def test_ssh_key_not_overwritten_when_asterisks_unchanged(
    app_with_user, admin_client
):
    """Test that SSH key is not overwritten when asterisks are submitted unchanged."""
    test_remote_url = "git@github.com:test/repo.git"
    test_private_key = "-----BEGIN OPENSSH PRIVATE KEY-----\noriginal_key\n-----END OPENSSH PRIVATE KEY-----"

    # Save initial settings
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_url": test_remote_url,
            "git_remote_private_key": test_private_key,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert app_with_user.config['GIT_REMOTE_PRIVATE_KEY'] == test_private_key

    # Submit form again with asterisks (simulating unchanged key field)
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_url": test_remote_url,
            "git_remote_private_key": "**********",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Key should remain unchanged
    assert app_with_user.config['GIT_REMOTE_PRIVATE_KEY'] == test_private_key


def test_ssh_key_cleared_when_feature_disabled(app_with_user, admin_client):
    """Test that SSH key is cleared when remote push feature is disabled."""
    test_remote_url = "git@github.com:test/repo.git"
    test_private_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key\n-----END OPENSSH PRIVATE KEY-----"

    # Enable feature first
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_url": test_remote_url,
            "git_remote_private_key": test_private_key,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert app_with_user.config['GIT_REMOTE_PRIVATE_KEY'] == test_private_key

    # Disable feature (don't send git_remote_push_enabled when unchecked)
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_url": "",
            "git_remote_private_key": "**********",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Key should be cleared
    assert app_with_user.config['GIT_REMOTE_PRIVATE_KEY'] == ""


def test_git_remote_push_validation_missing_url(app_with_user, admin_client):
    """Test that enabling remote push without URL shows error and disables feature."""
    # Try to enable feature without providing required URL
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_url": "",  # Empty URL
            "git_remote_private_key": "",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "SSH Remote URL is required when enabling automatic pushing" in html

    # Feature should remain disabled
    assert app_with_user.config['GIT_REMOTE_PUSH_ENABLED'] == False
    assert app_with_user.config['GIT_REMOTE_URL'] == ""
    assert app_with_user.config['GIT_REMOTE_PRIVATE_KEY'] == ""


def test_git_web_server_setting_in_repository_management(
    app_with_user, admin_client
):
    """Test that Git Web server setting works."""
    # Initially disabled
    assert not app_with_user.config.get('GIT_WEB_SERVER')

    # Enable Git Web server
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_web_server": "True",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert app_with_user.config['GIT_WEB_SERVER'] == True

    # Disable Git Web server
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert app_with_user.config['GIT_WEB_SERVER'] == False


@patch('otterwiki.gitstorage.GitStorage.push_to_remote')
def test_auto_push_functionality_mock(mock_push, app_with_user, admin_client):
    """Test that auto-push is triggered when feature is enabled (mocked)."""
    test_remote_url = "git@github.com:test/repo.git"
    test_private_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key\n-----END OPENSSH PRIVATE KEY-----"

    # Configure mock to return success
    mock_push.return_value = True

    # Enable remote push
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_url": test_remote_url,
            "git_remote_private_key": test_private_key,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Create a test page to trigger git operations
    rv = admin_client.post(
        "/TestPage/save",
        data={
            "content": "# Test Page\n\nThis is a test page for auto-push functionality.\n",
            "commit": "Test commit for auto-push",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Verify that push_to_remote was called
    mock_push.assert_called_with(test_remote_url, test_private_key)


def test_ssh_key_file_creation_and_cleanup():
    """Test SSH key temporary file creation and cleanup."""
    from otterwiki.gitstorage import GitStorage
    import tempfile
    import os

    # Create a temporary git repository for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = GitStorage(tmpdir, initialize=True)

        test_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key_content\n-----END OPENSSH PRIVATE KEY-----"

        # Test key file creation
        key_path = storage._create_ssh_key_file(test_key)
        assert key_path is not None
        assert os.path.exists(key_path)

        # Check file permissions (should be readable only by owner)
        stat_info = os.stat(key_path)
        assert stat_info.st_mode & 0o777 == 0o600

        # Check file content
        with open(key_path, 'r') as f:
            content = f.read()
        # The _create_ssh_key_file method normalizes line endings and ensures a trailing newline
        expected_content = (
            test_key.replace('\r\n', '\n').replace('\r', '\n').rstrip() + '\n'
        )
        assert content == expected_content

        # Test cleanup
        storage._cleanup_ssh_key_file(key_path)
        assert not os.path.exists(key_path)


def test_ssh_key_file_creation_with_empty_key():
    """Test SSH key file creation with empty key."""
    from otterwiki.gitstorage import GitStorage
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = GitStorage(tmpdir, initialize=True)

        # Test with empty key
        key_path = storage._create_ssh_key_file("")
        assert key_path is None

        # Test with None key
        key_path = storage._create_ssh_key_file(None)
        assert key_path is None
