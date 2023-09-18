# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Git repository class and helper utilities."""

import logging
from pathlib import Path

import pygit2

from .errors import GitError

logger = logging.getLogger(__name__)


def is_repo(path: Path) -> bool:
    """Check if a directory is a git repo.

    :param path: filepath to check

    :returns: True if path is a git repo.

    :raises GitError: if git fails while checking for a repository
    """
    # `path.absolute().parent` prevents pygit2 from checking parent directories
    try:
        return bool(
            pygit2.discover_repository(str(path), False, str(path.absolute().parent))
        )
    except pygit2.GitError as error:
        raise GitError(
            f"Could not check for git repository in {str(path)!r}."
        ) from error


class GitRepo:
    """Git repository class."""

    def __init__(self, path: Path) -> None:
        """Initialize a git repo.

        If a git repo does not already exist, a new repo will be initialized.

        :param path: filepath of the repo

        :raises FileNotFoundError: if the directory does not exist
        :raises GitError: if git is not installed or the repo cannot be initialized
        """
        self.path = path

        if not path.is_dir():
            raise FileNotFoundError(
                f"Could not initialize a git repository because {str(path)!r} does not "
                "exist or is not a directory."
            )

        if not is_repo(path):
            self._init_repo()

        self._repo = pygit2.Repository(path)

    def add_all(self) -> None:
        """Add all changes from the working tree to the index.

        :raises GitError: if the changes could not be added
        """
        try:
            self._repo.index.add_all()
            self._repo.index.write()
        except pygit2.GitError as error:
            raise GitError(
                f"Could not add changes for the git repository in {str(self.path)!r}"
            ) from error

    def commit(self, message: str = "auto commit") -> None:
        """Commit changes to the repo.

        :param message: the commit message

        :raises GitError: if the commit could not be created
        """
        try:
            tree = self._repo.index.write_tree()
        except pygit2.GitError as error:
            raise GitError(
                f"Could not create a tree for the git repository in {str(self.path)!r}."
            ) from error

        author = pygit2.Signature("auto commit", "auto commit")

        try:
            # pylint: disable=line-too-long
            # todo: figure out if `--no-gpg-sign` is required to avoid this problem:
            # https://github.com/snapcore/snapcraft/pull/2837/commits/987b39053429b23b829966837bf6b8c8dd3b9e28
            self._repo.create_commit("HEAD", author, author, message, tree, [])
        except pygit2.GitError as error:
            raise GitError(
                "Could not create a commit for the git repository "
                f"in {str(self.path)!r}."
            ) from error

    def is_clean(self) -> bool:
        """Check if the repo is clean.

        :returns: True if the repo is clean.

        :raises GitError: if git fails while checking if the repo is clean
        """
        try:
            # for a clean repo, `status()` will return an empty dict
            return not bool(self._repo.status())
        except pygit2.GitError as error:
            raise GitError(
                f"Could not check if the git repository in {str(self.path)!r} is clean."
            ) from error

    def _init_repo(self) -> None:
        """Initialize a git repo.

        :raises GitError: if the repo cannot be initialized
        """
        try:
            pygit2.init_repository(self.path)
        except pygit2.GitError as error:
            raise GitError(
                f"Could not initialize a git repository in {str(self.path)!r}."
            ) from error

    def push_url(self, remote_url: str, refspec: str = "HEAD") -> None:
        """Push a refspec to a remote url.

        :param remote_url: the remote repo URL to push to
        :param refspec: git refspec to push

        :raises GitError: if the refspec does not exist or the refspec cannot be pushed
        """
        try:
            reference = self._repo.lookup_reference_dwim(refspec).name
        # raises a KeyError if the ref does not exist and a GitError for git errors
        except (pygit2.GitError, KeyError) as error:
            raise GitError(
                f"Could not resolve reference {refspec!r} for the git repository in "
                f"{str(self.path)!r}."
            ) from error

        try:
            self._repo.remotes.create_anonymous(remote_url).push([reference])
        except pygit2.GitError as error:
            raise GitError(
                f"Could not push {refspec!r} to {remote_url!r} for the git "
                f"repository in {str(self.path)!r}."
            ) from error
