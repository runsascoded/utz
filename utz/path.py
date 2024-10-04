from os import makedirs
from os.path import dirname
from pathlib import Path


def mkdir(path: str | Path, mode=0o777, exist_ok=True) -> str | Path:
    """Wrapper for ``makedirs``, accepting ``str | Path``, and setting ``exist_ok=True`` by default."""
    makedirs(str(path), mode=mode, exist_ok=exist_ok)
    return path


def mkpar(path: str | Path, *args, **kwargs) -> str | Path:
    """Create parent directories for a path, if they do not exist."""
    if isinstance(path, Path):
        mkdir(path.parent, *args, **kwargs)
    else:
        mkdir(dirname(path))
    return path
