#!/usr/bin/env python

import re
from os import cpu_count
from typing import Callable, Tuple, Optional

import click
from git import Repo
from utz import process, DefaultDict, err
from utz.git.git_update_submodules import update_submodules, verbose_flag, no_reset_flag


def parallel(elems, fn: Callable, n_jobs: int = 0):
    try:
        from joblib import Parallel, delayed
        if not n_jobs:
            n_jobs = cpu_count()
        p = Parallel(n_jobs=n_jobs)
        return p(delayed(fn)(elem) for elem in elems)
    except ImportError:
        return [ fn(elem) for elem in elems ]


@click.command('git-meta-branch-update')
@click.option('-P', '--no-push', is_flag=True, help='Skip pushing')
@no_reset_flag
@verbose_flag
@click.argument('ref_strs', nargs=-1)
def main(no_push, no_reset, verbose, ref_strs):
    refs = DefaultDict.load(ref_strs, fallback='HEAD')
    if not refs:
        if verbose:
            err("No refs found, exiting")
        return

    def get_new_sha_entry(submodule) -> Optional[Tuple[str, str]]:
        ref = refs[submodule]
        if not ref:
            return
        cur_sha = submodule.hexsha
        line = process.line('git', 'ls-remote', submodule.url, ref, log=err if verbose else None)
        new_sha, _ = re.split(r'\s+', line, 1)
        if cur_sha != new_sha:
            return submodule.name, new_sha
        else:
            return None

    repo = Repo()
    submodules = repo.submodules
    new_shas = dict(filter(None, parallel(submodules, get_new_sha_entry)))

    for name, sha in new_shas.items():
        err(f'{name}: {sha}')

    new_commit_sha = update_submodules(new_shas, no_reset=no_reset, verbose=verbose)
    if new_commit_sha and not no_push:
        process.run('git', 'push')


if __name__ == '__main__':
    main()
