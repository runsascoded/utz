"""Tests for utz.version module."""

from pathlib import Path
from tempfile import TemporaryDirectory

from utz import line, match, run
from utz.git.status import is_dirty
from utz.version import VERSION_TAG_REGEX, pkg_version, pkg_version_with_git


def repo_sha() -> str:
    return line('git', 'rev-parse', 'HEAD')


def dirty_suffix() -> str:
    return '.dirty' if is_dirty() else ''


def test_parse_version():
    def parse(version):
        return match(VERSION_TAG_REGEX, version).groupdict()

    assert parse('0.1.2') == { 'version': '0.1.2', 'base': '0.1.2', 'commits_ahead': None, 'rc': None, 'sha': None, }
    assert parse('0.1.23r1') == { 'version': '0.1.23r1', 'base': '0.1.23', 'commits_ahead': None, 'rc': 'r1', 'sha': None, }
    assert parse('0.1.23rc45') == { 'version': '0.1.23rc45', 'base': '0.1.23', 'commits_ahead': None, 'rc': 'rc45', 'sha': None, }

    v = line('git','describe','--tags','e4282e1')
    assert v == 'v0.3.7rc1-4-ge4282e1'
    assert parse(v) == { 'version': '0.3.7rc1-4-ge4282e1', 'base': '0.3.7', 'commits_ahead': '4', 'rc': 'rc1', 'sha': 'e4282e1', }


def test_pkg_version():
    assert pkg_version('python-dateutil') == '2.9.0'


def test_pkg_version_with_git_basic():
    """Test basic version with git hash (7-char by default)."""
    version = pkg_version_with_git(pkg_version="1.0.0")
    assert version == f"1.0.0+git.{repo_sha()[:7]}{dirty_suffix()}"


def test_pkg_version_without_git():
    """Test plain version without git info."""
    version = pkg_version_with_git(pkg_version="1.0.0", include_git=False)
    assert version == "1.0.0"


def test_pkg_version_full_hash():
    """Test version with full 40-char git hash."""
    version = pkg_version_with_git(pkg_version="1.0.0", short_hash=False)
    assert version == f"1.0.0+git.{repo_sha()}{dirty_suffix()}"


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
    """Test that dirty flag is appended iff repo is dirty."""
    version = pkg_version_with_git(pkg_version="1.0.0", include_dirty=True)
    assert version == f"1.0.0+git.{repo_sha()[:7]}{dirty_suffix()}"


def test_pkg_version_no_dirty():
    """Test that dirty flag is not included when include_dirty=False."""
    version = pkg_version_with_git(pkg_version="1.0.0", include_dirty=False)
    assert version == f"1.0.0+git.{repo_sha()[:7]}"


def test_pkg_version_fallback_on_error():
    """Test graceful fallback when git operations fail."""
    # Pass a non-existent cwd to trigger error
    version = pkg_version_with_git(
        pkg_version="1.0.0",
        cwd="/nonexistent/path/that/does/not/exist"
    )
    # Should fall back to plain version
    assert version == "1.0.0"
