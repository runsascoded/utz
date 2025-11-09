"""Tests for utz.version module."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from utz import run
from utz.git.status import is_dirty
from utz.version import pkg_version_with_git


def test_pkg_version_with_git_basic():
    """Test basic version with git hash."""
    version = pkg_version_with_git(pkg_version="1.0.0")
    assert version.startswith("1.0.0+git.")
    # Should have 7-char hash by default
    assert len(version) >= len("1.0.0+git.") + 7


def test_pkg_version_without_git():
    """Test plain version without git info."""
    version = pkg_version_with_git(pkg_version="1.0.0", include_git=False)
    assert version == "1.0.0"


def test_pkg_version_full_hash():
    """Test version with full 40-char git hash."""
    version = pkg_version_with_git(pkg_version="1.0.0", short_hash=False)
    assert version.startswith("1.0.0+git.")
    # Should have full 40-char hash
    hash_part = version.split("+git.")[1].rstrip(".dirty")
    assert len(hash_part) == 40


def test_is_dirty_clean():
    """Test is_dirty on clean repo."""
    # This repo should be clean at test time (or dirty if we have uncommitted changes)
    # Just verify it returns a boolean
    result = is_dirty()
    assert isinstance(result, bool)


def test_is_dirty_with_temp_repo():
    """Test is_dirty on a temporary repo."""
    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Initialize a git repo
        run(['git', 'init'], cwd=tmpdir)
        run(['git', 'config', 'user.email', 'test@example.com'], cwd=tmpdir)
        run(['git', 'config', 'user.name', 'Test User'], cwd=tmpdir)

        # Empty repo (no HEAD) returns False
        assert not is_dirty(cwd=str(tmpdir))

        # Create and commit initial file to establish HEAD
        test_file = tmpdir / 'test.txt'
        test_file.write_text('hello')
        run(['git', 'add', 'test.txt'], cwd=tmpdir)
        run(['git', 'commit', '-m', 'initial'], cwd=tmpdir)

        # Clean repo should not be dirty
        assert not is_dirty(cwd=str(tmpdir))

        # Modify the file
        test_file.write_text('world')

        # Modified file counts as dirty
        assert is_dirty(cwd=str(tmpdir))

        # Stage the modified file
        run(['git', 'add', 'test.txt'], cwd=tmpdir)

        # Staged changes count as dirty
        assert is_dirty(cwd=str(tmpdir))

        # Commit the changes
        run(['git', 'commit', '-m', 'update'], cwd=tmpdir)

        # Clean again
        assert not is_dirty(cwd=str(tmpdir))


def test_pkg_version_dirty_detection():
    """Test that dirty flag is appended when repo is dirty."""
    # Get version with dirty detection
    version = pkg_version_with_git(pkg_version="1.0.0", include_dirty=True)

    # Should either end with hash or .dirty
    assert version.startswith("1.0.0+git.")

    # If our current repo is dirty, should have .dirty suffix
    if is_dirty():
        assert version.endswith(".dirty")


def test_pkg_version_no_dirty():
    """Test that dirty flag is not included when include_dirty=False."""
    version = pkg_version_with_git(pkg_version="1.0.0", include_dirty=False)
    assert not version.endswith(".dirty")
    assert version.startswith("1.0.0+git.")


def test_pkg_version_fallback_on_error():
    """Test graceful fallback when git operations fail."""
    # Pass a non-existent cwd to trigger error
    version = pkg_version_with_git(
        pkg_version="1.0.0",
        cwd="/nonexistent/path/that/does/not/exist"
    )
    # Should fall back to plain version
    assert version == "1.0.0"
