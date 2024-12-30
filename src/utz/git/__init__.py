from utz.proc import run

try:
    from git import Repo, Git, InvalidGitRepositoryError
    from functools import partial
    import os

    def make_repo(*args, exist_ok=False, search_parent_directories=True, gitignore=None, msg=None, **kwargs):
        load_kwargs = kwargs.copy()
        load_kwargs['search_parent_directories'] = search_parent_directories
        if exist_ok:
            try:
                return Repo(*args, **load_kwargs)
            except InvalidGitRepositoryError:
                repo = Repo.init(*args, **kwargs)
                if gitignore:
                    if isinstance(gitignore, str): gitignore = [ gitignore ]
                    gitignore_path = os.path.join(repo.working_dir, '.gitignore')
                    with open(gitignore_path, 'w') as f:
                        for line in gitignore:
                            f.write(line + '\n')
                    repo.git.add('.gitignore')
                    msg = msg or 'initial commit'
                    repo.git.commit('-m',msg)
                return repo
        else:
            return Repo(*args, **load_kwargs)
except ImportError:
    pass


from . import branch, clone, diff, head, remote, submodule
from .ctx import txn
from .head import fmt, sha
from .log import msg
from .remote import push, ls_remote, git_remote_sha
from .repo import git_repo
from .submodule import git_submodules


from ._checkout import Checkout
checkout = Checkout()


def merge(ref, msg=None, ff=None):
    cmd = ['git', 'merge', '--no-edit']

    if ff is True:
        cmd += ['--ff-only']
    elif ff is False:
        cmd += ['--no-ff']

    if msg:
        cmd += ['-m', msg]

    cmd += [ref]

    run(cmd)


def commit(msg=None, all=False, amend=False):
    cmd = ['git', 'commit']
    if amend: cmd += ['--amend']
    if all: cmd += ['-a']
    if msg: cmd += ['-m', msg]
    run(cmd)
