# utz
*("yoots")*: imports and utilities for easy wildcard-importing + boilerplate-reduction

[![](https://img.shields.io/pypi/v/utz?color=blue&style=flat-square)][utz]

## Install
```bash
pip install utz
```

## Use
Import everything:
```python
from utz import *
```

See [`__init__.py`](utz/__init__.py), which imports many of the modules below, as well as many standard-library methods and objects (via the [`stdlb`] package).

## Features
Some noteworthy modules:
- [cd](utz/cd.py): "change directory" contextmanager
- [o](utz/o.py): `dict` wrapper exposing keys as attrs (e.g.: `o({'a':1}).a == 1`)
- [process](utz/process.py): `subprocess` wrappers; shell out to commands, parse output
- [docker](docker/): DSL for programmatically creating Dockerfiles (and building images from them)
- [ssh](utz/ssh.py): SSH tunnel wrapped in a context manager
- [time](utz/time.py): `now()`/`today()` helpers with convenient / no-nonsense ISO string serialization and UTC bias
- [bases](utz/bases.py): `int`⟺`str` codecs with improvements over standard base64 et al.
- [tmpdir](utz/tmpdir.py): make temporary directories with a specific basename
- [context](utz/context.py): contextmanager helpers, including `ctxs` for composing multiple context managers
- [escape](utz/escape.py): escaping split/join helpers
- [backoff](utz/backoff.py): exponential-backoff utility
- [git](utz/git): Git helpers, wrappers around [GitPython](https://gitpython.readthedocs.io/en/stable/)
- [pnds](utz/pnds.py): [pandas](https://pandas.pydata.org/) imports and helpers
- [collections](utz/collections.py): collection/list helpers
- [plots](utz/plots.py): plotly helpers

### auto-`setup.py`
[`utz/setup.py`](utz/setup.py) provides defaults for various `setuptools.setup()` params:
- `name`: use parent directory name
- `version`: parse from git tag (otherwise from `git describe --tags`)
- `author_{name,email}`: infer from last commit
- `long_description`: parse `README.md` (and set `long_description_content_type)
- `description`: parse first `<p>` under opening `<h1>` from `README.md`
- `license`: parse from `LICENSE` file (MIT and Apache v2 supported)

For an example, see [`gsmo==0.0.1`](https://github.com/runsascoded/gsmo/blob/v0.0.1/setup.py) ([and corresponding release](https://pypi.org/project/gsmo/)).

This library also "self-hosts" using its own `setup` helper; see [pyproject.toml](pyproject.toml):

```toml
[build-system]
requires = ["setuptools", "utz[setup]==0.4.2", "wheel"]
build-backend = "setuptools.build_meta"
```

and [setup.py](setup.py):
```python
from utz.setup import setup

extras_require = {
    # …
}

# Various fields auto-populated from git, README.md, requirements.txt, …
setup(
    name="utz",
    version="0.8.0",
    extras_require=extras_require,
    url="https://github.com/runsascoded/utz",
    python_requires=">=3.10",
)

```

The `setup` helper can be installed via a pip "extra":
```bash
pip install utz[setup]
``` 

[utz]: https://pypi.org/project/utz/
[`stdlb`]: https://pypi.org/project/stdlb/
