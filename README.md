# utz
*("yoots")*: utilities I've missed in the Python standard library, Pytest, Pandas, Plotly, …

[![](https://img.shields.io/pypi/v/utz?color=blue&style=flat-square)][utz]

<!-- toc -->
- [Install](#install)
- [Use](#use)
    - [`utz.process`: `subprocess` wrappers; shell out to commands, parse output](#utz.process)
    - [`utz.collections`: Collection/list helpers](#utz.collections)
    - [`utz.cd`: "change directory" contextmanager](#utz.cd)
    - [`utz.fn`: decorator/function utilities](#utz.fn)
        - [`utz.decos`: compose decorators](#utz.decos)
        - [`utz.call`: only pass expected `kwargs` to functions](#utz.call)
    - [`utz.plot`: Plotly helpers](#utz.plots)
    - [`utz.setup`: `setup.py` helper](#utz.setup)
    - [`utz.test`: `dataclass` test cases, `raises` helper](#utz.test)
        - [`utz.parametrize`: `pytest.mark.parametrize` wrapper, accepts `dataclass` instances](#utz.parametrize)
        - [`utz.raises`: `pytest.raises` wrapper, match a regex or multiple strings](#utz.raises)
    - [`utz.time`: `now`/`today` helpers](#utz.time)
    - [`utz.hash_file`](#utz.hash_file)
    - [`utz.docker`, `utz.tmpdir`, etc.](#misc)
<!-- /toc -->

## Install <a id="install"></a>
```bash
pip install utz
```
- `utz` has one dependency, [`stdlb`] (wild-card standard library imports).
- ["Extras"][extras] provide optional deps (e.g. [Pandas], [Plotly], …).

## Use <a id="use"></a>

I usually do this at the top of Jupyter notebooks:
```python
from utz import *
```

This imports most standard library modules/functions (via [`stdlb`]), as well as the `utz` members below.

Below are a few modules, in rough order of how often I use them:

### [`utz.process`]: [`subprocess`] wrappers; shell out to commands, parse output <a id="utz.process"></a>

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

# Execute a "pipeline" of commands
pipeline(['seq 10', 'head -n5'])  # '1\n2\n3\n4\n5\n'

# Diff two command pipelines, e.g. compare lines/words/chars in a gzipped CSV, at Git HEAD vs. worktree:
cmds = ['gunzip -c', 'wc']
file = 'foo.csv.gz'
diff_cmds(
    [f'git show HEAD:{file}', *cmds],
    [f'cat {file}', *cmds]
)
```

`diff_cmds` is also exposed as a CLI, `diff-x`:
```bash
# Diff the contents of two `.gz` files
seq 10 | gzip -c > a.gz
seq 2 12 | gzip -c > b.gz
diff-x 'gunzip -c' {a,b}.gz
# 1d0
# < 1
# 10a10,11
# > 11
# > 12

# Pass multiple commands to create a pipeline:
diff-x 'gunzip -c' 'head -n5' {a,b}.gz
# 1d0
# < 1
# 5a5
# > 6
```

See also: [`test_process.py`].

### [`utz.collections`]: Collection/list helpers <a id="utz.collections"></a>

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

### [`utz.fn`]: decorator/function utilities <a id="utz.fn"></a>

#### `utz.decos`: compose decorators <a id="utz.decos"></a>
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

#### `utz.call`: only pass expected `kwargs` to functions <a id="utz.call"></a>
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

### [`utz.test`]: `dataclass` test cases, `raises` helper <a id="utz.test"></a>

#### `utz.parametrize`: [`pytest.mark.parametrize`] wrapper, accepts [`dataclass`] instances <a id="utz.parametrize"></a>

```python
from utz import parametrize
from dataclasses import dataclass


def fn(f: float, fmt: str) -> str:
    """Example function, to be tested with ``Case``s below."""
    return f"{f:{fmt}}"


@dataclass
class case:
    """Container for a test-case; float, format, and expected output."""
    f: float
    fmt: str
    expected: str

    @property
    def id(self):
        return f"fmt-{self.f}-{self.fmt}"


@parametrize(
    case(1.23, "0.1f", "1.2"),
    case(123.456, "0.1e", "1.2e+02"),
    case(-123.456, ".0f", "-123"),
)
def test_fn(f, fmt, expected):
    """Example test, "parametrized" by several ``Cases``s."""
    assert fn(f, fmt) == expected
```

[`test_parametrize.py`] contains more examples, customizing test "ID"s, adding parameter sweeps, etc.

#### `utz.raises`: `pytest.raises` wrapper, match a regex or multiple strings <a id="utz.raises"></a>

### [`utz.time`]: `now`/`today` helpers <a id="utz.time"></a>

`now` and `today` are wrappers around `datetime.datetime.now` that expose convenient functions:
```python
from utz import now, today
now()     # 2024-10-11T15:43:54Z
today()   # 2024-10-11
now().s   # 1728661583
now().ms  # 1728661585952
```

Use in conjunction with [`utz.bases`] codecs for easy timestamp-nonces:
```python
from utz import b62, now
b62(now().s)   # A18Q1l
b62(now().ms)  # dZ3fYdS
b62(now().us)  # G31Cn073v
```

Sample values for various units and codecs:

<table border="1" class="dataframe">
<thead>
  <tr style="text-align: right;">
    <th>unit</th>
    <th>b62</th>
    <th>b64</th>
    <th>b90</th>
  </tr>
</thead>
<tbody>
  <tr>
    <th>s</th>
    <td>A18RXZ</td>
    <td>+a/I/7</td>
    <td>:?98&gt;</td>
  </tr>
  <tr>
    <th>ds</th>
    <td>R0165M</td>
    <td>D3KFIY</td>
    <td>"sJh_?</td>
  </tr>
  <tr>
    <th>cs</th>
    <td>CBp0oXI</td>
    <td>/TybqKo</td>
    <td>=8d'#K</td>
  </tr>
  <tr>
    <th>ms</th>
    <td>dZ3no2f</td>
    <td>M6vLchJ</td>
    <td>#6cRfBj</td>
  </tr>
  <tr>
    <th>us</th>
    <td>G31ExCseD</td>
    <td>360KU8v9V</td>
    <td>D,f`6&amp;uX</td>
  </tr>
</tbody>
</table>

(generated by [`time-slug-grid.py`](scripts/time-slug-grid.py))

### [`utz.hash_file`](utz/hash.py) <a id="utz.hash_file"></a>

```python
from utz import hash_file
hash_file("path/to/file")  # sha256 by default
hash_file("path/to/file", 'md5')
```

### [`utz.docker`](utz/docker/), [`utz.tmpdir`](utz/tmpdir.py), etc. <a id="misc"></a>

Misc other modules:
- [o](utz/o.py): `dict` wrapper exposing keys as attrs (e.g.: `o({'a':1}).a == 1`)
- [docker](utz/docker/): DSL for programmatically creating Dockerfiles (and building images from them)
- [bases][`utz.bases`]: encode/decode in various bases (62, 64, 90, …)
- [tmpdir](utz/tmpdir.py): make temporary directories with a specific basename
- [escape](utz/escape.py): split/join on an arbitrary delimiter, with backslash-escaping
- [ssh](utz/ssh.py): SSH tunnel wrapped in a context manager
- [backoff](utz/backoff.py): exponential-backoff utility
- [git](utz/git): Git helpers, wrappers around [GitPython](https://gitpython.readthedocs.io/en/stable/)
- [pnds](utz/pnds.py): [pandas](https://pandas.pydata.org/) imports and helpers
- [ctxs][`utz.ctxs`]: compose `contextmanager`s


[utz]: https://pypi.org/project/utz/
[extras]: https://github.com/runsascoded/utz/blob/main/setup.py#L3-L34
[`stdlb`]: https://pypi.org/project/stdlb/
[`utz.process`]: utz/process/__init__.py
[`subprocess`]: https://docs.python.org/3/library/subprocess.html
[`test_process.py`]: utz/tests/test_process.py
[`utz.collections`]: utz/collections.py
[`test_collections.py`]: utz/tests/test_collections.py
[`utz.context`]: utz/context.py
[`utz.bases`]: utz/bases.py
[`utz.time`]: utz/time.py
[`test_context.py`]: utz/tests/test_context.py
[`utz.setup`]: utz/setup.py
[`utz.cd`]: utz/cd.py
[`utz.fn`]: utz/fn.py
[`utz.ctxs`]: utz/context.py
[`utz.plot`]: utz/plots.py
[Plotly]: https://plotly.com/python/
[hudcostreets/nj-crashes utz.plots]: https://github.com/search?q=repo%3Ahudcostreets%2Fnj-crashes%20utz.plot&type=code
[ryan-williams/arrayloader-benchmarks utz.plots]: https://github.com/search?q=repo%3Aryan-williams%2Farrayloader-benchmarks%20utz.plot&type=code

[tdbs parametrize_cases]: https://github.com/single-cell-data/TileDB-SOMA/blob/1.14.2/apis/python/tests/parametrize_cases.py
[roundtrips]: https://github.com/single-cell-data/TileDB-SOMA/blob/1.14.2/apis/python/tests/test_dataframe_io_roundtrips.py
[`utz.test`]: utz/test.py
[`test_parametrize.py`]: utz/tests/test_parametrize.py
[`pytest.mark.parametrize`]: https://docs.pytest.org/en/stable/how-to/parametrize.html
[`dataclass`]: https://docs.python.org/3/library/dataclasses.html

[Pandas]: https://pandas.pydata.org/
[Plotly]: https://plotly.com/python/
