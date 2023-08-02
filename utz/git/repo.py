_repo = None


def git_repo():
    global _repo
    if not _repo:
        from git import Repo
        _repo = Repo()
    return _repo
