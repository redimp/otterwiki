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
    assert "Enable pushing to SSH remote" in html


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
    assert not app_with_user.config.get('GIT_REMOTE_PUSH_URL')
    assert not app_with_user.config.get('GIT_REMOTE_PUSH_PRIVATE_KEY')

    # Enable the feature with URL and key
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_push_url": test_remote_url,
            "git_remote_push_private_key": test_private_key,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Repository Management Preferences updated" in html

    # Check that settings were saved (config values are now properly converted to boolean)
    assert app_with_user.config['GIT_REMOTE_PUSH_ENABLED'] == True
    assert app_with_user.config['GIT_REMOTE_PUSH_URL'] == test_remote_url
    assert (
        app_with_user.config['GIT_REMOTE_PUSH_PRIVATE_KEY'] == test_private_key
    )


def test_ssh_key_masking_in_form(app_with_user, admin_client):
    """Test that SSH private key is masked with asterisks after saving."""
    test_remote_url = "git@github.com:test/repo.git"
    test_private_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key_content\n-----END OPENSSH PRIVATE KEY-----"

    # Save settings with SSH key
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_push_url": test_remote_url,
            "git_remote_push_private_key": test_private_key,
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
    key_textarea = soup.find(
        'textarea', {'name': 'git_remote_push_private_key'}
    )
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
            "git_remote_push_url": test_remote_url,
            "git_remote_push_private_key": test_private_key,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert (
        app_with_user.config['GIT_REMOTE_PUSH_PRIVATE_KEY'] == test_private_key
    )

    # Submit form again with asterisks (simulating unchanged key field)
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_push_url": test_remote_url,
            "git_remote_push_private_key": "**********",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Key should remain unchanged
    assert (
        app_with_user.config['GIT_REMOTE_PUSH_PRIVATE_KEY'] == test_private_key
    )


def test_ssh_key_cleared_when_feature_disabled(app_with_user, admin_client):
    """Test that SSH key is cleared when remote push feature is disabled."""
    test_remote_url = "git@github.com:test/repo.git"
    test_private_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key\n-----END OPENSSH PRIVATE KEY-----"

    # Enable feature first
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_push_url": test_remote_url,
            "git_remote_push_private_key": test_private_key,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert (
        app_with_user.config['GIT_REMOTE_PUSH_PRIVATE_KEY'] == test_private_key
    )

    # Disable feature (don't send git_remote_push_enabled when unchecked)
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_url": "",
            "git_remote_push_private_key": "**********",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Key should be cleared
    assert app_with_user.config['GIT_REMOTE_PUSH_PRIVATE_KEY'] == ""


def test_git_remote_push_validation_missing_url(app_with_user, admin_client):
    """Test that enabling remote push without URL shows error and disables feature."""
    # Try to enable feature without providing required URL
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_push_url": "",  # Empty URL
            "git_remote_push_private_key": "",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "SSH Remote URL is required when enabling automatic pushing" in html

    # Feature should remain disabled
    assert app_with_user.config['GIT_REMOTE_PUSH_ENABLED'] == False
    assert app_with_user.config['GIT_REMOTE_PUSH_URL'] == ""
    assert app_with_user.config['GIT_REMOTE_PUSH_PRIVATE_KEY'] == ""


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


@patch('otterwiki.repomgmt.RepositoryManager.push_to_remote')
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
            "git_remote_push_url": test_remote_url,
            "git_remote_push_private_key": test_private_key,
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
    from otterwiki.repomgmt import RepositoryManager
    from otterwiki.gitstorage import GitStorage
    import tempfile
    import os

    # Create a temporary git repository for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = GitStorage(tmpdir, initialize=True)
        repo_manager = RepositoryManager(storage)

        test_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key_content\n-----END OPENSSH PRIVATE KEY-----"

        # Test key file creation
        key_path = repo_manager._create_ssh_key_file(test_key)
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
        repo_manager._cleanup_ssh_key_file(key_path)
        assert not os.path.exists(key_path)


def test_ssh_key_file_creation_with_empty_key():
    """Test SSH key file creation with empty key."""
    from otterwiki.repomgmt import RepositoryManager
    from otterwiki.gitstorage import GitStorage
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = GitStorage(tmpdir, initialize=True)
        repo_manager = RepositoryManager(storage)

        # Test with empty key
        key_path = repo_manager._create_ssh_key_file("")
        assert key_path is None


