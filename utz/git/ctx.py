from git import Repo
from utz import contextmanager, git, run


@contextmanager
def txn(msg=None):
    '''Contextmanager that creates a synthetic merge with __enter__- and __exit__-time HEADs as parents, and tree (and
    message, by default) of the latter.'''
    prv = git.sha()
    yield
    cur = git.sha()
    if cur == prv:
        return

    if msg is None:
        msg = git.msg()
    elif isinstance(msg, str):
        pass
    elif callable(msg):
        msg = msg(prv, cur)
    else:
        raise ValueError(f'Invalid msg: {msg}')

    tree = Repo().tree().hexsha
    run('git','commit-tree',tree,'-p',prv,'-p',cur,'-m',msg)
