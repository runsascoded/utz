from contextlib import contextmanager
from os import mkdir
from os.path import join
from tempfile import TemporaryDirectory


@contextmanager
def tmpdir(name: str = None, dir: str = None):
    """``contextmanager`` for creating a temporary directory with an optional ``name``"""
    if name:
        with TemporaryDirectory(dir=dir) as tmpdir:
            dir = join(tmpdir, name)
            mkdir(dir)
            yield dir
    else:
        yield TemporaryDirectory(dir=dir)