@patch('otterwiki.repomgmt.RepositoryManager.auto_pull_webhook')
@patch('otterwiki.repomgmt.get_repo_manager')
def test_auto_pull_webhook_functionality_mock(
    mock_get_repo_manager, mock_auto_pull_webhook, app_with_user, admin_client
):
    """Test that auto-pull webhook is triggered when feature is enabled (mocked)."""
    test_remote_url = "git@github.com:test/repo.git"
    test_private_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key\n-----END OPENSSH PRIVATE KEY-----"

    # Configure mocks
    mock_repo_manager = MagicMock()
    mock_repo_manager.auto_pull_webhook.return_value = True
    mock_get_repo_manager.return_value = mock_repo_manager

    # Enable remote pull
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_pull_enabled": "True",
            "git_remote_pull_url": test_remote_url,
            "git_remote_pull_private_key": test_private_key,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Test webhook endpoint (need to calculate the hash)
    import hashlib

    webhook_hash = hashlib.sha256(
        (test_remote_url + 'otterwiki').encode()
    ).hexdigest()

    # Trigger webhook
    rv = admin_client.post(f"/-/api/v1/pull/{webhook_hash}")
    assert rv.status_code == 200

    # Verify that auto_pull_webhook was called
    mock_repo_manager.auto_pull_webhook.assert_called_once()


def test_webhook_incorrect_hash_returns_404(app_with_user, admin_client):
    """Test that webhook endpoint returns 404 for incorrect hash."""
    test_remote_url = "git@github.com:test/repo.git"
    test_private_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key\n-----END OPENSSH PRIVATE KEY-----"

    # Enable remote pull
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_pull_enabled": "True",
            "git_remote_pull_url": test_remote_url,
            "git_remote_pull_private_key": test_private_key,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Test with incorrect hash - should return 404
    incorrect_hash = "incorrecthash123"
    rv = admin_client.post(f"/-/api/v1/pull/{incorrect_hash}")
    assert rv.status_code == 404

    # Test with correct hash but feature disabled
    import hashlib

    correct_hash = hashlib.sha256(
        (test_remote_url + 'otterwiki').encode()
    ).hexdigest()

    # Disable the feature
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Now the correct hash should also return 404 since feature is disabled
    rv = admin_client.post(f"/-/api/v1/pull/{correct_hash}")
    assert rv.status_code == 404


def test_webhook_endpoint_when_feature_disabled(app_with_user, admin_client):
    """Test that webhook endpoint returns 404 when pull feature is disabled."""
    # Feature is disabled by default, any hash should return 404
    rv = admin_client.post("/-/api/v1/pull/anyhash")
    assert rv.status_code == 404


def test_webhook_endpoint_missing_remote_url(app_with_user, admin_client):
    """Test that webhook endpoint returns 404 when remote URL is not configured."""
    # Enable feature but don't set remote URL (this shouldn't be possible through UI but test edge case)
    from otterwiki.server import app

    with app.app_context():
        app.config['GIT_REMOTE_PULL_ENABLED'] = True
        app.config['GIT_REMOTE_PULL_URL'] = None

        # Any hash should return 404 when no remote URL is configured
        rv = admin_client.post("/-/api/v1/pull/anyhash")
        assert rv.status_code == 404


def test_git_remote_pull_validation_missing_url(app_with_user, admin_client):
    """Test that enabling remote pull without URL shows error and disables feature."""
    # Try to enable feature without providing required URL
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_pull_enabled": "True",
            "git_remote_pull_url": "",  # Empty URL
            "git_remote_pull_private_key": "",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "SSH Remote URL is required when enabling automatic pulling" in html

    # Feature should remain disabled
    assert app_with_user.config['GIT_REMOTE_PULL_ENABLED'] == False
    assert app_with_user.config['GIT_REMOTE_PULL_URL'] == ""
    assert app_with_user.config['GIT_REMOTE_PULL_PRIVATE_KEY'] == ""


def test_enable_git_remote_pull_basic(app_with_user, admin_client):
    """Test enabling git remote pull with basic settings."""
    test_remote_url = "git@github.com:test/repo.git"
    test_private_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key_content\n-----END OPENSSH PRIVATE KEY-----"

    # Initially disabled
    assert not app_with_user.config.get('GIT_REMOTE_PULL_ENABLED')
    assert not app_with_user.config.get('GIT_REMOTE_PULL_URL')
    assert not app_with_user.config.get('GIT_REMOTE_PULL_PRIVATE_KEY')

    # Enable the feature with URL and key
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_pull_enabled": "True",
            "git_remote_pull_url": test_remote_url,
            "git_remote_pull_private_key": test_private_key,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Repository Management Preferences updated" in html

    # Check that settings were saved
    assert app_with_user.config['GIT_REMOTE_PULL_ENABLED'] == True
    assert app_with_user.config['GIT_REMOTE_PULL_URL'] == test_remote_url
    assert (
        app_with_user.config['GIT_REMOTE_PULL_PRIVATE_KEY'] == test_private_key
    )


