from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from re import fullmatch
from subprocess import CalledProcessError

from .proc import line


VERSION_TAG_REGEX = r"v?(?P<version>(?P<base>\d+\.\d+\.\d+)(?P<rc>(?:r|c|rc|a|b)\d+)?(?:-(?P<commits_ahead>\d+)-g(?P<sha>[0-9a-f]{6,}))?)"


def git_version():
    """Infer version from git tag of the form "v_._._"; otherwise, return current Git commit SHA"""
    try:
        tag = line('git', 'describe', '--tags', 'HEAD')
        m = fullmatch(VERSION_TAG_REGEX, tag)
        if not m:
            raise ValueError('Unrecognized tag: %s' % tag)
        version = m['version']
    except CalledProcessError:
        version = line('git', 'log', '--format=%h', '-n1')

    return version


def pkg_version(name: str = None):
    try:
        return version(name)
    except PackageNotFoundError:
        if name:
            raise
        return git_version()


def pkg_version_with_git(
    pkg_version: str = None,
    pkg_name: str = None,
    include_git: bool = True,
    include_dirty: bool = True,
    short_hash: bool = True,
    cwd: str = None,
) -> str:
    """Get package version with optional git hash suffix.

    Args:
        pkg_version: Explicit version string (e.g., "0.1.1")
        pkg_name: Package name for importlib.metadata lookup (if pkg_version not provided)
        include_git: If True, append git hash (default: True)
        include_dirty: If True, append ".dirty" suffix for uncommitted changes (default: True)
        short_hash: If True, use 7-char hash; if False, use full 40-char hash (default: True)
        cwd: Directory to run git commands in (default: auto-detect from caller's package)

    Returns:
        Version string in one of these formats:
        - "0.1.1" (if include_git=False or git not available)
        - "0.1.1+git.abc1234" (clean working tree)
        - "0.1.1+git.abc1234.dirty" (uncommitted changes)
        - "0.1.1+git.abc1234567890abcdef1234567890abcdef12" (full hash if short_hash=False)

    Examples:
        >>> # In your package's __init__.py:
        >>> from utz.version import pkg_version_with_git
        >>>
        >>> __version__ = "0.1.1"
        >>>
        >>> def get_version(include_git=True):
        ...     return pkg_version_with_git(pkg_version=__version__, include_git=include_git)
        >>>
        >>> # Usage:
        >>> import mypackage
        >>> mypackage.get_version()
        '0.1.1+git.abc1234'
        >>> mypackage.get_version(include_git=False)
        '0.1.1'
        >>> mypackage.__version__
        '0.1.1'

    Notes:
        - Falls back to plain version if git is not available or fails
        - If neither pkg_version nor pkg_name provided, tries git_version()
        - The "+git.HASH" format follows PEP 440 local version identifier conventions
    """
    # Get base version
    if pkg_version is None:
        if pkg_name:
            try:
                pkg_version = version(pkg_name)
            except PackageNotFoundError:
                pkg_version = git_version()
        else:
            pkg_version = git_version()

    # Return plain version if git info not requested
    if not include_git:
        return pkg_version

    # Try to get git info
    try:
        # Determine working directory
        if cwd is None:
            # Try to auto-detect from caller's package directory
            import inspect
            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_file = frame.f_back.f_globals.get('__file__')
                if caller_file:
                    # Walk up from caller's file to find .git
                    current = Path(caller_file).resolve().parent
                    while current != current.parent:
                        if (current / '.git').exists():
                            cwd = str(current)
                            break
                        current = current.parent

        # Get git hash
        hash_format = '--short=7' if short_hash else ''
        git_cmd = ['git', 'rev-parse']
        if hash_format:
            git_cmd.append(hash_format)
        git_cmd.append('HEAD')

        kwargs = {}
        if cwd:
            kwargs['cwd'] = cwd

        git_hash = line(*git_cmd, **kwargs)

        # Check if dirty
        dirty_suffix = ''
        if include_dirty:
            from .git.status import is_dirty
            if is_dirty(cwd=cwd):
                dirty_suffix = '.dirty'

        return f"{pkg_version}+git.{git_hash}{dirty_suffix}"

    except Exception:
        # Fall back to plain version if anything goes wrong
        return pkg_version
