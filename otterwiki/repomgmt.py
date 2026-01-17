#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import tempfile
import stat
from threading import Thread, Lock


class RepositoryManager:
    """
    Repository management functionality for Git operations including
    push/pull operations, SSH key management, and periodic pull scheduling.
    """

    git_push_pull_Lock = Lock()

    def __init__(self, storage):
        """Initialize with a GitStorage instance."""
        self.storage = storage

    def _create_ssh_key_file(self, private_key):
        """
        Create a temporary SSH key file with proper permissions.
        Returns the path to the temporary file.
        """
        if not private_key:
            return None

        fd, key_path = tempfile.mkstemp(prefix='otterwiki_ssh_', suffix='.key')
        try:
            with os.fdopen(fd, 'w') as f:
                # SSH key must use unix line endings only
                key_content = private_key.replace('\r\n', '\n').replace(
                    '\r', '\n'
                )
                # and a newline at the end
                key_content = key_content.rstrip() + '\n'
                f.write(key_content)

            # the key should be readable only by the owner
            os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)
            return key_path
        except Exception:
            self._cleanup_ssh_key_file(key_path)
            raise

    def _cleanup_ssh_key_file(self, key_path):
        if key_path and os.path.exists(key_path):
            try:
                os.unlink(key_path)
            except OSError:
                pass

    def _setup_ssh_environment(self, private_key=None):
        """
        Setup SSH environment for git operations.
        Returns (key_path, original_ssh_command, original_ssh_auth_sock)
        """
        key_path = None
        original_ssh_command = os.environ.get('GIT_SSH_COMMAND')
        original_ssh_auth_sock = os.environ.get('SSH_AUTH_SOCK')

        if private_key:
            key_path = self._create_ssh_key_file(private_key)

            # completely isolate SSH:
            # - disable SSH agent
            # - clear all default key locations
            # - force only our identity
            ssh_command = (
                f'ssh '
                f'-F /dev/null '
                f'-o StrictHostKeyChecking=no '
                f'-o UserKnownHostsFile=/dev/null '
                f'-o IdentitiesOnly=yes '
                f'-o PasswordAuthentication=no '
                f'-o PubkeyAuthentication=yes '
                f'-o PreferredAuthentications=publickey '
                f'-o IdentityFile={key_path} '
                f'-o IdentityFile2=none '
            )
            os.environ['GIT_SSH_COMMAND'] = ssh_command

            if 'SSH_AUTH_SOCK' in os.environ:
                del os.environ['SSH_AUTH_SOCK']
        else:
            # if no private key is provided, we assume that
            # there is no auth or it's handled externally
            os.environ['GIT_SSH_COMMAND'] = (
                'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
            )

        return key_path, original_ssh_command, original_ssh_auth_sock

    def _restore_ssh_environment(
        self, key_path, original_ssh_command, original_ssh_auth_sock
    ):
        """
        Restore SSH environment after git operations.
        """
        if key_path:
            self._cleanup_ssh_key_file(key_path)

        # restore original SSH command and SSH agent
        if original_ssh_command is not None:
            os.environ['GIT_SSH_COMMAND'] = original_ssh_command
        elif 'GIT_SSH_COMMAND' in os.environ:
            del os.environ['GIT_SSH_COMMAND']
        if original_ssh_auth_sock is not None:
            os.environ['SSH_AUTH_SOCK'] = original_ssh_auth_sock

    def push_to_remote(self, remote_url, private_key=None, force=False):
        """
        Push the current branch to a remote repository.
        Returns (success, output) tuple.
        """
        if not remote_url:
            return False, "No remote URL provided"

        with self.git_push_pull_Lock:
            key_path, original_ssh_command, original_ssh_auth_sock = (
                self._setup_ssh_environment(private_key)
            )

            try:
                from otterwiki.server import app

                try:
                    current_branch = self.storage.repo.active_branch.name
                except TypeError:
                    # if there is no current branch we should probably just stop
                    return False, "No active branch found"

                action_type = "Force push" if force else "Push"
                app.logger.info(
                    f"[RepositoryManager] {action_type} to remote: {remote_url}"
                )

                if force:
                    result = self.storage.repo.git.push(
                        remote_url, current_branch, force=True
                    )
                else:
                    result = self.storage.repo.git.push(
                        remote_url, current_branch
                    )

                if result:
                    app.logger.info(
                        f"[RepositoryManager] {action_type} result: {result}"
                    )
                return True, result or f"{action_type} completed successfully"

            except Exception as e:
                try:
                    from otterwiki.server import app

                    app.logger.error(
                        f"[RepositoryManager] Push to remote failed: {e}"
                    )
                except ImportError:
                    pass
                return False, str(e)
            finally:
                self._restore_ssh_environment(
                    key_path, original_ssh_command, original_ssh_auth_sock
                )

    def pull_from_remote(self, remote_url, private_key=None):
        """
        Pull from a remote repository.
        Returns (success, output) tuple.
        """
        if not remote_url:
            return False, "No remote URL provided"

        with self.git_push_pull_Lock:
            key_path, original_ssh_command, original_ssh_auth_sock = (
                self._setup_ssh_environment(private_key)
            )

            try:
                from otterwiki.server import app

                try:
                    current_branch = self.storage.repo.active_branch.name
                except TypeError:
                    # if there is no current branch we should probably just stop
                    return False, "No active branch found"

                app.logger.info(
                    f"[RepositoryManager] Pulling from remote: {remote_url}"
                )
                result = self.storage.repo.git.pull(remote_url, current_branch)
                if result:
                    app.logger.info(
                        f"[RepositoryManager] Pull result: {result}"
                    )
                return True, result or "Pull completed successfully"

            except Exception as e:
                try:
                    from otterwiki.server import app

                    app.logger.error(
                        f"[RepositoryManager] Pull from remote failed: {e}"
                    )
                except ImportError:
                    pass
                return False, str(e)
            finally:
                self._restore_ssh_environment(
                    key_path, original_ssh_command, original_ssh_auth_sock
                )

    def push_to_remote_async(self, remote_url, private_key=None):
        """
        Asynchronously push to remote repository.
        """
        try:
            from otterwiki.server import app

            with app.app_context():
                app.logger.debug(
                    "[RepositoryManager] push_to_remote_async() started"
                )
                success, output = self.push_to_remote(remote_url, private_key)
                if not success:
                    # Send error notification for failed automatic push
                    from otterwiki.helper import (
                        send_repository_error_notification,
                    )

                    send_repository_error_notification(
                        "Auto Push", output, remote_url
                    )
        except Exception as e:
            try:
                from otterwiki.server import app

                app.logger.error(
                    f"[RepositoryManager] push_to_remote_async() failed: {e}"
                )
                # Send error notification for exception in automatic push
                from otterwiki.helper import send_repository_error_notification

                send_repository_error_notification(
                    "Auto Push", str(e), remote_url
                )
            except ImportError:
                pass

    def pull_from_remote_async(self, remote_url, private_key=None):
        """
        Asynchronously pull from remote repository.
        """
        try:
            from otterwiki.server import app

            with app.app_context():
                app.logger.debug(
                    "[RepositoryManager] pull_from_remote_async() started"
                )
                success, output = self.pull_from_remote(
                    remote_url, private_key
                )
                if not success:
                    # Send error notification for failed automatic pull
                    from otterwiki.helper import (
                        send_repository_error_notification,
                    )

                    send_repository_error_notification(
                        "Auto Pull", output, remote_url
                    )
        except Exception as e:
            try:
                from otterwiki.server import app

                app.logger.error(
                    f"[RepositoryManager] pull_from_remote_async() failed: {e}"
                )
                # Send error notification for exception in automatic pull
                from otterwiki.helper import send_repository_error_notification

                send_repository_error_notification(
                    "Auto Pull", str(e), remote_url
                )
            except ImportError:
                pass

    def auto_push_if_enabled(self):
        """
        Automatically push to remote if the feature is enabled.
        This method should be called after any git operation that changes the repository.
        Push happens asynchronously to avoid blocking user interaction.
        """
        try:
            from otterwiki.server import app

            if not app.config.get('GIT_REMOTE_PUSH_ENABLED'):
                return

            remote_url = app.config.get('GIT_REMOTE_PUSH_URL')
            if not remote_url:
                return

            private_key = app.config.get('GIT_REMOTE_PUSH_PRIVATE_KEY')

            thr = Thread(
                target=self.push_to_remote_async,
                args=[remote_url, private_key],
            )
            thr.start()

            # while testing wait for the thread to finish
            if app.config['TESTING']:
                thr.join()

        except Exception as e:
            try:
                from otterwiki.server import app

                app.logger.error(f"[RepositoryManager] Auto-push failed: {e}")
            except ImportError:
                pass

    def auto_pull_webhook(self):
        """
        Pull from remote repository via webhook trigger.
        This method should be called when the webhook endpoint is hit.
        """
        try:
            from otterwiki.server import app

            if not app.config.get('GIT_REMOTE_PULL_ENABLED'):
                return False

            remote_url = app.config.get('GIT_REMOTE_PULL_URL')
            if not remote_url:
                return False

            private_key = app.config.get('GIT_REMOTE_PULL_PRIVATE_KEY')

            thr = Thread(
                target=self.pull_from_remote_async,
                args=[remote_url, private_key],
            )
            thr.start()
            return True

        except Exception as e:
            try:
                from otterwiki.server import app

                app.logger.error(
                    f"[RepositoryManager] Auto-pull webhook failed: {e}"
                )
            except ImportError:
                pass
            return False


repo_manager = None


def initialize_repo_management(storage):
    """
    Initialize the global repository management instances.
    This should be called from server.py after storage is created.
    """
    global repo_manager
    repo_manager = RepositoryManager(storage)


def get_repo_manager():
    """Get the global repository manager instance."""
    return repo_manager