def test_git_action_buttons_visibility(app_with_user, admin_client):
    """Test that git action buttons appear only when corresponding features are enabled."""
    # First, explicitly disable all features to ensure clean state
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Now check that no buttons should be visible
    rv = admin_client.get("/-/admin/repository_management")
    assert rv.status_code == 200
    html = rv.data.decode()
    soup = BeautifulSoup(html, 'html.parser')

    # No action buttons should be present initially
    push_button = soup.find('input', {'name': 'git_push'})
    force_push_button = soup.find('input', {'name': 'git_force_push'})
    pull_button = soup.find('input', {'name': 'git_pull'})

    assert push_button is None
    assert force_push_button is None
    assert pull_button is None

    # Enable push functionality
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_push_url": "git@github.com:test/repo.git",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Now push buttons should be visible
    rv = admin_client.get("/-/admin/repository_management")
    html = rv.data.decode()
    soup = BeautifulSoup(html, 'html.parser')

    push_button = soup.find('input', {'name': 'git_push'})
    force_push_button = soup.find('input', {'name': 'git_force_push'})
    pull_button = soup.find('input', {'name': 'git_pull'})

    assert push_button is not None
    assert force_push_button is not None
    assert pull_button is None  # Pull still disabled

    # Enable pull functionality
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_push_url": "git@github.com:test/repo.git",
            "git_remote_pull_enabled": "True",
            "git_remote_pull_url": "git@github.com:test/repo.git",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Now all buttons should be visible
    rv = admin_client.get("/-/admin/repository_management")
    html = rv.data.decode()
    soup = BeautifulSoup(html, 'html.parser')

    push_button = soup.find('input', {'name': 'git_push'})
    force_push_button = soup.find('input', {'name': 'git_force_push'})
    pull_button = soup.find('input', {'name': 'git_pull'})

    assert push_button is not None
    assert force_push_button is not None
    assert pull_button is not None


@patch('otterwiki.repomgmt.RepositoryManager.push_to_remote')
def test_git_push_button_functionality(mock_push, app_with_user, admin_client):
    """Test that the git push button works correctly."""
    test_remote_url = "git@github.com:test/repo.git"
    test_private_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key\n-----END OPENSSH PRIVATE KEY-----"

    # Configure mock to return success
    mock_push.return_value = (True, "Everything up-to-date")

    # Enable push functionality
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_push_url": test_remote_url,
            "git_remote_push_private_key": test_private_key,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Test push button
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_push": "Push",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()

    # Check that push was called with correct parameters
    mock_push.assert_called_with(
        test_remote_url, test_private_key, force=False
    )

    # Check that results are displayed
    assert "Push Results" in html
    assert "Everything up-to-date" in html
    soup = BeautifulSoup(html, 'html.parser')
    results_div = soup.find('div', class_='card')
    assert results_div is not None


@patch('otterwiki.repomgmt.RepositoryManager.push_to_remote')
def test_git_force_push_button_functionality(
    mock_push, app_with_user, admin_client
):
    """Test that the git force push button works correctly."""
    test_remote_url = "git@github.com:test/repo.git"
    test_private_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key\n-----END OPENSSH PRIVATE KEY-----"

    # Configure mock to return success
    mock_push.return_value = (True, "Force push completed")

    # Enable push functionality
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_push_url": test_remote_url,
            "git_remote_push_private_key": test_private_key,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Test force push button
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_force_push": "Force Push",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()

    # Check that push was called with force=True
    mock_push.assert_called_with(test_remote_url, test_private_key, force=True)

    # Check that results are displayed
    assert "Force Push Results" in html
    assert "Force push completed" in html


@patch('otterwiki.repomgmt.RepositoryManager.pull_from_remote')
def test_git_pull_button_functionality(mock_pull, app_with_user, admin_client):
    """Test that the git pull button works correctly."""
    test_remote_url = "git@github.com:test/repo.git"
    test_private_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key\n-----END OPENSSH PRIVATE KEY-----"

    # Configure mock to return success
    mock_pull.return_value = (True, "Already up to date.")

    # Enable pull functionality
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_pull_enabled": "True",
            "git_remote_pull_url": test_remote_url,
            "git_remote_pull_private_key": test_private_key,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Test pull button
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_pull": "Pull",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()

    # Check that pull was called with correct parameters
    mock_pull.assert_called_with(test_remote_url, test_private_key)

    # Check that results are displayed
    assert "Pull Results" in html
    assert "Already up to date." in html


