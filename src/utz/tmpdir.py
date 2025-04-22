from __future__ import annotations

from contextlib import contextmanager, nullcontext
import os
from os import makedirs, mkdir, rmdir
from os.path import exists, join, sep, dirname
from tempfile import TemporaryDirectory


@contextmanager
def named_tmpdir(name: str = None, **kwargs):
    """``contextmanager`` for creating a temporary directory with an optional ``name``"""
    if name:
        if 'prefix' in kwargs:
            raise ValueError('`prefix` is not supported; use `name` instead')
        if 'suffix' in kwargs:
            raise ValueError('`suffix` is not supported; use `name` instead')
        with TemporaryDirectory(**kwargs) as tmpdir:
            dir = join(tmpdir, name)
            mkdir(dir)
            yield dir
    else:
        with TemporaryDirectory(**kwargs) as td:
            yield td


@contextmanager
def tmp_ensure_dir(path: str):
    """Ensure a directory (and its parents) exist; any dirs created are cleaned up on exit (expected to be empty)."""
    pcs = path.split(sep)
    cur = ''
    rms = []
    for pc in pcs:
        cur = os.path.join(cur, pc) if cur else pc
        if not exists(cur):
            makedirs(cur)
            rms.append(cur)
    try:
        yield
    finally:
        while rms:
            rm = rms.pop()
            rmdir(rm)


@contextmanager
def TmpDir(
    name: str | None = None,
    dir: str | None = None,
    **kwargs,
):
    """``TemporaryDirectory`` wrapper that temporarily creates ``dir`` (and parents), if necessary.

    Also supports ``name`` kwarg for specifying the exact basename of the temporary directory.
    """
    ctx0 = tmp_ensure_dir(dir) if dir else nullcontext()
    ctx1 = named_tmpdir(name, dir=dir, **kwargs)
    with (
        ctx0,
        ctx1 as rv,
    ):
        yield rv


tmpdir = TmpDir


@contextmanager
def TmpPath(name: str | None = None, **kwargs):
    """Yield a path to a temporary file with a given name."""
    name = name or 'tmpfile'
    with TemporaryDirectory(**kwargs) as tmpdir:
        path = join(tmpdir, name)
        parent = dirname(path)
        makedirs(parent, exist_ok=True)
        yield path


tmppath = TmpPath
