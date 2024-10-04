# utz
*("yoots")*: utilities I've missed in the Python standard library

[![](https://img.shields.io/pypi/v/utz?color=blue&style=flat-square)][utz]

<!-- toc -->
- [Install](#install)
- [Use](#use)
    - [`utz.process`](#utz.process)
    - [`utz.collections`](#utz.collections)
    - [`utz.cd`: "change directory" contextmanager](#utz.cd)
    - [`utz.ctxs`: compose `contextmanager`s](#utz.ctxs)
    - [`utz.fn`](#utz.fn)
    - [`utz.plot`: Plotly helpers](#utz.plots)
    - [`utz.setup`: `setup.py` helper](#utz.setup)
    - [Misc](#misc)
<!-- /toc -->

## Install <a id="install"></a>
```bash
pip install utz
```

## Use <a id="use"></a>

I usually do this at the top of Jupyter notebooks:
```python
from utz import *
```

This imports most standard library modules/functions (via [`stdlb`]), as well as the `utz.*` members below. 

Some specific modules, in rough order of how often I use them:

### [`utz.process`] <a id="utz.process"></a>

[`subprocess`] wrappers; shell out to commands, parse output:

```python
from utz.process import *

# Run a command
run('git', 'commit', '-m', 'message')  # Commit staged changes

# Return `list[str]` of stdout lines
lines('git', 'log', '-n5', '--format=%h')  # Last 5 commit SHAs

# Verify exactly one line of stdout, return it
line('git', 'log', '-1', '--format=%h')  # Current HEAD commit SHA

# Return stdout as a single string
output('git', 'log', '-1', '--format=%B')  # Current HEAD commit message

# Check whether a command succeeds, suppress output
check('git', 'diff', '--exit-code', '--quiet')  # `True` iff there are no uncommitted changes

err("This will be output to stderr")
```

See also: [`test_process.py`].

### [`utz.collections`] <a id="utz.collections"></a>

Collection/list helpers:

```python
from utz.collections import *

# Verify a collection has one element, return it
singleton(["aaa"])         # "aaa"
singleton(["aaa", "bbb"])  # error
```

See also: [`test_collections.py`].

### [`utz.cd`]: "change directory" contextmanager <a id="utz.cd"></a>
```python
from utz import cd
with cd('..'):  # change to parent dir
    ...
```

### [`utz.ctxs`]: compose `contextmanager`s <a id="utz.ctxs"></a>
```python
from utz import *
with ctxs(NamedTemporaryFile(), NamedTemporaryFile()) as (f1, f2):
    ...
```

See also: [`test_context.py`].


### [`utz.fn`] <a id="utz.fn"></a>

Compose decorators:
```python
from utz import decos
from click import option

common_opts = decos(
    option('-n', type=int),
    option('-v', is_flag=True),
)

@common_opts
def subcmd1(n: int, v: bool):
    ...

@common_opts
def subcmd2(n: int, v: bool):
    ...
```

Only pass expected `kwargs` to functions:
```python
from utz.fn import call
def fn1(a, b):
    ...
def fn2(a, c):
    ...
kwargs = dict(a=11, b='22', c=33)
call(fn1, kwargs)  # only pass {a, b}
call(fn2, kwargs)  # only pass {a, c}
```

### [`utz.plot`]: [Plotly] helpers <a id="utz.plots"></a>
Helpers for Plotly transformations I make frequently, e.g.:
```python
from utz import plot
import plotly.express as px
fig = px.bar(x=[1, 2, 3], y=[4, 5, 6])
plot(
    fig,
    name='my-plot',  # Filename stem. will save my-plot.png, my-plot.json, optional my-plot.html
    title=['Some Title', 'Some subtitle'],  # Plot title, followed by "subtitle" line(s) (smaller font, just below)
    bg='white', xgrid='#ccc',  # white background, grey x-gridlines
    hoverx=True,  # show x-values on hover
    x="X-axis title",  # x-axis title or configs
    y=dict(title="Y-axis title", zerolines=True),  # y-axis title or configs
    # ...
)
```

Example usages: [hudcostreets/nj-crashes][hudcostreets/nj-crashes utz.plots], [ryan-williams/arrayloader-benchmarks][ryan-williams/arrayloader-benchmarks utz.plots].

### [`utz.setup`]: `setup.py` helper <a id="utz.setup"></a>
[`utz/setup.py`](utz/setup.py) provides defaults for various `setuptools.setup()` params:
- `name`: use parent directory name
- `version`: parse from git tag (otherwise from `git describe --tags`)
- `install_requires`: read `requirements.txt`
- `author_{name,email}`: infer from last commit
- `long_description`: parse `README.md` (and set `long_description_content_type`)
- `description`: parse first `<p>` under opening `<h1>` from `README.md`
- `license`: parse from `LICENSE` file (MIT and Apache v2 supported)

For an example, see [`gsmo==0.0.1`](https://github.com/runsascoded/gsmo/blob/v0.0.1/setup.py) ([and corresponding release](https://pypi.org/project/gsmo/)).

This library also "self-hosts" using `utz.setup`; see [pyproject.toml](pyproject.toml):

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


### Misc <a id="misc"></a>
Other noteworthy modules:
- [o](utz/o.py): `dict` wrapper exposing keys as attrs (e.g.: `o({'a':1}).a == 1`)
- [docker](utz/docker/): DSL for programmatically creating Dockerfiles (and building images from them)
- [ssh](utz/ssh.py): SSH tunnel wrapped in a context manager
- [time](utz/time.py): `now()`/`today()` helpers with convenient / no-nonsense ISO string serialization and UTC bias
- [bases](utz/bases.py): `int`⟺`str` codecs with improvements over standard base64 et al.
- [tmpdir](utz/tmpdir.py): make temporary directories with a specific basename
- [escape](utz/escape.py): escaping split/join helpers
- [backoff](utz/backoff.py): exponential-backoff utility
- [git](utz/git): Git helpers, wrappers around [GitPython](https://gitpython.readthedocs.io/en/stable/)
- [pnds](utz/pnds.py): [pandas](https://pandas.pydata.org/) imports and helpers


[utz]: https://pypi.org/project/utz/
[`stdlb`]: https://pypi.org/project/stdlb/
[`utz.process`]: utz/process/__init__.py
[`subprocess`]: https://docs.python.org/3/library/subprocess.html
[`test_process.py`]: utz/tests/test_process.py
[`utz.collections`]: utz/collections.py
[`test_collections.py`]: utz/tests/test_collections.py
[`utz.context`]: utz/context.py
[`test_context.py`]: utz/tests/test_context.py
[`utz.setup`]: utz/setup.py
[`utz.cd`]: utz/cd.py
[`utz.fn`]: utz/fn.py
[`utz.ctxs`]: utz/context.py
[`utz.plot`]: utz/plots.py
[Plotly]: https://plotly.com/python/
[hudcostreets/nj-crashes utz.plots]: https://github.com/search?q=repo%3Ahudcostreets%2Fnj-crashes%20utz.plot&type=code
[ryan-williams/arrayloader-benchmarks utz.plots]: https://github.com/search?q=repo%3Aryan-williams%2Farrayloader-benchmarks%20utz.plot&type=code 
