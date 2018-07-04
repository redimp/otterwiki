#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import re
import git

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
        self.path = path
        if initialize:
            self.repo = git.Repo.init(self.path)
        try:
            self.repo = git.Repo(self.path)
        except git.InvalidGitRepositoryError:
            raise StorageError("No valid git repository in '{}'. Did you run 'git init'?".format(self.path))

    def exists(self, filename):
        return os.path.exists(os.path.join(self.path, filename))

    def load(self, filename, mode='r', revision=None):
        if revision is not None:
            try:
                content = self.repo.git.show('{}:{}'.format(revision, filename))
                if mode=="rb":
                    content = content.encode('utf8','surrogateescape')
            except git.exc.GitCommandError:
                raise StorageNotFound
            return content
        try:
            with open(os.path.join(self.path, filename), mode=mode) as f:
                content = f.read()
        except (IOError, FileNotFoundError):
            raise StorageNotFound
        return content

    def _get_metadata_of_commit(self, commit):
        metadata = {
            'revision-full' : commit.hexsha,
            'revision' : commit.hexsha[0:6], # FIXME: Too slow, self.repo.git.rev_parse(commit.hexsha, short=6),
            'datetime' : commit.authored_datetime,
            'author_name' : commit.author.name,
            'author_email' : commit.author.email,
#            'author' : '{} {}'.format(commit.author.name, commit.author.email),
            'message' : commit.message,
            'files' : {}, # FIXME: Too slow: commit.stats.files,
        }
        # this is a workaround
        if commit.author.email is None:
            metadata['author_name'] = metadata['author_name'].replace("<>","").strip()
        return  metadata

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

    def metadata(self, filename, revision=None):
        #sha = repo.head.object.hexsha
        #short_sha = repo.git.rev_parse(sha, short=6)
        commit = self._get_commit(filename, revision)

        return self._get_metadata_of_commit(commit)

    def log(self, filename=None):
        # TODO
        # check if parsing
        #   repo.git.log("--name-only", "-z", filename).strip('\x00').split('\x00')
        # is faster ...
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


    def store(self, filename, content, message="", author=None, mode='w'):
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
            self.repo.git.revert("--abort")
            raise StorageError("Revert failed.")

        actor = git.Actor(author[0], author[1])
        self.repo.index.commit(message, author=actor)

    def diff(self, filename, rev_a, rev_b):
        # https://docs.python.org/2/library/difflib.html
        return self.repo.git.diff(rev_a, rev_b, filename)

    def delete(self, filename, message=None, author=None):
        self.repo.index.remove([filename], working_tree=True)
        actor = git.Actor(author[0], author[1])
        if message is None:
            message = "Deleted {}.".format(filename)
        self.repo.index.commit(message, author=actor)

    def rename(self, old_filename, new_filename, message=None, author=None):
        try:
            self.repo.git.mv(old_filename, new_filename)
        except Exception:
            raise StorageError("Renaming {} to {} failed.".format(old_filename, new_filename))
        if message is None:
            message = "{} renamed to {}.".format(old_filename, new_filename)
        self.commit([new_filename], message, author)

    def list_files(self, p=None):
        fullpath = self.path
        excludes = ['.git']
        if p is not None:
            fullpath = os.path.join(fullpath, p)
        l = []
        striproot = re.compile(r"^{}\/?".format(re.escape(fullpath)))
        for root, dirs, files in os.walk(fullpath):
            dirs[:] = [d for d in dirs if d not in excludes]
            for file in files:
                # add the root and all subdirectories
                fn = os.path.join(root,file)
                # and remove the root again
                fn = striproot.sub("", fn)
                l.append(fn)
        return sorted(l)

storage = None
