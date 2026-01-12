#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import pathlib
import re
from datetime import datetime
from typing import List, cast

import git
import git.exc

from otterwiki.util import split_path, ttl_lru_cache
from otterwiki.repomgmt import get_repo_manager


class StorageError(Exception):
    pass


class StorageNotFound(StorageError):
    pass


try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


class GitStorage(object):
    def __init__(self, path, initialize=False):
        # make path absolute
        self.path = str(pathlib.Path(path).absolute())
        if initialize:
            self.repo = git.Repo.init(self.path)
        self.repo = self._read_repo()

    def _read_repo(self):
        try:
            return git.Repo(self.path)
        except git.InvalidGitRepositoryError:
            raise StorageError(
                "No valid git repository in '{}'. Did you run 'git init'?".format(
                    self.path
                )
            )

    def _check_reload(self):
        if os.path.exists(os.path.join(self.path, ".git/RELOAD_GIT")):
            os.remove(os.path.join(self.path, ".git/RELOAD_GIT"))
            self.repo = self._read_repo()

    def exists(self, filename):
        return os.path.exists(os.path.join(self.path, filename))

    def mtime(self, filename):
        return datetime.fromtimestamp(
            os.path.getmtime(os.path.join(self.path, filename))
        )

    def size(self, filename: str) -> int:
        """
        Get the filesize in bytes
        """
        return os.path.getsize(os.path.join(self.path, filename))

    def isdir(self, dirname):
        return os.path.isdir(os.path.join(self.path, dirname))

    def isemptydir(self, dirname):
        return len(os.listdir(os.path.join(self.path, dirname))) == 0

    def load(self, filename, mode="r", revision=None, size=-1):
        self._check_reload()
        if revision is not None:
            try:
                content = self.repo.git.show(
                    "{}:{}".format(revision, filename)
                )
                if mode == "rb":
                    content = content.encode("utf8", "surrogateescape")
            except git.exc.GitCommandError:
                raise StorageNotFound
            return content
        try:
            with open(os.path.join(self.path, filename), mode=mode) as f:
                content = f.read(size)
        except (IOError, FileNotFoundError):
            raise StorageNotFound("{} not found.".format(filename))
        return content

    @ttl_lru_cache(maxsize=128, ttl=60)
    def _get_metadata_of_commit(self, commit):
        metadata = {
            "revision-full": commit.hexsha,
            "revision": commit.hexsha[
                0:6
            ],  # FIXME: Too slow, self.repo.git.rev_parse(commit.hexsha, short=6),
            "datetime": commit.authored_datetime,
            "author_name": commit.author.name,
            "author_email": commit.author.email,
            #            'author' : '{} {}'.format(commit.author.name, commit.author.email),
            "message": commit.message,
            "files": commit.stats.files,  # This is slow
        }
        # this is a workaround
        if commit.author.email is None:
            metadata["author_name"] = (
                metadata["author_name"].replace("<>", "").strip()
            )
        return metadata

    def _get_commit(self, filename, revision):
        self._check_reload()
        commit = None
        if revision is None:
            try:
                commit = list(
                    self.repo.iter_commits(paths=filename, max_count=1)
                )[0]
            except (ValueError, IndexError, git.exc.GitCommandError):
                raise StorageNotFound
        else:
            try:
                all_commits = list(self.repo.iter_commits(paths=filename))
            except (git.exc.GitCommandError, ValueError):
                raise StorageNotFound
            for c in all_commits:
                if c.hexsha.startswith(revision):
                    # found
                    commit = c
                    break
        # not found :(
        if commit is None:
            raise StorageNotFound

        return commit

    def blame(self, filename, revision=None):
        if revision is None:
            revision = "HEAD"
        try:
            commits = list(self.repo.blame(revision, filename) or [])
        except (ValueError, IndexError, git.exc.GitCommandError):
            raise StorageNotFound
        # initialize data and helper
        blamedata = []
        metadata_cache = {}
        n = 1
        # blame can return an iterable blame if incremental=True
        # casting to keep it obvious we aren't doing that
        # can be removed if gitpython adds an overload on incremental
        for commit, lines in cast(
            List[List[git.Commit | List[str | bytes] | None]], commits
        ):
            try:
                metadata = metadata_cache[commit]
            except KeyError:
                metadata = self._get_metadata_of_commit(commit)
                metadata_cache[commit] = metadata
            for line in cast(List[str | bytes], lines) or []:
                blamedata.append(
                    (
                        metadata["revision"],
                        metadata["author_name"],
                        metadata["datetime"],
                        n,
                        line,
                    )
                )
                # increase linenumber
                n += 1
        return blamedata

    def metadata(self, filename, revision=None):
        # sha = repo.head.object.hexsha
        # short_sha = repo.git.rev_parse(sha, short=6)
        commit = self._get_commit(filename, revision)

        return self._get_metadata_of_commit(commit)

    def _get_metadata_of_log(self, logentry: str):
        logentry_lines = logentry.split("\n")
        # Get revision
        revision = re.findall(r"commit ([a-z0-9]*)", logentry_lines[0])[0]
        # Check if a offset for entries is necessary
        offset = 0
        if logentry_lines[1].startswith("Merge:"):
            offset = 1
        # Find author data
        author_info = re.findall(
            r"Author: ([^\<]*) <([^\>]*)>", logentry_lines[offset + 1]
        )[0]
        author_name = author_info[0]
        author_email = author_info[1]
        # Get and convert Datetime
        datetime_str = re.findall("Date: (.*)", logentry_lines[offset + 2])[
            0
        ].strip()
        datetime_obj = datetime.strptime(
            datetime_str, "%a %b %d %H:%M:%S %Y %z"
        )
        # Get commit msg
        message = "\n".join(
            [x.strip() for x in logentry_lines[offset + 4 : -2]]
        )

        files = logentry_lines[-1].split("\x00")

        # TODO: make an object?
        metadata = {
            "revision-full": revision,
            "revision": revision[0:6],
            "author_name": author_name,
            "author_email": author_email,
            "datetime": datetime_obj,
            "files": files,
            "message": message,
        }

        return metadata

    def log(self, filename=None, fail_on_git_error=False, max_count=None):
        if filename is None:
            try:
                if max_count:
                    rawlog = self.repo.git.log(
                        "--name-only", "-z", f"--max-count={max_count}"
                    )
                else:
                    rawlog = self.repo.git.log("--name-only", "-z")
            except git.exc.GitCommandError as e:
                if fail_on_git_error:
                    raise StorageNotFound(str(e))
                return []
        else:
            try:
                if max_count:
                    rawlog = self.repo.git.log(
                        "--name-only",
                        "-z",
                        "--follow",
                        f"--max-count={max_count}",
                        "--",
                        filename,
                    )
                else:
                    rawlog = self.repo.git.log(
                        "--name-only", "-z", "--follow", "--", filename
                    )
            except git.exc.GitCommandError as e:
                raise StorageNotFound(str(e))

        # clean up artifacts
        rawlog = [
            entry
            for entry in re.split(r'\x00\x00|\n\x00', rawlog.strip("\x00"))
            if len(entry) > 0
        ]
        # raise Exception of no log entry has been found
        if len(rawlog) < 1:
            raise StorageNotFound

        return [self._get_metadata_of_log(entry) for entry in rawlog]

    def log_slow(self, filename=None):
        if filename is None:
            try:
                commits = list(self.repo.iter_commits())
            except (IndexError, ValueError):
                return []
        else:
            try:
                commits = list(self.repo.iter_commits(paths=filename))
            except (IndexError, ValueError):
                raise StorageNotFound
            if len(commits) == 0:
                raise StorageNotFound
        # build and return logfile
        return [self._get_metadata_of_commit(commit) for commit in commits]

    def store(
        self,
        filename,
        content,
        message: str | None = "",
        author=("", ""),
        mode="w",
    ):
        if message is None:
            message = ""
        dirname = os.path.dirname(filename)
        if dirname != "":
            os.makedirs(
                os.path.join(self.path, dirname), mode=0o775, exist_ok=True
            )
        # store file on filesystem
        with open(os.path.join(self.path, filename), mode) as f:
            f.write(content)
        # check if file has changed
        diff = self.repo.index.diff(None, paths=filename)
        if len(diff) == 0 and filename not in self.repo.untracked_files:
            return False
        # add and commit to git
        index = self.repo.index
        index.add([filename])
        actor = git.Actor(author[0], author[1])
        index.commit(message, author=actor)

        # auto-push after storing file
        repo_manager = get_repo_manager()
        if repo_manager:
            repo_manager.auto_push_if_enabled()

        return True

    def commit(self, filenames, message="", author=("", ""), no_add=False):
        index = self.repo.index
        # add and commit to git
        if no_add == False:
            try:
                index.add(filenames)
            except Exception:
                raise StorageError(
                    "index.add {} in commit failed.".format(filenames)
                )
        actor = git.Actor(author[0], author[1])
        index.commit(message, author=actor)

        # auto-push after commit
        repo_manager = get_repo_manager()
        if repo_manager:
            repo_manager.auto_push_if_enabled()

    def revert(self, revision, message="", author=("", "")):
        actor = git.Actor(author[0], author[1])
        try:
            self.repo.git.revert(revision, "--no-commit")
        except git.exc.GitCommandError:
            try:
                self.repo.git.revert("--abort")
            except git.exc.GitCommandError:
                pass
            raise StorageError("Revert failed.")

        actor = git.Actor(author[0], author[1])
        self.repo.index.commit(message, author=actor)

        # auto-push after revert
        repo_manager = get_repo_manager()
        if repo_manager:
            repo_manager.auto_push_if_enabled()

    def diff(self, rev_a, rev_b):
        # https://docs.python.org/2/library/difflib.html
        return self.repo.git.diff(rev_a, rev_b)

    def delete(self, filename, message=None, author=("", "")):
        if not type(filename) == list:
            filename = [filename]
        # make sure we only try to delete what exists
        filename_remove = [
            f for f in filename if self.exists(f) and not self.isdir(f)
        ]
        filename_remove += [
            d
            for d in filename
            if self.exists(d) and self.isdir(d) and not self.isemptydir(d)
        ]
        # remove empty directories via os
        empty_dirs = [
            d
            for d in filename
            if self.exists(d) and self.isdir(d) and self.isemptydir(d)
        ]
        for dirname in empty_dirs:
            os.rmdir(os.path.join(self.path, dirname))

        # or this will raise an exception
        self.repo.index.remove(filename_remove, working_tree=True, r=True)
        actor = git.Actor(author[0], author[1])
        if message is None:
            message = "Deleted {}.".format(filename_remove)
        self.repo.index.commit(message, author=actor)

        # auto-push after delete
        repo_manager = get_repo_manager()
        if repo_manager:
            repo_manager.auto_push_if_enabled()

    def rename(
        self,
        old_filename,
        new_filename,
        message=None,
        author=None,
        no_commit=False,
    ):
        if self.exists(new_filename):
            raise StorageError(
                f'The filename "{new_filename}" already exist. Please choose a new filename.'
            )
        # make sure the target directory exists
        dirname = os.path.dirname(new_filename)
        if dirname != "":
            os.makedirs(
                os.path.join(self.path, dirname), mode=0o775, exist_ok=True
            )
        try:
            self.repo.git.mv(old_filename, new_filename)
        except Exception as e:
            raise StorageError(
                "Renaming {} to {} failed: {}.".format(
                    old_filename, new_filename, e
                )
            )
        if message is None:
            message = "{} renamed to {}.".format(old_filename, new_filename)
        if not no_commit:
            self.commit([new_filename], message, author, no_add=True)

    def list(self, p=None, depth=None, exclude=[]):
        excludes = [".git"] + exclude
        # full path to search
        if p is not None:
            if os.path.isabs(p):
                raise ValueError("p must not be an absolute path")
            # That would break os.path.join():
            # If a component is an absolute path, all previous components are
            # thrown away and joining continues from the absolute path component.
            fullpath = os.path.normpath(os.path.join(self.path, p))
        else:
            fullpath = self.path
        # regexp to strip the root path from any path
        striproot = re.compile(r"^{}\/?".format(re.escape(fullpath)))
        # initialize empty results
        result_files, result_directories = [], []
        # walk the path
        for root, dirs, files in os.walk(fullpath):
            root = striproot.sub("", root)
            # check the depth
            if depth is not None:
                d = len(split_path(root))
                if d > depth:
                    continue
            # filter directories
            dirs[:] = [d for d in dirs if d not in excludes]
            # collect files
            for file in files:
                # add the root and all subdirectories
                fn = os.path.join(root, file)
                result_files.append(fn)
            # collect directories
            for dir in dirs:
                dn = os.path.join(root, dir)
                result_directories.append(dn)

        return sorted(result_files), sorted(result_directories)

    def show_commit(self, revision):
        try:
            commit = self.repo.commit(revision)
        except git.exc.BadName as e:
            raise StorageError(f"No commit found for ref {revision}")
        # fetch metadata
        metadata = self._get_metadata_of_commit(commit)
        # get diff via 'git show'
        diff = self.repo.git.show(revision, format="%b")
        return metadata, diff

    def get_parent_revision(self, filename, revision):
        """
        Walk the log for the given file to find the revision of the commit before the given one.
        """
        log = self.log(filename)
        for i, entry in enumerate(log):
            if entry['revision'] == revision:
                try:
                    return log[i + 1]['revision']
                except IndexError:
                    raise StorageNotFound
        raise StorageNotFound

    def get_filename_at_revision(self, current_filename, revision):
        """
        Get the filename that was used at a specific revision.
        """
        try:
            # get the full log with --follow to understand the rename chain
            full_log = self.repo.git.log(
                "--follow",
                "--name-only",
                "-z",
                "--format=format:%H",
                "--",
                current_filename,
            )

            if not full_log.strip():
                return current_filename

            entries = [
                entry
                for entry in full_log.strip('\x00').split('\x00\x00')
                if entry
            ]

            for entry in entries:
                # format: "commit_hash\nfilename"
                lines = entry.strip('\x00').split('\n')
                if len(lines) >= 2:
                    entry_revision = lines[0]
                    entry_filename = lines[1]

                    if entry_revision.startswith(
                        revision
                    ) or revision.startswith(entry_revision[:6]):
                        return entry_filename

            return current_filename

        except git.exc.GitCommandError as e:
            return current_filename


storage = None
