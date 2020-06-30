try:
    from git import Repo, Git
    from functools import partial
    Repo = partial(Repo, search_parent_directories=True)
except ImportError:
    pass


from .remote import push
from .process import run


def checkout(branch, ref=None, exist=False):
    if exist:
        run('git','checkout',branch,ref)
    else:
        run('git','checkout','-B',branch,ref)


def merge(ref, msg=None):
    cmd = ['git','merge','--no-edit']
    if msg: cmd += ['-m',msg]
    run(cmd)


def commit(msg=None, all=False, amend=False):
    cmd = ['git','commit']
    if amend: cmd += ['--amend']
    if all: cmd += ['-a']
    if msg: cmd += ['-m',msg]
    run(cmd)
