#!/env/bin/python
# vim: set et ts=8 sts=4 sw=4 ai:

import subprocess
import os

from flask import request, abort, make_response, Response
from otterwiki.server import app
from otterwiki.auth import current_user, has_permission, check_credentials


class GitHttpServer:
    def __init__(self, path: str):
        self.path = path
        # configure git to allow pushing into the current branch
        # of the non-bare repository, see https://git-scm.com/docs/git-config#Documentation/git-config.txt-receivedenyCurrentBranch
        config_command = [
            "git",
            "config",
            "--file",
            os.path.join(self.path, ".git", "config"),
            "receive.denyCurrentBranch",
            "updateInstead",
        ]
        p = subprocess.run(config_command, capture_output=True)
        if p.returncode > 0:
            app.logger.error(
                f"GitHttpServer failed: {config_command} with \"{p.stderr}\""
            )

    def check_if_enabled(self):
        # FIXME
        if not app.config["GIT_WEB_SERVER"]:
            abort(404, "Feature GITHTTPSERVER not enabled.")

    def check_permission(self, permission):
        if not has_permission(permission, current_user):
            auth = request.authorization
            if auth is None:
                abort(
                    401,
                    response=Response(
                        'Please authenticate with your OtterWiki email address and password.',
                        401,
                        {'WWW-Authenticate': 'Basic realm="Login Required"'},
                    ),
                )
            user = check_credentials(auth.username, auth.password)
            if not user or not has_permission(permission, user):
                abort(403)

    def advertise_refs(self, service: str):
        self.check_if_enabled()
        if service not in ["git-upload-pack", "git-receive-pack"]:
            return abort(400)

        # permissions check
        if service == "git-receive-pack":
            self.check_permission("UPLOAD")
        else:
            self.check_permission("READ")

        command = [service, "--stateless-rpc", "--advertise-refs", self.path]
        p = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()
        if p.returncode > 0:
            app.logger.error(
                f"GitHttpServer failed: {command} with \"{stderr}\""
            )
            return abort(500)
        data = b'# service=' + service.encode()
        datalen = len(data) + 4
        datalen = b'%04x' % datalen
        data = datalen + data + b'0000' + stdout
        response = make_response(data)
        response.mimetype = f"application/x-{service}-advertisement"
        return response

    def git_upload_pack(self, stream):
        self.check_if_enabled()
        self.check_permission("READ")
        return self.git_pack("upload", stream)

    def git_receive_pack(self, stream):
        self.check_if_enabled()
        self.check_permission("UPLOAD")
        result = self.git_pack("receive", stream)

        try:
            from otterwiki.repomgmt import get_repo_manager
            from otterwiki.server import storage

            storage.notify_repository_changed_from_external()

            repo_manager = get_repo_manager()
            if repo_manager:
                repo_manager.auto_push_if_enabled()
        except Exception as e:
            app.logger.error(f"Auto-push after git receive failed: {e}")

        return result

    def git_pack(self, service, stream):
        command = [f"git-{service}-pack", "--stateless-rpc", self.path]
        p = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate(stream.read())
        if p.returncode > 0:
            app.logger.error(
                f"GitHttpServer failed: {command} with \"{stderr}\""
            )
            return abort(500)

        response = make_response(stdout)
        response.mimetype = f"application/x-git-{service}-pack-result"
        return response


# vim: set et ts=8 sts=4 sw=4 ai
