from git import Repo

_repo = None


def git_repo():
    global _repo
    if not _repo:
        _repo = Repo()
    return _repo
