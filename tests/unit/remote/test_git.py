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


"""Tests for the pygit2 wrapper class."""

from pathlib import Path

import pygit2
import pytest

from snapcraft.remote import GitError, GitRepo, is_repo


def test_is_repo(new_dir):
    """Check if directory is a repo."""
    GitRepo(new_dir)

    assert is_repo(new_dir)


def test_is_not_repo(new_dir):
    """Check if a directory is not a repo."""
    assert not is_repo(new_dir)


def test_is_repo_path_only(new_dir):
    """Only look at the path for a repo."""
    Path("parent-repo/not-a-repo/child-repo").mkdir(parents=True)
    # create the parent and child repos
    GitRepo(Path("parent-repo"))
    GitRepo(Path("parent-repo/not-a-repo/child-repo"))

    assert is_repo(Path("parent-repo"))
    assert not is_repo(Path("parent-repo/not-a-repo"))
    assert is_repo(Path("parent-repo/not-a-repo/child-repo"))


def test_is_repo_error(new_dir, mocker):
    """Raise an error if git fails to check a repo."""
    mocker.patch("pygit2.discover_repository", side_effect=pygit2.GitError)

    with pytest.raises(GitError) as raised:
        assert is_repo(new_dir)

    assert raised.value.details == (
        f"Could not check for git repository in {str(new_dir)!r}."
    )


def test_init_repo(new_dir):
    """Initialize a GitRepo object."""
    repo = GitRepo(new_dir)

    assert is_repo(new_dir)
    assert repo.path == new_dir


def test_init_repo_no_directory(new_dir):
    """Raise an error if the directory is missing."""
    with pytest.raises(FileNotFoundError) as raised:
        GitRepo(new_dir / "missing")

    assert str(raised.value) == (
        "Could not initialize a git repository because "
        f"{str(new_dir / 'missing')!r} does not exist or is not a directory."
    )


def test_init_repo_not_a_directory(new_dir):
    """Raise an error if the path is not a directory."""
    Path("regular-file").touch()

    with pytest.raises(FileNotFoundError) as raised:
        GitRepo(new_dir / "regular-file")

    assert str(raised.value) == (
        "Could not initialize a git repository because "
        f"{str(new_dir / 'regular-file')!r} does not exist or is not a directory."
    )


def test_init_repo_error(new_dir, mocker):
    """Raise an error if the repo cannot be initialized."""
    mocker.patch("pygit2.init_repository", side_effect=pygit2.GitError)

    with pytest.raises(GitError) as raised:
        GitRepo(new_dir)

    assert raised.value.details == (
        f"Could not initialize a git repository in {str(new_dir)!r}."
    )


def test_add_all(new_dir):
    """Add all files."""
    repo = GitRepo(new_dir)
    Path("foo").touch()
    Path("bar").touch()
    repo.add_all()

    status = pygit2.Repository(new_dir).status()

    assert status == {
        "foo": pygit2.GIT_STATUS_INDEX_NEW,
        "bar": pygit2.GIT_STATUS_INDEX_NEW,
    }


def test_add_all_no_files_to_add(new_dir):
    """`add_all` should succeed even if there are no files to add."""
    repo = GitRepo(new_dir)
    repo.add_all()

    status = pygit2.Repository(new_dir).status()

    assert status == {}


def test_add_all_error(new_dir, mocker):
    """Raise an error if the changes could not be added."""
    mocker.patch("pygit2.Index.add_all", side_effect=pygit2.GitError)
    repo = GitRepo(new_dir)

    with pytest.raises(GitError) as raised:
        repo.add_all()

    assert raised.value.details == (
        f"Could not add changes for the git repository in {str(new_dir)!r}"
    )


def test_commit(new_dir):
    """Commit a file and confirm it is in the tree."""
    repo = GitRepo(new_dir)
    Path("test-file").touch()
    repo.add_all()

    repo.commit()

    # verify commit (the `isinstance` checks are to satsify pyright)
    commit = pygit2.Repository(new_dir).revparse_single("HEAD")
    assert isinstance(commit, pygit2.Commit)
    assert commit.message == "auto commit"
    assert commit.committer.name == "auto commit"
    assert commit.committer.email == "auto commit"

    # verify tree
    tree = commit.tree
    assert isinstance(tree, pygit2.Tree)
    assert len(tree) == 1

    # verify contents of tree
    blob = tree[0]
    assert isinstance(blob, pygit2.Blob)
    assert blob.name == "test-file"


