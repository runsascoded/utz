from contextlib import contextmanager
from os import remove
from os.path import basename, dirname, join, splitext
from pathlib import Path
from typing import Any, ContextManager, IO, Literal
from zipfile import is_zipfile, ZipFile


def try_unzip(path: str) -> str:
    """If `path` is a zip file, extract it to a directory with the same name"""
    if isinstance(path, Path):
        path = str(path)
    if is_zipfile(path):
        from shutil import move
        parent = dirname(path)
        name, ext = splitext(basename(path))
        if ext == '.zip':
            zip_path = path
            path = join(parent, name)
        else:
            zip_path = join(parent, '%s.zip' % name)
            print('Renaming %s to %s' % (path, zip_path))
            move(path, zip_path)

        print('Extracting %s to %s' % (zip_path, path))
        with ZipFile(zip_path) as f:
            f.extractall(path)

        remove(zip_path)

    return path


@contextmanager
def zip_open(
    zip_path: str,
    inner_path: str,
    mode: Literal["r", "w", "x", "a"] = 'r',
) -> ContextManager[IO[Any]]:
    """Open a file within a zip archive"""
    with ZipFile(zip_path, mode) as z:
        with z.open(inner_path) as f:
            yield f
