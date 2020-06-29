try:
    from git import Repo, Git
    from functools import partial
    Repo = partial(Repo, search_parent_directories=True)
except ImportError:
    pass
