from ..proc import line

_repo = None


def git_repo():
    global _repo
    if not _repo:
        from git import Repo
        _repo = Repo()
    return _repo


def root():
    """Get the root directory of the current git repository."""
    return line('git', 'rev-parse', '--show-toplevel')
