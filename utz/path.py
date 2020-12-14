from os import makedirs
from os.path import dirname
from pathlib import Path


def mkdir(path, *args, exist_ok=True, **kwargs):
    makedirs(str(path), *args, exist_ok=exist_ok, **kwargs)
    return path

def mkpar(path, *args, **kwargs):
    if isinstance(path, Path):
        path.parent.mkdir(exist_ok=True, parents=True)
    else:
        mkdir(dirname(path))
    return path