@patch('otterwiki.repomgmt.RepositoryManager.push_to_remote')
def test_git_push_button_error_handling(
    mock_push, app_with_user, admin_client
):
    """Test that git push button handles errors correctly."""
    test_remote_url = "git@github.com:test/repo.git"

    # Configure mock to return error
    mock_push.return_value = (False, "Permission denied (publickey).")

    # Enable push functionality
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_push_url": test_remote_url,
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Test push button with error
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_push": "Push",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()

    # Check that error is displayed with proper styling
    assert "Push Results" in html
    assert "Permission denied (publickey)." in html
    soup = BeautifulSoup(html, 'html.parser')
    error_pre = soup.find('pre', class_='bg-danger')
    assert error_pre is not None


@patch('otterwiki.repomgmt.RepositoryManager.push_to_remote')
@patch('otterwiki.repomgmt.RepositoryManager.pull_from_remote')
def test_git_action_buttons_when_feature_disabled(
    mock_pull, mock_push, app_with_user, admin_client
):
    """Test that git action buttons return error when feature is disabled."""
    # Ensure features are disabled first
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Try to use push button when push is disabled
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_push": "Push",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()

    # Should show error message
    assert "Push Results" in html
    assert "Push functionality is not enabled" in html

    # Try to use pull button when pull is disabled
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_pull": "Pull",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()

    # Should show error message
    assert "Pull Results" in html
    assert "Pull functionality is not enabled" in html

    # Verify that the actual git methods were never called
    mock_push.assert_not_called()
    mock_pull.assert_not_called()


@patch('otterwiki.repomgmt.get_repo_manager')
def test_git_action_buttons_when_repo_manager_unavailable(
    mock_get_repo_manager, app_with_user, admin_client
):
    """Test that git action buttons handle missing repository manager."""
    # Configure mock to return None (repo manager unavailable)
    mock_get_repo_manager.return_value = None

    # Enable push functionality
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_push_url": "git@github.com:test/repo.git",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Test push button when repo manager is unavailable
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_push": "Push",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    html = rv.data.decode()

    # Should show error message
    assert "Push Results" in html
    assert "Repository manager not available" in html


def test_force_push_confirmation_dialog_in_template(
    app_with_user, admin_client
):
    """Test that force push button has confirmation dialog in the template."""
    # Enable push functionality
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_push_url": "git@github.com:test/repo.git",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Get the form and check for confirmation dialog
    rv = admin_client.get("/-/admin/repository_management")
    html = rv.data.decode()
    soup = BeautifulSoup(html, 'html.parser')

    force_push_button = soup.find('input', {'name': 'git_force_push'})
    assert force_push_button is not None

    # Check that onclick attribute contains confirmation dialog
    onclick_attr = force_push_button.get('onclick')
    assert onclick_attr is not None
    assert "confirm(" in onclick_attr


def test_git_action_results_styling(app_with_user, admin_client):
    """Test that git action results have proper styling for success and error cases."""
    from unittest.mock import patch

    # Enable push functionality
    rv = admin_client.post(
        "/-/admin/repository_management",
        data={
            "git_remote_push_enabled": "True",
            "git_remote_push_url": "git@github.com:test/repo.git",
            "update_preferences": "true",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # Test success case
    with patch(
        'otterwiki.repomgmt.RepositoryManager.push_to_remote'
    ) as mock_push:
        mock_push.return_value = (True, "Push successful")

        rv = admin_client.post(
            "/-/admin/repository_management",
            data={
                "git_push": "Push",
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()
        soup = BeautifulSoup(html, 'html.parser')

        # Should have success styling
        success_pre = soup.find('pre', class_='bg-success')
        assert success_pre is not None
        assert "Push successful" in success_pre.get_text()

    # Test error case
    with patch(
        'otterwiki.repomgmt.RepositoryManager.push_to_remote'
    ) as mock_push:
        mock_push.return_value = (False, "Push failed")

        rv = admin_client.post(
            "/-/admin/repository_management",
            data={
                "git_push": "Push",
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200
        html = rv.data.decode()
        soup = BeautifulSoup(html, 'html.parser')

        # Should have error styling
        error_pre = soup.find('pre', class_='bg-danger')
        assert error_pre is not None
        assert "Push failed" in error_pre.get_text()
