from git import Repo
from utz import contextmanager, git, line, run


@contextmanager
def txn(msg=None, start=None,):
    '''Contextmanager that creates a synthetic merge with __enter__- and __exit__-time HEADs as parents, and tree (and
    message, by default) of the latter.'''
    start = start or git.sha()
    yield
    end = git.sha()
    if end == start:
        return

    if msg is None:
        msg = git.msg()
    elif isinstance(msg, str):
        pass
    elif callable(msg):
        msg = msg(start, end)
    else:
        raise ValueError(f'Invalid msg: {msg}')

    tree = Repo().tree().hexsha
    sha = line('git','commit-tree',tree,'-p',start,'-p',end,'-m',msg)
    run('git','reset',sha)