def test_commit_write_tree_error(new_dir, mocker):
    """Raise an error if the tree cannot be created."""
    mocker.patch("pygit2.Index.write_tree", side_effect=pygit2.GitError)
    repo = GitRepo(new_dir)
    Path("test-file").touch()
    repo.add_all()

    with pytest.raises(GitError) as raised:
        repo.commit()

    assert raised.value.details == (
        f"Could not create a tree for the git repository in {str(new_dir)!r}."
    )


def test_commit_error(new_dir, mocker):
    """Raise an error if the commit cannot be created."""
    mocker.patch("pygit2.Repository.create_commit", side_effect=pygit2.GitError)
    repo = GitRepo(new_dir)
    Path("test-file").touch()
    repo.add_all()

    with pytest.raises(GitError) as raised:
        repo.commit()

    assert raised.value.details == (
        f"Could not create a commit for the git repository in {str(new_dir)!r}."
    )


def test_is_clean(new_dir):
    """Check if a repo is clean."""
    repo = GitRepo(new_dir)

    assert repo.is_clean()

    Path("foo").touch()

    assert not repo.is_clean()


def test_is_clean_error(new_dir, mocker):
    """Check if git fails when checking if the repo is clean."""
    mocker.patch("pygit2.Repository.status", side_effect=pygit2.GitError)
    repo = GitRepo(new_dir)

    with pytest.raises(GitError) as raised:
        repo.is_clean()

    assert raised.value.details == (
        f"Could not check if the git repository in {str(new_dir)!r} is clean."
    )


def test_push_url(new_dir):
    """Push a file to a remote url."""
    # create a local repo and make a commit
    Path("local-repo").mkdir()
    repo = GitRepo(Path("local-repo"))
    Path("local-repo/test-file").touch()
    repo.add_all()
    repo.commit()
    # create a bare remote repo
    Path("remote-repo").mkdir()
    remote = pygit2.init_repository(Path("remote-repo"), True)

    repo.push_url(f"file://{str(Path('remote-repo').absolute())}", "HEAD")

    # verify commit in remote (the `isinstance` checks are to satsify pyright)
    commit = remote.revparse_single("HEAD")
    assert isinstance(commit, pygit2.Commit)
    assert commit.message == "auto commit"
    assert commit.committer.name == "auto commit"
    assert commit.committer.email == "auto commit"

    # verify tree in remote
    tree = commit.tree
    assert isinstance(tree, pygit2.Tree)
    assert len(tree) == 1

    # verify contents of tree in remote
    blob = tree[0]
    assert isinstance(blob, pygit2.Blob)
    assert blob.name == "test-file"


def test_push_url_refspec_unknown_ref(new_dir):
    """Raise an error for an unknown refspec."""
    repo = GitRepo(new_dir)

    with pytest.raises(GitError) as raised:
        repo.push_url("test-url", "bad-refspec")

    assert raised.value.details == (
        "Could not resolve reference 'bad-refspec' for the git repository "
        f"in {str(new_dir)!r}."
    )


def test_push_url_refspec_git_error(mocker, new_dir):
    """Raise an error if git fails when looking for a refspec."""
    mocker.patch(
        "pygit2.Repository.lookup_reference_dwim",
        side_effect=pygit2.GitError,
    )
    repo = GitRepo(new_dir)

    with pytest.raises(GitError) as raised:
        repo.push_url("test-url", "bad-refspec")

    assert raised.value.details == (
        "Could not resolve reference 'bad-refspec' for the git repository "
        f"in {str(new_dir)!r}."
    )


def test_push_url_push_error(new_dir):
    """Raise an error when the refspec cannot be pushed."""
    repo = GitRepo(new_dir)
    Path("test-file").touch()
    repo.add_all()
    repo.commit()

    with pytest.raises(GitError) as raised:
        repo.push_url("bad-url", "HEAD")

    assert raised.value.details == (
        "Could not push 'HEAD' to 'bad-url' for the git repository "
        f"in {str(new_dir)!r}."
    )
