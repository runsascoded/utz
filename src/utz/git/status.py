"""Git status utilities."""

from subprocess import CalledProcessError

from ..proc import run


def is_dirty(cwd: str = None) -> bool:
    """Check if git working tree has uncommitted changes.

    Args:
        cwd: Directory to run git command in (default: current directory)

    Returns:
        True if there are uncommitted changes (staged or unstaged), False otherwise

    Examples:
        >>> from utz.git.status import is_dirty
        >>> is_dirty()
        False
        >>> # After editing a file
        >>> is_dirty()
        True

    Implementation:
        Uses `git diff-index --quiet HEAD --` which exits with:
        - 0 if clean
        - 1 if dirty
        - 128 if no HEAD (empty repo)
    """
    try:
        kwargs = {}
        if cwd:
            kwargs['cwd'] = cwd
        run(['git', 'diff-index', '--quiet', 'HEAD', '--'], **kwargs)
        return False
    except CalledProcessError as e:
        if e.returncode == 1:
            return True
        if e.returncode == 128:
            # No HEAD (empty repo with no commits)
            return False
        raise
