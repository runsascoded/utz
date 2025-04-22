from __future__ import annotations

from contextlib import contextmanager
from os import chdir, getcwd
from pathlib import Path

from utz.tmpdir import TmpDir


class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, path: str | Path, mk: bool = False):
        path = Path(path)
        self.path = path.expanduser()
        self.mk = mk

    def __enter__(self):
        self.prevPath = Path(getcwd())
        if self.mk:
            self.path.mkdir(parents=True, exist_ok=True)
        chdir(str(self.path))

    def __exit__(self, etype, value, traceback):
        chdir(str(self.prevPath))


@contextmanager
def cd_tmpdir(*args, **kwargs):
    """Create a ``TemporaryDirectory`` (creating any parents of ``dir``, as necessary) and ``cd`` into it."""
    with TmpDir(*args, **kwargs) as rv, cd(rv):
        yield rv
