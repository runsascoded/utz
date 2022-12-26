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

See [`__init__.py`](utz/__init__.py), which imports many of the modules below, as well as a bevy of handy stdlib methods and objects.

## Features
Some noteworthy modules:
- [cd](utz/cd.py): "change directory" contextmanager
- [o](utz/o.py): `dict` wrapper exposing keys as attrs (e.g.: `o({'a':1}).a == 1`)
- [process](utz/process.py): subprocess wrappers for more easily shelling out to commands and parsing their stdout
- [docker](docker/): DSL for programmatically creating Dockerfiles (and building images from them)
- [ssh](utz/ssh.py): SSH tunnel wrapped in a context manager
- [time](utz/time.py): `now()`/`today()` helpers with convenient / no-nonsense ISO string serialization and UTC bias
- [bases](utz/bases.py): `int`⟺`str` codecs with improvements over standard base64 et al.
- [tmpdir](utz/tmpdir.py): make temporary directories with a specific basename
- [context](utz/context.py): context-manager helpers, including `ctxs` for composing multiple context managers
- [escape](utz/escape.py): escaping split/join helpers
- [backoff](utz/backoff.py): simple exponential-backoff utility
- [git](utz/git): git helpers / wrappers around [GitPython](https://gitpython.readthedocs.io/en/stable/)
- [pnds](utz/pnds.py): common [pandas](https://pandas.pydata.org/) imports and helpers
- [collections](utz/collections.py): collection/list helpers

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
