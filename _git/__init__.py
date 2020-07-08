try:
    from git import Repo, Git
    from functools import partial
    Repo = partial(Repo, search_parent_directories=True)
except ImportError:
    pass


from .remote import push
from ..process import run


from ._checkout import Checkout
checkout = Checkout()


def merge(ref, msg=None, ff=None):
    cmd = ['git','merge','--no-edit']

    if ff == True: cmd += ['--ff-only']
    elif ff == False: cmd += ['--no-ff']

    if msg: cmd += ['-m',msg]

    cmd += [ref]

    run(cmd)


def commit(msg=None, all=False, amend=False):
    cmd = ['git','commit']
    if amend: cmd += ['--amend']
    if all: cmd += ['-a']
    if msg: cmd += ['-m',msg]
    run(cmd)
