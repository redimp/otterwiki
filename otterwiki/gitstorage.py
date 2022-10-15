#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import re
import git
from datetime import datetime
from pprint import pprint
from otterwiki.util import split_path
import pathlib
import os
import typing

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
        try:
            self.repo = git.Repo(self.path)
        except git.InvalidGitRepositoryError:
            raise StorageError(
                "No valid git repository in '{}'. Did you run 'git init'?".format(
                    self.path
                )
            )

    def exists(self, filename):
        return os.path.exists(os.path.join(self.path, filename))

    def load(self, filename, mode="r", revision=None):
        if revision is not None:
            try:
                content = self.repo.git.show("{}:{}".format(revision, filename))
                if mode == "rb":
                    content = content.encode("utf8", "surrogateescape")
            except git.exc.GitCommandError as e:
                raise StorageNotFound
            return content
        try:
            with open(os.path.join(self.path, filename), mode=mode) as f:
                content = f.read()
        except (IOError, FileNotFoundError) as e:
            raise StorageNotFound("{} not found.".format(filename))
        return content

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
            metadata["author_name"] = metadata["author_name"].replace("<>", "").strip()
        return metadata

    def _get_commit(self, filename, revision):
        commit = None
        if revision is None:
            try:
                commit = list(self.repo.iter_commits(paths=filename, max_count=1))[0]
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
            commits = self.repo.blame(revision, filename)
        except (ValueError, IndexError, git.exc.GitCommandError):
            raise StorageNotFound
        # initialize data and helper
        blamedata = []
        metadata_cache = {}
        n = 1
        for commit, lines in commits:
            try:
                metadata = metadata_cache[commit]
            except KeyError:
                metadata = self._get_metadata_of_commit(commit)
                metadata_cache[commit] = metadata
            for line in lines:
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

    def _get_metadata_of_log(self, logentry):
        logentry = logentry.split("\n")
        # Get revision
        revision = re.findall(r"commit ([a-z0-9]*)", logentry[0])[0]
        # Check if a offset for entries is necessary
        offset = 0
        if logentry[1].startswith("Merge:"):
            offset = 1
        # Find author data
        author_info = re.findall(r"Author: ([^\<]*) <([^\>]*)>", logentry[offset + 1])[
            0
        ]
        author_name = author_info[0]
        author_email = author_info[1]
        # Get and convert Datetime
        datetime_str = re.findall("Date: (.*)", logentry[offset + 2])[0].strip()
        datetime_obj = datetime.strptime(datetime_str, "%a %b %d %H:%M:%S %Y %z")
        # Get commit msg
        message = "\n".join([x.strip() for x in logentry[offset + 4 : -2]])

        files = logentry[-1].split("\x00")

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

    def log(self, filename=None):
        if filename is None:
            try:
                rawlog = self.repo.git.log("--name-only", "-z")
            except (git.exc.GitCommandError):
                return []
        else:
            try:
                rawlog = self.repo.git.log("--name-only", "-z", "--follow", filename)
            except (git.exc.GitCommandError):
                raise StorageNotFound

        rawlog = rawlog.strip("\x00").split("\x00\x00")
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

    def store(self, filename, content, message="", author=None, mode="w"):
        if message is None:
            message = ""
        dirname = os.path.dirname(filename)
        if dirname != "":
            os.makedirs(os.path.join(self.path, dirname), mode=0o777, exist_ok=True)
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
        return True

    def commit(self, filenames, message="", author=None):
        index = self.repo.index
        # add and commit to git
        index.add(filenames)
        actor = git.Actor(author[0], author[1])
        index.commit(message, author=actor)

    def revert(self, revision, message="", author=None):
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

    def diff(self, filename, rev_a, rev_b):
        # https://docs.python.org/2/library/difflib.html
        return self.repo.git.diff(rev_a, rev_b, filename)

    def delete(self, filename, message=None, author=None):
        if not type(filename) == list:
            filename=[filename]
        # make sure we only try to delete what exists
        filename = [f for f in filename if self.exists(f)]
        # or this will raise an exception
        self.repo.index.remove(filename, working_tree=True, r=True)
        actor = git.Actor(author[0], author[1])
        if message is None:
            message = "Deleted {}.".format(filename)
        self.repo.index.commit(message, author=actor)

    def rename(
        self, old_filename, new_filename, message=None, author=None, no_commit=False
    ):
        if self.exists(new_filename):
            raise StorageError(f'The filename "{new_filename}" already exist. Please choose a new filename.')

        try:
            self.repo.git.mv(old_filename, new_filename)
        except Exception:
            raise StorageError(
                "Renaming {} to {} failed.".format(old_filename, new_filename)
            )
        if message is None:
            message = "{} renamed to {}.".format(old_filename, new_filename)
        if not no_commit:
            self.commit([new_filename], message, author)

    def list(self, p=None, depth=None, exclude=[]):
        fullpath = self.path
        excludes = [".git"] + exclude
        # full path to search
        if p is not None:
            fullpath = os.path.join(fullpath, p)
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

    def _recurse_folders(self, s, level, fullpath, stop_depth):
        '''Recurisvely build up a list of files and folders until a specified depth.
        This will generate a flat list. Example:
        [
            (1, 'a page', 'a page.md'),
            (1, 'an important wiki page', 'an important wiki page.md'),
            (1, 'home', 'home.md'),
            (1, 'organizational things', 'organizational things.md')
        ]
        Each item in the tuple is:
        depth (starting at 1)
        url path from root (also title)
        '''
        excludes = [".git"] #+ exclude

        level += 1

        if stop_depth < level:
            return s

        for root, dirs, files in os.walk(fullpath):

            dirs.sort()
            files.sort()

            for dir in dirs:
                if all([
                    f'{dir}.md' not in files,  # This will ignore the attachments
                    dir not in excludes,  # ignore excludes
                    not str(dir).startswith('.') # ignore hidden dirs
                ]):
                    title = dir.replace(".md", "")

                    # Add into TOC
                    s.append((level, title, dir))
                    _fp = os.path.join(root, dir)
                    s = self._recurse_folders(s, level, _fp, stop_depth,)

            for file in files:
                if all([
                    file not in excludes,
                    not str(file).startswith('.')
                ]):
                    title = file.replace(".md", "")
                    # Add into TOC
                    s.append((level, title, file ))

            break

        return s

    def toc(self, p=None, depth=1) -> typing.List[typing.Tuple[int, str]]:
        '''
        Generate a toc from a given path

        :param: p = path in which to generate the toc from, whill default to root path
        :param: depth = how deep to recurse (helpful for when sub folders are implemented)
        '''
        fullpath = self.path

        # regexp to strip the root path from any path
        striproot = re.compile(r"^{}\/?".format(re.escape(fullpath)))
        # I took this from the index function, but I don't think we need it?

        # full path to search
        if p is not None:
            # This is not yet implemented, but the idea is to generate
            # a toc from a given path
            fullpath = os.path.join(fullpath, p)

        s = []
        r = self._recurse_folders(s, 0, fullpath, depth)
        return r

storage = None
