
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Iterable

from utz import cd, run


@contextmanager
def tmp(url, *clone_args, submodules=True, push=False, **run_kwargs):
    with TemporaryDirectory() as tmpdir:
        cmd = ['git','clone']
        if submodules: cmd += ['--recurse-submodules']
        cmd += clone_args
        cmd += [ url,tmpdir, ]
        run(*cmd, **run_kwargs)
        with cd(tmpdir):
            yield tmpdir
            if push:
                cmd = ['git','push']
                if isinstance(push, str):
                    cmd += ['origin',push]
                elif isinstance(push, Iterable):
                    cmd += push
                run(*cmd)
