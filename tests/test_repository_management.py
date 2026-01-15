#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import tempfile
import hashlib
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
import pytest


# Test constants
TEST_REMOTE_URL = "git@github.com:test/repo.git"
TEST_PRIVATE_KEY = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key_content\n-----END OPENSSH PRIVATE KEY-----"
ADMIN_REPO_MGMT_URL = "/-/admin/repository_management"


@pytest.fixture
def test_data():
    """Fixture providing common test data."""
    return {
        'remote_url': TEST_REMOTE_URL,
        'private_key': TEST_PRIVATE_KEY,
        'admin_url': ADMIN_REPO_MGMT_URL,
    }


@pytest.fixture
def repo_manager_mock():
    """Fixture providing a mocked repository manager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from otterwiki.gitstorage import GitStorage
        from otterwiki.repomgmt import RepositoryManager

        storage = GitStorage(tmpdir, initialize=True)
        yield RepositoryManager(storage)


class TestRepositoryManagementAccess:
    """Test access control for repository management."""

    def test_admin_access(self, admin_client):
        """Admin users can access repository management."""
        rv = admin_client.get(ADMIN_REPO_MGMT_URL)
        assert rv.status_code == 200
        html = rv.data.decode()
        assert "Repository Management" in html
        assert "Enable Git Web server" in html
        assert "Enable pushing to SSH remote" in html

    def test_non_admin_access_denied(self, other_client):
        """Non-admin users get 403 when accessing repository management."""
        for method in ['get', 'post']:
            rv = getattr(other_client, method)(
                ADMIN_REPO_MGMT_URL, follow_redirects=True
            )
            assert rv.status_code == 403

    def test_menu_item_visibility(self, admin_client):
        """Repository Management menu item appears in admin menu."""
        rv = admin_client.get("/-/settings")
        assert rv.status_code == 200
        html = rv.data.decode()
        assert "Repository Management" in html
        assert "fa-code-branch" in html


class TestGitWebServer:
    """Test Git Web server configuration."""

    def test_enable_disable_git_web_server(self, app_with_user, admin_client):
        """Test enabling and disabling Git Web server."""
        # Initially disabled
        assert not app_with_user.config.get('GIT_WEB_SERVER')

        # Enable Git Web server
        rv = admin_client.post(
            ADMIN_REPO_MGMT_URL,
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
            ADMIN_REPO_MGMT_URL,
            data={
                "update_preferences": "true",
            },
            follow_redirects=True,
        )

        assert rv.status_code == 200
        assert app_with_user.config['GIT_WEB_SERVER'] == False


class TestGitRemotePush:
    """Test Git remote push functionality."""

    def _enable_push_feature(self, admin_client, test_data, include_key=True):
        """Helper to enable push feature with test data."""
        data = {
            "git_remote_push_enabled": "True",
            "git_remote_push_url": test_data['remote_url'],
            "update_preferences": "true",
        }
        if include_key:
            data["git_remote_push_private_key"] = test_data['private_key']

        return admin_client.post(
            ADMIN_REPO_MGMT_URL, data=data, follow_redirects=True
        )

    def test_enable_basic_push(self, app_with_user, admin_client, test_data):
        """Test enabling git remote push with basic settings."""
        # Initially disabled
        assert not app_with_user.config.get('GIT_REMOTE_PUSH_ENABLED')
        assert not app_with_user.config.get('GIT_REMOTE_PUSH_URL')
        assert not app_with_user.config.get('GIT_REMOTE_PUSH_PRIVATE_KEY')

        # Enable the feature
        rv = self._enable_push_feature(admin_client, test_data)
        assert rv.status_code == 200

        html = rv.data.decode()
        assert "Repository Management Preferences updated" in html

        # Check settings were saved
        assert app_with_user.config['GIT_REMOTE_PUSH_ENABLED'] == True
        assert (
            app_with_user.config['GIT_REMOTE_PUSH_URL']
            == test_data['remote_url']
        )
        assert (
            app_with_user.config['GIT_REMOTE_PUSH_PRIVATE_KEY']
            == test_data['private_key']
        )

    def test_ssh_key_masking(self, app_with_user, admin_client, test_data):
        """Test that SSH private key is masked with asterisks after saving."""
        # Save settings with SSH key
        rv = self._enable_push_feature(admin_client, test_data)
        assert rv.status_code == 200

        # Get form again and check key is masked
        rv = admin_client.get(ADMIN_REPO_MGMT_URL)
        assert rv.status_code == 200

        html = rv.data.decode()
        soup = BeautifulSoup(html, 'html.parser')
        key_textarea = soup.find(
            'textarea', {'name': 'git_remote_push_private_key'}
        )

        assert key_textarea is not None
        assert "**********" in key_textarea.get_text()
        assert test_data['private_key'] not in html

    def test_ssh_key_preservation_with_asterisks(
        self, app_with_user, admin_client, test_data
    ):
        """Test that SSH key is not overwritten when asterisks are submitted unchanged."""
        # Save initial settings
        rv = self._enable_push_feature(admin_client, test_data)
        assert rv.status_code == 200
        assert (
            app_with_user.config['GIT_REMOTE_PUSH_PRIVATE_KEY']
            == test_data['private_key']
        )

        # Submit form again with asterisks
        rv = admin_client.post(
            ADMIN_REPO_MGMT_URL,
            data={
                "git_remote_push_enabled": "True",
                "git_remote_push_url": test_data['remote_url'],
                "git_remote_push_private_key": "**********",
                "update_preferences": "true",
            },
            follow_redirects=True,
        )

        assert rv.status_code == 200
        assert (
            app_with_user.config['GIT_REMOTE_PUSH_PRIVATE_KEY']
            == test_data['private_key']
        )

    def test_ssh_key_cleared_when_disabled(
        self, app_with_user, admin_client, test_data
    ):
        """Test that SSH key is cleared when remote push feature is disabled."""
        # Enable feature first
        rv = self._enable_push_feature(admin_client, test_data)
        assert rv.status_code == 200
        assert (
            app_with_user.config['GIT_REMOTE_PUSH_PRIVATE_KEY']
            == test_data['private_key']
        )

        # Disable feature
        rv = admin_client.post(
            ADMIN_REPO_MGMT_URL,
            data={
                "git_remote_push_url": "",
                "git_remote_push_private_key": "**********",
                "update_preferences": "true",
            },
            follow_redirects=True,
        )

        assert rv.status_code == 200
        assert app_with_user.config['GIT_REMOTE_PUSH_PRIVATE_KEY'] == ""

    def test_validation_missing_url(self, app_with_user, admin_client):
        """Test that enabling remote push without URL shows error."""
        rv = admin_client.post(
            ADMIN_REPO_MGMT_URL,
            data={
                "git_remote_push_enabled": "True",
                "git_remote_push_url": "",
                "git_remote_push_private_key": "",
                "update_preferences": "true",
            },
            follow_redirects=True,
        )

        assert rv.status_code == 200
        html = rv.data.decode()
        assert (
            "SSH Remote URL is required when enabling automatic pushing"
            in html
        )

        # Feature should remain disabled
        assert app_with_user.config['GIT_REMOTE_PUSH_ENABLED'] == False
        assert app_with_user.config['GIT_REMOTE_PUSH_URL'] == ""

    @patch('otterwiki.repomgmt.RepositoryManager.push_to_remote')
    def test_auto_push_functionality(
        self, mock_push, app_with_user, admin_client, test_data
    ):
        """Test that auto-push is triggered when feature is enabled."""
        mock_push.return_value = True

        # Enable remote push
        rv = self._enable_push_feature(admin_client, test_data)
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
        mock_push.assert_called_with(
            test_data['remote_url'], test_data['private_key']
        )


class TestGitRemotePull:
    """Test Git remote pull functionality."""

    def _enable_pull_feature(self, admin_client, test_data):
        """Helper to enable pull feature with test data."""
        return admin_client.post(
            ADMIN_REPO_MGMT_URL,
            data={
                "git_remote_pull_enabled": "True",
                "git_remote_pull_url": test_data['remote_url'],
                "git_remote_pull_private_key": test_data['private_key'],
                "update_preferences": "true",
            },
            follow_redirects=True,
        )

    def test_enable_basic_pull(self, app_with_user, admin_client, test_data):
        """Test enabling git remote pull with basic settings."""
        # Initially disabled
        assert not app_with_user.config.get('GIT_REMOTE_PULL_ENABLED')
        assert not app_with_user.config.get('GIT_REMOTE_PULL_URL')
        assert not app_with_user.config.get('GIT_REMOTE_PULL_PRIVATE_KEY')

        # Enable the feature
        rv = self._enable_pull_feature(admin_client, test_data)
        assert rv.status_code == 200

        html = rv.data.decode()
        assert "Repository Management Preferences updated" in html

        # Check settings were saved
        assert app_with_user.config['GIT_REMOTE_PULL_ENABLED'] == True
        assert (
            app_with_user.config['GIT_REMOTE_PULL_URL']
            == test_data['remote_url']
        )
        assert (
            app_with_user.config['GIT_REMOTE_PULL_PRIVATE_KEY']
            == test_data['private_key']
        )

    def test_validation_missing_url(self, app_with_user, admin_client):
        """Test that enabling remote pull without URL shows error."""
        rv = admin_client.post(
            ADMIN_REPO_MGMT_URL,
            data={
                "git_remote_pull_enabled": "True",
                "git_remote_pull_url": "",
                "git_remote_pull_private_key": "",
                "update_preferences": "true",
            },
            follow_redirects=True,
        )

        assert rv.status_code == 200
        html = rv.data.decode()
        assert (
            "SSH Remote URL is required when enabling automatic pulling"
            in html
        )

        # Feature should remain disabled
        assert app_with_user.config['GIT_REMOTE_PULL_ENABLED'] == False
        assert app_with_user.config['GIT_REMOTE_PULL_URL'] == ""

    @patch('otterwiki.repomgmt.RepositoryManager.auto_pull_webhook')
    @patch('otterwiki.repomgmt.get_repo_manager')
    def test_webhook_functionality(
        self,
        mock_get_repo_manager,
        mock_auto_pull_webhook,
        app_with_user,
        admin_client,
        test_data,
    ):
        """Test that auto-pull webhook is triggered when feature is enabled."""
        # Configure mocks
        mock_repo_manager = MagicMock()
        mock_repo_manager.auto_pull_webhook.return_value = True
        mock_get_repo_manager.return_value = mock_repo_manager

        # Enable remote pull
        rv = self._enable_pull_feature(admin_client, test_data)
        assert rv.status_code == 200

        # Calculate webhook hash and trigger webhook
        webhook_hash = hashlib.sha256(
            (test_data['remote_url'] + 'otterwiki').encode()
        ).hexdigest()
        rv = admin_client.post(f"/-/api/v1/pull/{webhook_hash}")
        assert rv.status_code == 200

        mock_repo_manager.auto_pull_webhook.assert_called_once()

    def test_webhook_security(self, app_with_user, admin_client, test_data):
        """Test webhook endpoint security with incorrect hash and disabled feature."""
        # Enable feature first
        rv = self._enable_pull_feature(admin_client, test_data)
        assert rv.status_code == 200

        # Test with incorrect hash
        rv = admin_client.post("/-/api/v1/pull/incorrecthash123")
        assert rv.status_code == 404

        # Disable feature and test with correct hash
        rv = admin_client.post(
            ADMIN_REPO_MGMT_URL,
            data={
                "update_preferences": "true",
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200

        correct_hash = hashlib.sha256(
            (test_data['remote_url'] + 'otterwiki').encode()
        ).hexdigest()
        rv = admin_client.post(f"/-/api/v1/pull/{correct_hash}")
        assert rv.status_code == 404


class TestGitActionButtons:
    """Test Git action buttons functionality."""

    def _setup_features(
        self, admin_client, test_data, enable_push=False, enable_pull=False
    ):
        """Helper to setup push/pull features."""
        data = {"update_preferences": "true"}

        if enable_push:
            data.update(
                {
                    "git_remote_push_enabled": "True",
                    "git_remote_push_url": test_data['remote_url'],
                }
            )

        if enable_pull:
            data.update(
                {
                    "git_remote_pull_enabled": "True",
                    "git_remote_pull_url": test_data['remote_url'],
                }
            )

        return admin_client.post(
            ADMIN_REPO_MGMT_URL, data=data, follow_redirects=True
        )

    def test_button_visibility(self, app_with_user, admin_client, test_data):
        """Test that git action buttons appear only when corresponding features are enabled."""
        # Initially no buttons should be visible
        rv = admin_client.get(ADMIN_REPO_MGMT_URL)
        soup = BeautifulSoup(rv.data.decode(), 'html.parser')

        assert soup.find('input', {'name': 'git_push'}) is None
        assert soup.find('input', {'name': 'git_force_push'}) is None
        assert soup.find('input', {'name': 'git_pull'}) is None

        # Enable push functionality
        self._setup_features(admin_client, test_data, enable_push=True)
        rv = admin_client.get(ADMIN_REPO_MGMT_URL)
        soup = BeautifulSoup(rv.data.decode(), 'html.parser')

        assert soup.find('input', {'name': 'git_push'}) is not None
        assert soup.find('input', {'name': 'git_force_push'}) is not None
        assert soup.find('input', {'name': 'git_pull'}) is None

        # Enable both push and pull
        self._setup_features(
            admin_client, test_data, enable_push=True, enable_pull=True
        )
        rv = admin_client.get(ADMIN_REPO_MGMT_URL)
        soup = BeautifulSoup(rv.data.decode(), 'html.parser')

        assert soup.find('input', {'name': 'git_push'}) is not None
        assert soup.find('input', {'name': 'git_force_push'}) is not None
        assert soup.find('input', {'name': 'git_pull'}) is not None

    @patch('otterwiki.repomgmt.RepositoryManager.push_to_remote')
    def test_push_button_functionality(
        self, mock_push, app_with_user, admin_client, test_data
    ):
        """Test that the git push button works correctly."""
        mock_push.return_value = (True, "Everything up-to-date")

        # Enable push functionality
        self._setup_features(admin_client, test_data, enable_push=True)

        # Test push button
        rv = admin_client.post(
            ADMIN_REPO_MGMT_URL,
            data={"git_push": "Push"},
            follow_redirects=True,
        )
        assert rv.status_code == 200

        html = rv.data.decode()
        assert "Push Results" in html
        assert "Everything up-to-date" in html

        mock_push.assert_called_with(test_data['remote_url'], "", force=False)

    @patch('otterwiki.repomgmt.RepositoryManager.push_to_remote')
    def test_force_push_button_functionality(
        self, mock_push, app_with_user, admin_client, test_data
    ):
        """Test that the git force push button works correctly."""
        mock_push.return_value = (True, "Force push completed")

        # Enable push functionality
        self._setup_features(admin_client, test_data, enable_push=True)

        # Test force push button
        rv = admin_client.post(
            ADMIN_REPO_MGMT_URL,
            data={"git_force_push": "Force Push"},
            follow_redirects=True,
        )
        assert rv.status_code == 200

        html = rv.data.decode()
        assert "Force Push Results" in html
        assert "Force push completed" in html

        mock_push.assert_called_with(test_data['remote_url'], "", force=True)

    @patch('otterwiki.repomgmt.RepositoryManager.pull_from_remote')
    def test_pull_button_functionality(
        self, mock_pull, app_with_user, admin_client, test_data
    ):
        """Test that the git pull button works correctly."""
        mock_pull.return_value = (True, "Already up to date.")

        # Enable pull functionality
        self._setup_features(admin_client, test_data, enable_pull=True)

        # Test pull button
        rv = admin_client.post(
            ADMIN_REPO_MGMT_URL,
            data={"git_pull": "Pull"},
            follow_redirects=True,
        )
        assert rv.status_code == 200

        html = rv.data.decode()
        assert "Pull Results" in html
        assert "Already up to date." in html

        mock_pull.assert_called_with(test_data['remote_url'], "")

    def test_error_handling_and_styling(
        self, app_with_user, admin_client, test_data
    ):
        """Test error handling and result styling for git actions."""
        # Enable push functionality
        self._setup_features(admin_client, test_data, enable_push=True)

        # Test success styling
        with patch(
            'otterwiki.repomgmt.RepositoryManager.push_to_remote'
        ) as mock_push:
            mock_push.return_value = (True, "Push successful")
            rv = admin_client.post(
                ADMIN_REPO_MGMT_URL,
                data={"git_push": "Push"},
                follow_redirects=True,
            )

            soup = BeautifulSoup(rv.data.decode(), 'html.parser')
            success_pre = soup.find('pre', class_='bg-success')
            assert success_pre is not None
            assert "Push successful" in success_pre.get_text()

        # Test error styling
        with patch(
            'otterwiki.repomgmt.RepositoryManager.push_to_remote'
        ) as mock_push:
            mock_push.return_value = (False, "Permission denied (publickey).")
            rv = admin_client.post(
                ADMIN_REPO_MGMT_URL,
                data={"git_push": "Push"},
                follow_redirects=True,
            )

            soup = BeautifulSoup(rv.data.decode(), 'html.parser')
            error_pre = soup.find('pre', class_='bg-danger')
            assert error_pre is not None
            assert "Permission denied (publickey)." in error_pre.get_text()

    def test_disabled_feature_error_handling(
        self, app_with_user, admin_client
    ):
        """Test that git action buttons return error when feature is disabled."""
        # Ensure features are disabled
        rv = admin_client.post(
            ADMIN_REPO_MGMT_URL,
            data={"update_preferences": "true"},
            follow_redirects=True,
        )
        assert rv.status_code == 200

        # Test push button when disabled
        rv = admin_client.post(
            ADMIN_REPO_MGMT_URL,
            data={"git_push": "Push"},
            follow_redirects=True,
        )
        html = rv.data.decode()
        assert "Push Results" in html
        assert "Push functionality is not enabled" in html

        # Test pull button when disabled
        rv = admin_client.post(
            ADMIN_REPO_MGMT_URL,
            data={"git_pull": "Pull"},
            follow_redirects=True,
        )
        html = rv.data.decode()
        assert "Pull Results" in html
        assert "Pull functionality is not enabled" in html

    @patch('otterwiki.repomgmt.get_repo_manager')
    def test_unavailable_repo_manager_handling(
        self, mock_get_repo_manager, app_with_user, admin_client, test_data
    ):
        """Test that git action buttons handle missing repository manager."""
        mock_get_repo_manager.return_value = None

        # Enable push functionality
        self._setup_features(admin_client, test_data, enable_push=True)

        # Test push button when repo manager is unavailable
        rv = admin_client.post(
            ADMIN_REPO_MGMT_URL,
            data={"git_push": "Push"},
            follow_redirects=True,
        )
        html = rv.data.decode()
        assert "Push Results" in html
        assert "Repository manager not available" in html

    def test_force_push_confirmation_dialog(
        self, app_with_user, admin_client, test_data
    ):
        """Test that force push button has confirmation dialog in the template."""
        # Enable push functionality
        self._setup_features(admin_client, test_data, enable_push=True)

        # Check for confirmation dialog
        rv = admin_client.get(ADMIN_REPO_MGMT_URL)
        soup = BeautifulSoup(rv.data.decode(), 'html.parser')

        force_push_button = soup.find('input', {'name': 'git_force_push'})
        assert force_push_button is not None

        onclick_attr = force_push_button.get('onclick')
        assert onclick_attr is not None
        assert "confirm(" in onclick_attr


class TestSSHKeyManagement:
    """Test SSH key file creation and management."""

    def test_ssh_key_file_creation_and_cleanup(self, repo_manager_mock):
        """Test SSH key temporary file creation and cleanup."""
        test_key = TEST_PRIVATE_KEY

        # Test key file creation
        key_path = repo_manager_mock._create_ssh_key_file(test_key)
        assert key_path is not None
        assert os.path.exists(key_path)

        # Check file permissions (should be readable only by owner)
        stat_info = os.stat(key_path)
        assert stat_info.st_mode & 0o777 == 0o600

        # Check file content
        with open(key_path, 'r') as f:
            content = f.read()
        expected_content = (
            test_key.replace('\r\n', '\n').replace('\r', '\n').rstrip() + '\n'
        )
        assert content == expected_content

        # Test cleanup
        repo_manager_mock._cleanup_ssh_key_file(key_path)
        assert not os.path.exists(key_path)

    def test_ssh_key_file_creation_with_empty_key(self, repo_manager_mock):
        """Test SSH key file creation with empty key."""
        key_path = repo_manager_mock._create_ssh_key_file("")
        assert key_path is None


class TestRepositoryErrorNotifications:
    """Test repository error notification system."""

    @patch('otterwiki.helper.send_mail')
    @patch('otterwiki.helper.get_admin_emails')
    def test_push_error_notifications(
        self,
        mock_get_admin_emails,
        mock_send_mail,
        app_with_user,
        repo_manager_mock,
    ):
        """Test that repository error notifications are sent for push failures."""
        mock_get_admin_emails.return_value = [
            'admin1@example.com',
            'admin2@example.com',
        ]

        with patch.object(repo_manager_mock, 'push_to_remote') as mock_push:
            mock_push.return_value = (False, "Permission denied (publickey)")

            with app_with_user.app_context():
                repo_manager_mock.push_to_remote_async(
                    TEST_REMOTE_URL, TEST_PRIVATE_KEY
                )

            # Verify notification was sent
            mock_send_mail.assert_called()
            call_args = mock_send_mail.call_args

            assert (
                call_args[1]['subject']
                == "OtterWiki Repository Error - Auto Push Failed"
            )
            assert call_args[1]['recipients'] == [
                'admin1@example.com',
                'admin2@example.com',
            ]
            assert "Auto Push" in call_args[1]['text_body']
            assert "Permission denied (publickey)" in call_args[1]['text_body']
            assert TEST_REMOTE_URL in call_args[1]['text_body']

    @patch('otterwiki.helper.send_mail')
    @patch('otterwiki.helper.get_admin_emails')
    def test_pull_error_notifications(
        self,
        mock_get_admin_emails,
        mock_send_mail,
        app_with_user,
        repo_manager_mock,
    ):
        """Test that repository error notifications are sent for pull failures."""
        mock_get_admin_emails.return_value = ['admin@example.com']

        with patch.object(repo_manager_mock, 'pull_from_remote') as mock_pull:
            mock_pull.return_value = (
                False,
                "Could not read from remote repository",
            )

            with app_with_user.app_context():
                repo_manager_mock.pull_from_remote_async(
                    TEST_REMOTE_URL, TEST_PRIVATE_KEY
                )

            # Verify notification was sent
            mock_send_mail.assert_called()
            call_args = mock_send_mail.call_args

            assert (
                call_args[1]['subject']
                == "OtterWiki Repository Error - Auto Pull Failed"
            )
            assert "Auto Pull" in call_args[1]['text_body']
            assert (
                "Could not read from remote repository"
                in call_args[1]['text_body']
            )

    @patch('otterwiki.helper.send_mail')
    @patch('otterwiki.helper.get_admin_emails')
    def test_exception_handling_in_notifications(
        self,
        mock_get_admin_emails,
        mock_send_mail,
        app_with_user,
        repo_manager_mock,
    ):
        """Test that repository error notifications handle exceptions properly."""
        mock_get_admin_emails.return_value = ['admin@example.com']

        with patch.object(repo_manager_mock, 'push_to_remote') as mock_push:
            mock_push.side_effect = Exception("Network timeout")

            with app_with_user.app_context():
                # Should not raise exception, but should send notification
                repo_manager_mock.push_to_remote_async(
                    TEST_REMOTE_URL, TEST_PRIVATE_KEY
                )

            # Verify notification was sent
            mock_send_mail.assert_called()
            call_args = mock_send_mail.call_args

            assert (
                call_args[1]['subject']
                == "OtterWiki Repository Error - Auto Push Failed"
            )
            assert "Network timeout" in call_args[1]['text_body']

    @patch('otterwiki.helper.send_mail')
    @patch('otterwiki.helper.get_admin_emails')
    def test_no_notifications_when_no_admins(
        self,
        mock_get_admin_emails,
        mock_send_mail,
        app_with_user,
        repo_manager_mock,
    ):
        """Test that no notifications are sent when no admin emails are found."""
        mock_get_admin_emails.return_value = []

        with patch.object(repo_manager_mock, 'push_to_remote') as mock_push:
            mock_push.return_value = (False, "Permission denied")

            with app_with_user.app_context():
                repo_manager_mock.push_to_remote_async(
                    TEST_REMOTE_URL, TEST_PRIVATE_KEY
                )

            # Verify no notification was sent
            mock_send_mail.assert_not_called()

    def test_get_admin_emails_function(self, app_with_user):
        """Test the get_admin_emails helper function."""
        from otterwiki.helper import get_admin_emails
        from otterwiki.auth import get_all_user

        with app_with_user.app_context():
            admin_emails = get_admin_emails()
            assert isinstance(admin_emails, list)

            # Check that admin user emails are included
            all_users = get_all_user()
            admin_users = [user for user in all_users if user.is_admin]

            for admin_user in admin_users:
                if admin_user.email:
                    assert admin_user.email in admin_emails
