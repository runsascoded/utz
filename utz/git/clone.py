
from contextlib import contextmanager
from tempfile import TemporaryDirectory

from utz import cd, run


@contextmanager
def tmp(url, *clone_args, submodules=True, **run_kwargs):
    with TemporaryDirectory() as tmpdir:
        cmd = ['git','clone']
        if submodules: cmd += ['--recurse-submodules']
        cmd += clone_args
        cmd += [ url,tmpdir, ]
        run(*cmd, **run_kwargs)
        with cd(tmpdir):
            yield tmpdir
