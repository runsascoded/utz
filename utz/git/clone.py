
from contextlib import contextmanager
from os.path import basename
from sys import stderr
from typing import Iterable

import utz
from utz import check, git, line, match, now, print_exc, run, tmpdir


@contextmanager
def tmp(
    url,
    *clone_args,
    branch=None,
    ref=None,
    submodules=True,
    push=False,
    pull=False,
    cd=True,
    name=None,
    bare=False,
    dir=None,
    **run_kwargs,
):
    '''contextmanager for creating a Git repo in a temporary directory, and optionally cd'ing into it and upstreaming
    commits from it

    - `url`: local or remote path to Git repository to be cloned
    - `clone_args` (List[str]): passed directly to `git clone`
    - `branch`: Git branch to operate on inside temporary clone (by default, inherit from origin)
    - `ref`: if `branch` doesn't already exist, reset it to this ref. Note: if `ref` is omitted, `branch` must already
        exist in the remote! If `ref` is set and `branch` isn't, a temporary/nonced branch name will be used.
    - `submodules`: recursively clone submodules (`git clone --recurse-submodules`)
    - `push` (str | bool | List[str]): run a `git push` after `yield`ing; `str` or `List[str]` serve as arguments to
        `git push`
    - `pull` (bool): upstream changes post-`yield` by `cd`ing into the origin directory (must be a local dir, otherwise
        use `push`) and running a `git pull` from this temporary clone
    - `cd` (bool): move into the temporary clone dir before `yield`ing
    - `name`: basename for the temporary clone directory (defaults to basename of `url`)
    - `bare`: clone a bare repository
    '''

    name = name or basename(url)
    if name.endswith('.git'): name = name[:-len('.git')]
    with tmpdir(name, dir=dir) as repo_dir:
        cmd = ['git','clone']
        if submodules: cmd += ['--recurse-submodules']
        if bare: cmd += ['--bare']
        if branch and not ref:
            # branch must already exist and we want to clone and work on it
            cmd += ['-b',branch]
        cmd += clone_args
        cmd += [ url, repo_dir, ]
        run(*cmd, **run_kwargs)
        if ref:
            with utz.cd(repo_dir):
                if ref is True:
                    ref = git.branch.current()

                if not branch:
                    branch = f'tmp-{now("short")}'

                if git.branch.exists(branch):
                    make_branch = False
                else:
                    make_branch = True

                if make_branch:
                    if bare:
                        run('git','branch',branch,ref)
                        run('git','symbolic-ref','HEAD',f'refs/heads/{branch}')
                    else:
                        run('git','checkout','-b',branch,ref)

                if cd:
                    yield repo_dir
        if cd:
            if not ref:
                # if `checkout or init`, we've already cd'd and yielded above
                with utz.cd(repo_dir):
                    yield repo_dir
        else:
            yield repo_dir

        # optionally cd into upstream `url` dir (assumed to be a local directory if `pull` is set) and pull changes
        # from the temporary `repo_dir`
        if pull:
            with utz.cd(url):
                if not branch: branch = git.branch.current()
                run('git','fetch',repo_dir)
                try:
                    ref_line = line('git','ls-remote',repo_dir,f'refs/heads/{branch}')
                    m = match(
                        '(?P<sha>[0-9a-f]{40})\s+refs/heads/%s' % branch,
                        ref_line,
                    )
                    if m:
                        sha = m['sha']
                    else:
                        raise RuntimeError(f'Unrecognized ls-remote line: {ref_line}')
                except Exception as e:
                    stderr.write('%s\n' % f'Error fetching branch {branch} from remote {repo_dir}')
                    print_exc()
                    sha = git.sha('FETCH_HEAD')

                if not check('git','merge','-m','\n'.join([f'Merge {branch} from tmpdir','',repo_dir]),sha):
                    tmp_branch = f'conflict-{sha}'
                    run('git','branch',tmp_branch,sha)
                    stderr.write('Pulling from %s failed, aborting merge, saving to %s\n' % (repo_dir, tmp_branch))
                    run('git','merge','--abort')

        # optionally push back upstream
        if push:
            with utz.cd(repo_dir):
                cmd = ['git','push',]
                if isinstance(push, str):
                    cmd += ['origin',f'{push}:{push}',]
                elif isinstance(push, Iterable):
                    cmd += push
                elif push is True:
                    if branch:
                        cmd += ['origin',f'{branch}:{branch}',]
                run(*cmd)
