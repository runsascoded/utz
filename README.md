# utz
*("yoots")*: common imports and utilities exposed for easy wildcard-importing + boilerplate-reduction

## Install
```bash
pip install utz
```

## Use
Import the whole kitchen sink:
```python
from utz import *
```

See [__init__.py](utz/__init__.py), which imports many of the modules below, as well as a bevy of handy stdlib methods and objects.

## Features
Some noteworthy modules:
- [cd](utz/cd.py): "change directory" contextmanager
- [o](utz/o.py): `dict` wrapper exposing keys as attrs (e.g.: `o({'a':1}).a == 1`)
- [process](utz/process.py): subprocess wrappers for more easily shelling out to commands and parsing their stdout
- [docker](docker/): DSL for programmatically creating Dockerfiles (and building images from them)
- [git](utz/git): git helpers / wrappers around [GitPython](https://gitpython.readthedocs.io/en/stable/)
- [pnds](utz/pnds.py): common [pandas](https://pandas.pydata.org/) imports and helpers
- [collections](utz/collections.py): collection/list helpers
- [context](utz/context.py): contextlib helpers

### auto-`setup.py`
[`utz/setup.py`](utz/setup.py) provides defaults for various `setuptools.setup()` params:
- `name`: use parent directory name
- `version`: parse from git tag (otherwise from `git describe --tags`)
- `author_{name,email}`: infer from last commit
- `long_description`: parse `README.md` (and set `long_description_content_type)
- `description`: parse first `<p>` under opening `<h1>` from `README.md`
- `license`: parse from `LICENSE` file (MIT and Apache v2 supported)

For an example, see [`gsmo==0.0.1`](https://github.com/runsascoded/gsmo/blob/v0.0.1/setup.py) ([and corresponding release](https://pypi.org/project/gsmo/)).

It can be installed via a pip extra:
```bash
pip install utz[setup]
``` 
