
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Iterable

import utz
from utz import nullcontext, run


@contextmanager
def tmp(url, *clone_args, submodules=True, push=False, cd=True, **run_kwargs):
    with TemporaryDirectory() as tmpdir:
        cmd = ['git','clone']
        if submodules: cmd += ['--recurse-submodules']
        cmd += clone_args
        cmd += [ url,tmpdir, ]
        run(*cmd, **run_kwargs)
        if cd:
            ctx = utz.cd(tmpdir)
            post_ctx = nullcontext()
        else:
            ctx = nullcontext()
            post_ctx = utz.cd(tmpdir)
        with ctx:
            yield tmpdir
            with post_ctx:
                if push:
                    cmd = ['git','push']
                    if isinstance(push, str):
                        cmd += ['origin',push]
                    elif isinstance(push, Iterable):
                        cmd += push
                    run(*cmd)
