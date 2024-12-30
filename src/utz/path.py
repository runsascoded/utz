from os import makedirs
from os.path import dirname
import pathlib
from typing import Union

Path = Union[str, pathlib.Path]


def mkdir(path: Path, mode=0o777, exist_ok=True) -> Path:
    """Wrapper for ``makedirs``, accepting ``str | Path``, and setting ``exist_ok=True`` by default."""
    makedirs(str(path), mode=mode, exist_ok=exist_ok)
    return path


def mkpar(path: Path, *args, **kwargs) -> Path:
    """Create parent directories for a path, if they do not exist."""
    if isinstance(path, pathlib.Path):
        mkdir(path.parent, *args, **kwargs)
    else:
        mkdir(dirname(path))
    return path
