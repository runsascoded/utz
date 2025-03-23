# utz
*("yoots")*: utilities augmenting the Python standard library; processes, Pytest, Pandas, Plotly, …

[![](https://img.shields.io/pypi/v/utz?color=blue&style=flat-square)][pypi]

<!-- toc -->
- [Install](#install)
- [Import: `from utz import *`](#import)
    - [Jupyter](#jupyter)
    - [Python REPL](#repl)
- [Modules](#modules)
    - [`utz.proc`: `subprocess` wrappers; shell out commands, parse output](#utz.proc)
        - [`utz.proc.aio`: async `subprocess` wrappers](#utz.proc.aio)
    - [`utz.collections`: collection/list helpers](#utz.collections)
    - [`utz.env`: `os.environ` wrapper + `contextmanager`](#utz.env)
    - [`utz.fn`: decorator/function utilities](#utz.fn)
        - [`utz.decos`: compose decorators](#utz.decos)
        - [`utz.call`: only pass expected `kwargs` to functions](#utz.call)
    - [`utz.jsn`: `JsonEncoder` for datetimes, `dataclasses`](#utz.jsn)
    - [`utz.context`: `{async,}contextmanager` helpers](#utz.context)
    - [`utz.cli`: `click` helpers](#utz.cli)
    - [`utz.mem`: memray wrapper](#utz.mem)
    - [`utz.time`: `Time` timer, `now`/`today` helpers](#utz.time)
    - [`utz.size`: `humanize.naturalsize` wrapper](#utz.size)
    - [`utz.hash_file`: hash file contents](#utz.hash_file)
    - [`utz.ym`: `YM` (year/month) class](#utz.ym)
    - [`utz.cd`: "change directory" contextmanager](#utz.cd)
    - [`utz.gzip`: deterministic GZip helpers](#utz.gzip)
    - [`utz.s3`: S3 utilities](#utz.s3)
    - [`utz.plot`: Plotly helpers](#utz.plots)
    - [`utz.setup`: `setup.py` helper](#utz.setup)
    - [`utz.test`: `dataclass` test cases, `raises` helper](#utz.test)
        - [`utz.parametrize`: `pytest.mark.parametrize` wrapper, accepts `dataclass` instances](#utz.parametrize)
        - [`utz.raises`: `pytest.raises` wrapper, match a regex or multiple strings](#utz.raises)
    - [`utz.docker`, `utz.tmpdir`, etc.](#misc)
- [Examples / Users](#examples)
<!-- /toc -->

## Install <a id="install"></a>
```bash
pip install utz
```
- `utz` has one dependency, [`stdlb`] (wild-card standard library imports).
- ["Extras"][extras] provide optional deps (e.g. [Pandas], [Plotly], …).

## Import: `from utz import *` <a id="import"></a>

### Jupyter <a id="jupyter"></a>
I often import `utz.*` in Jupyter notebooks:
```python
from utz import *
```

This imports most standard library modules/functions (via [`stdlb`]), as well as the `utz` members below.

### Python REPL <a id="repl"></a>
You can also import `utz.*` during Python REPL startup:
```bash
cat >~/.pythonrc <<EOF
try:
    from utz import *
    err("Imported utz")
except ImportError:
    err("Couldn't find utz")
EOF
export PYTHONSTARTUP=~/.pythonrc
# Configure for Python REPL in new Bash shells:
echo 'export PYTHONSTARTUP=~/.pythonrc' >> ~/.bashrc
```

## Modules <a id="modules"></a>
Here are a few `utz` modules, in rough descending order of how often I use them:

### [`utz.proc`]: [`subprocess`] wrappers; shell out commands, parse output <a id="utz.proc"></a>

```python
from utz.proc import *

# Run a command
run('git', 'commit', '-m', 'message')  # Commit staged changes

# Passing a single string implies `shell=True` (for all functions listed here)
# Return `list[str]` of stdout lines
lines('git log -n5 --format=%h')  # Last 5 commit SHAs

# Verify exactly one line of stdout, return it
line('git log -1 --format=%h')  # Current HEAD commit SHA

# Return stdout as a single string
output('git log -1 --format=%B')  # Current HEAD commit message

# Check whether a command succeeds, suppress output
check('git diff --exit-code --quiet')  # `True` iff there are no uncommitted changes
# Nested arrays are flattened (for all commands above):
check(['git', 'diff', ['--exit-code', '--quiet']])

err("This will be output to stderr")

# Execute a "pipeline" of commands
pipeline(['seq 10', 'head -n5'])  # '1\n2\n3\n4\n5\n'
```

See also: [`test_proc.py`].

#### [`utz.proc.aio`]: async [`subprocess`] wrappers <a id="utz.proc.aio"></a>
Async versions of most [`utz.proc`] helpers are also available:

```python
from utz.proc.aio import *
import asyncio
from asyncio import gather

async def test():
  _1, _2, _3, nums = await gather(*[
      run('sleep', '1'),
      run('sleep', '2'),
      run('sleep', '3'),
      lines('seq', '10'),
  ])
  return nums

asyncio.run(test())
# ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
```

### [`utz.collections`]: collection/list helpers <a id="utz.collections"></a>

```python
from utz.collections import *

# Verify a collection has one element, return it
singleton(["aaa"])         # "aaa"
singleton(["aaa", "bbb"])  # error

# `solo` is an alias for `singleton`; both also work on dicts, verifying and extracting a single "item" pair:
solo({'a': 1})  # ('a', 1)

# Filter by a predicate
solo([2, 3, 4], pred=lambda n: n % 2)  # 3
solo([{'a': 1}, {'b': 2}], pred=lambda o: 'a' in o)  # {'a': 1}
```

See also: [`test_collections.py`].

### [`utz.env`]: `os.environ` wrapper + `contextmanager` <a id="utz.env"></a>
```python
from utz import env, os

# Temporarily set env vars
with env(FOO='bar'):
    assert os.environ['FOO'] == 'bar'

assert 'FOO' not in os.environ
```

The `env()` contextmanager also supports configurable [`on_conflict`] and [`on_exit`] kwargs, for handling env vars that were patched, then changed while the context was active.

See also: [`test_env.py`].

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
from utz import call, wraps
def fn1(a, b):
    ...

@wraps(fn1)
def fn2(a, c, **kwargs):
    ...
kwargs = dict(a=11, b='22', c=33, d=44)
call(fn1, **kwargs)  # passes {a, b}, not {c, d}
call(fn2, **kwargs)  # passes {a, b, c}, not {d}
```

See also: [`test_fn.py`].

### [`utz.jsn`]: `JsonEncoder` for datetimes, `dataclasses` <a id="utz.jsn"></a>
```python
from utz import dataclass, Encoder, fromtimestamp, json  # Convenience imports from standard library
epoch = fromtimestamp(0)
print(json.dumps({ 'epoch': epoch }, cls=Encoder))
# {"epoch": "1969-12-31 19:00:00"}
print(json.dumps({ 'epoch': epoch }, cls=Encoder("%Y-%m-%d"), indent=2))
# {
#   "epoch": "1969-12-31"
# }

@dataclass
class A:
    n: int

print(json.dumps(A(111), cls=Encoder))
# {"n": 111}
```

See [`test_jsn.py`] for more examples.

### [`utz.context`]: `{async,}contextmanager` helpers <a id="utz.context"></a>
- `ctxs`: compose `contextmanager`s
- `actxs`: compose `asynccontextmanager`s
- `with_exit_hook`: wrap a `contextmanager`'s `__exit__` method in another `contextmanager`

### [`utz.cli`]: [`click`] helpers <a id="utz.cli"></a>
[`utz.cli`] provides wrappers around `click.option` for parsing common option formats:
- `@count`: "count" options, including optional value mappings (e.g. `-v` → "info", `-vv` → "debug")
- `@multi`: parse comma-delimited values (or other delimiter), with optional value-`parse` callback (e.g. `-a1,2 -a3` → `(1,2,3)`)
- `@num`: parse numeric values, including human-readable SI/IEC suffixes (i.e. `10k` → `10_000`)
- `@obj`: parse dictionaries from multi-value options (e.g. `-eFOO=BAR -eBAZ=QUX` → `dict(FOO="BAR", BAZ="QUX")`)
- `@incs`/`@excs`: construct an [`Includes` or `Excludes`](#utz.rgx) object for regex-filtering of string arguments
- `@inc_exc`: combination of `@incs` and `@excs`; constructs an [`Includes` or `Excludes`](#utz.rgx) for regex-filtering of strings, from two (mutually-exclusive) `option`s
- `@opt`, `@arg`, `@flag`: wrappers for `click.{option,argument}`, `option(is_flag=True)`

Examples:
```python
# cli.py
from utz.cli import cmd, count, incs, multi, num, obj
from utz import Includes, Literal

@cmd  # Alias for `click.command`
@multi('-a', '--arr', parse=int, help="Comma-separated integers")
@obj('-e', '--env', help='Env vars, in the form `k=v`')
@incs('-i', '--include', 'includes', help="Only print `env` keys that match one of these regexs")
@num('-m', '--max-memory', help='Max memory size (e.g. "100m"')
@count('-v', '--verbosity', values=['warn', 'info', 'debug'], help='0x: "warn", 1x: "info", 2x: "debug"')
def main(
    arr: tuple[int, ...],
    env: dict[str, str],
    includes: Includes,
    max_memory: int,
    verbosity: Literal['warn', 'info', 'debug'],
):
    filtered_env = { k: v for k, v in env.items() if includes(k) }
    print(f"{arr} {filtered_env} {max_memory} {verbosity}")

if __name__ == '__main__':
    main()
```

Saving the above as `cli.py` and running will yield:
```bash
python cli.py -a1,2 -a3 -eAAA=111 -eBBB=222 -eccc=333 -i[A-Z] -m10k
# (1, 2, 3) {'AAA': '111', 'BBB': '222'} 10000 warn
python cli.py -m 1Gi -v
# () {} 1073741824 info
```

```python
from utz.cli import arg, cmd, inc_exc, multi
from utz.rgx import Patterns

@cmd
@inc_exc(
    multi('-i', '--include', help="Print arguments iff they match at least one of these regexs; comma-delimited, and can be passed multiple times"),
    multi('-x', '--exclude', help="Print arguments iff they don't match any of these regexs; comma-delimited, and can be passed multiple times"),
)
@arg('vals', nargs=-1)
def main(patterns: Patterns, vals: tuple[str, ...]):
    print(' '.join([ val for val in vals if patterns(val) ]))

if __name__ == '__main__':
    main()
```

Saving the above as `cli.py` and running will yield:
```bash
python cli.py -i a.,b aa bc cb c a AA B
# aa bc cb
python cli.py -x a.,b aa bc cb c a AA B
# c a AA B
```

See [`test_cli`] for more examples.

### [`utz.mem`]: [memray] wrapper <a id="utz.mem"></a>
Use [memray] to profile memory allocations, extract stats, flamegraph HTML, and peak memory use:

```python
from utz.mem import Tracker
from utz import iec
with (tracker := Tracker()):
    nums = list(sorted(range(1_000_000, 0, -1)))

peak_mem = tracker.peak_mem
print(f'Peak memory use: {peak_mem:,} ({iec(peak_mem)})')
# Peak memory use: 48,530,432 (46.3 MiB)
```

### [`utz.time`]: `Time` timer, `now`/`today` helpers <a id="utz.time"></a>

#### `Time`: minimal timer class

```python
from utz import Time, sleep

time = Time()
time("step 1")
sleep(1)
time("step 2")  # Ends "step 1" timer
sleep(1)
time()  # Ends "step 2" timer
print(f'Step 1 took {time["step 1"]:.1f}s, step 2 took {time["step 2"]:.1f}s.')
# Step 1 took 1.0s, step 2 took 1.0s.

# contextmanager timers can overlap/contain others
with time("run"):    # ≈2s
    time("sleep-1")  # ≈1s
    sleep(1)
    time("sleep-2")  # ≈1s
    sleep(1)

print(f'Run took {time["run"]:.1f}s')
# Run took 1.0s
```

#### `now`, `today`

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

<!-- `python scripts/time-slug-grid.py` -->
<table border="1" style="text-align: right">
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
      <td><code>A2kw7P</code></td>
      <td><code>+aYIh1</code></td>
      <td><code>:Kn&gt;H</code></td>
    </tr>
    <tr>
      <th>ds</th>
      <td><code>R7FCrj</code></td>
      <td><code>D8oM9b</code></td>
      <td><code>"tn_BH</code></td>
    </tr>
    <tr>
      <th>cs</th>
      <td><code>CCp7kK0</code></td>
      <td><code>/UpIuxG</code></td>
      <td><code>=Fc#jK</code></td>
    </tr>
    <tr>
      <th>ms</th>
      <td><code>dj4u83i</code></td>
      <td><code>MFSOKhy</code></td>
      <td><code>#8;HF8g</code></td>
    </tr>
    <tr>
      <th>us</th>
      <td><code>G6cozJjWb</code></td>
      <td><code>385u0dp8B</code></td>
      <td><code>D&gt;$y/9Hr</code></td>
    </tr>
  </tbody>
</table>

(generated by [`time-slug-grid.py`](scripts/time-slug-grid.py))

### [`utz.size`]: `humanize.naturalsize` wrapper <a id="utz.size"></a>
`iec` wraps `humanize.naturalsize`, printing IEC-formatted sizes by default, to 3 sigfigs:
```python
from utz import iec
iec(2**30 + 2**29 + 2**28 + 2**27)
# '1.88 GiB'
```

### [`utz.hash_file`]: hash file contents <a id="utz.hash_file"></a>

```python
from utz import hash_file
hash_file("path/to/file")  # sha256 by default
hash_file("path/to/file", 'md5')
```

### [`utz.ym`]: `YM` (year/month) class <a id="utz.ym"></a>
The `YM` class represents a year/month, e.g. `202401` for January 2024.
```python
from utz import YM
ym = YM(202501)  # Jan '25
assert ym + 1 == YM(202502)  # Add one month
assert YM(202502) - YM(202406) == 8  # subtract months
YM(202401).until(YM(202501))  # 202401, 202402, ..., 202412

# `YM` constructor accepts several representations:
assert all(ym == YM(202401) for ym in [
    YM(202401),
    YM('202401'),
    YM('2024-01'),
    YM(2024, 1),
    YM(y=2024, m=1),
    YM(dict(year=2022, month=12)),
    YM(YM(202401)),
])
```

### [`utz.cd`]: "change directory" contextmanager <a id="utz.cd"></a>
```python
from utz import cd
with cd('..'):  # change to parent dir
    ...
```

### [`utz.gzip`]: deterministic GZip helpers <a id="utz.gzip"></a>
```python
from utz import deterministic_gzip_open, hash_file
with deterministic_gzip_open('a.gz', 'w') as f:
    f.write('\n'.join(map(str, range(10))))
hash_file('a.gz')  # dfbe03625c539cbc2a2331d806cc48652dd3e1f52fe187ac2f3420dbfb320504
```

See also: [`test_gzip.py`].

### [`utz.s3`]: S3 utilities <a id="utz.s3"></a>

- `client()`: cached boto3 S3 client
- `parse_bkt_key(args: tuple[str, ...]) -> tuple[str, str]`: parse bucket and key from s3:// URL or separate arguments
- `get_etag(*args: str, err_ok: bool = False, strip: bool = True) -> str | None`: get ETag of S3 object
- `get_etags(*args: str) -> dict[str, str]`: get ETags for all objects with the given prefix
- `atomic_edit(...) -> Iterator[str]`: context manager for atomically editing S3 objects

```python
from utz import s3, pd

url = 's3://bkt/key.parquet'
# `url`'s ETag is snapshotted on initial read
with s3.atomic_edit(url) as out_path:
    df = pd.read_parquet(url)
    df.sort_index(inplace=True)
    df.to_parquet(out_path)
    # On contextmanager exit, `out_path` is uploaded to `url`, iff
    # `url`'s ETag hasn't changed (no concurrent update has occurred).
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
[`utz/setup.py`][`utz.setup`] provides defaults for various `setuptools.setup()` params:
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

### [`utz.docker`], [`utz.tmpdir`], etc. <a id="misc"></a>

Misc other modules:
- [bases][`utz.bases`]: encode/decode in various bases (62, 64, 90, …)
- [escape][`utz.escape`]: split/join on an arbitrary delimiter, with backslash-escaping; `utz.esc` escapes a specific character in a string.
- [ctxs][`utz.ctxs`]: compose `contextmanager`s
- [o][`utz.o`]: `dict` wrapper exposing keys as attrs (e.g.: `o({'a':1}).a == 1`)
- [docker][`utz.docker`]: DSL for programmatically creating Dockerfiles (and building images from them)
- [tmpdir][`utz.tmpdir`]: make temporary directories with a specific basename
- [ssh][`utz.ssh`]: SSH tunnel wrapped in a context manager
- [backoff][`utz.backoff`]: exponential-backoff utility
- [git][`utz.git`]: Git helpers, wrappers around [GitPython](https://gitpython.readthedocs.io/en/stable/)
- [pnds][`utz.pnds`]: [pandas](https://pandas.pydata.org/) imports and helpers

## Examples / Users <a id="examples"></a>
Some repos that use `utz`:
- [hudcostreets/nj-crashes][crashes utz]
- [hudcostreets/path][path utz]
- [neighbor-ryan/ctbk.dev][ctbk.dev utz]
- [runsascoded/bash-markdown-fence][bmdf utz]
- [runsascoded/juq][juq utz]
- [runsascoded/dffs][dffs utz]
- [runsascoded/ire/py][ire utz]
- [ryan-williams/arrayloader-benchmarks][alb utz]
- [ryan-williams/av-helpers][av utz]
- [ryan-williams/git-helpers][git utz]
- [ryan-williams/py-helpers][py utz]


[juq utz]: https://github.com/runsascoded/juq/blob/ae0b5f2de21ff66c390bd17dce052d19538b1653/requirements.txt#L2
[bmdf utz]: https://github.com/runsascoded/bash-markdown-fence/blob/8faccc73725a91e4c60481fe9086e45c1f7334bb/pyproject.toml#L12
[ctbk.dev utz]: https://github.com/neighbor-ryan/ctbk.dev/blob/a32aa11f3a1f9c075ec7e614e399c3bda157bfdb/requirements.txt#L21
[crashes utz]: https://github.com/hudcostreets/nj-crashes/blob/877c575645f4af3ab04af5d48335018934372464/requirements.txt#L32
[path utz]: https://github.com/hudcostreets/path/blob/64d72d13ff25cc289fc8ec9445bb92e9c489c9c2/pyproject.toml#L19
[ire utz]: https://gitlab.com/runsascoded/ire/py/-/blob/main/requirements.txt#L5
[alb utz]: https://github.com/ryan-williams/arrayloader-benchmarks/blob/100b4fe02b748743cca693e185859eb27bc965b9/requirements.txt#L23
[dffs utz]: https://github.com/runsascoded/dffs/blob/e99ba92df7d7b69e0f995f8e50a8cb98ecad0d02/requirements.txt#L2
[av utz]: https://github.com/search?q=repo%3Aryan-williams%2Fav-helpers%20utz&type=code
[py utz]: https://github.com/search?q=repo%3Aryan-williams%2Fpy-helpers%20utz&type=code
[git utz]: https://github.com/search?q=repo%3Aryan-williams%2Fgit-helpers%20utz&type=code

[pypi]: https://pypi.org/project/utz/
[extras]: https://github.com/runsascoded/utz/blob/main/setup.py#L3-L34
[`stdlb`]: https://pypi.org/project/stdlb/
[`subprocess`]: https://docs.python.org/3/library/subprocess.html

[`utz.backoff`]: src/utz/backoff.py
[`utz.bases`]: src/utz/bases.py
[`utz.cd`]: src/utz/cd.py
[`utz.cli`]: src/utz/cli.py
[`utz.collections`]: src/utz/collections.py
[`utz.context`]: src/utz/context.py
[`utz.ctxs`]: src/utz/context.py
[`utz.docker`]: src/utz/docker/
[`utz.env`]: src/utz/environ.py
[`utz.escape`]: src/utz/escape.py
[`utz.fn`]: src/utz/fn.py
[`utz.git`]: src/utz/git
[`utz.gzip`]: src/utz/gzip.py
[`utz.hash_file`]: src/utz/hash.py
[`utz.jsn`]: src/utz/jsn.py
[`utz.mem`]: src/utz/mem.py
[`utz.o`]: src/utz/o.py
[`utz.plot`]: src/utz/plots.py
[`utz.pnds`]: src/utz/pnds.py
[`utz.proc`]: src/utz/proc/__init__.py
[`utz.proc.aio`]: src/utz/proc/aio.py
[`utz.process`]: src/utz/process/__init__.py
[`utz.s3`]: src/utz/s3.py
[`utz.setup`]: src/utz/setup.py
[`utz.size`]: src/utz/size.py
[`utz.ssh`]: src/utz/ssh.py
[`utz.test`]: src/utz/test.py
[`utz.time`]: src/utz/time.py
[`utz.tmpdir`]: src/utz/tmpdir.py
[`utz.ym`]: src/utz/ym.py

[`test_cli`]: test/test_cli.py
[`test_collections.py`]: test/test_collections.py
[`test_context.py`]: test/test_context.py
[`test_env.py`]: test/test_env.py
[`test_fn.py`]: test/test_fn.py
[`test_gzip.py`]: test/test_gzip.py
[`test_jsn.py`]: test/test_jsn.py
[`test_parametrize.py`]: test/test_parametrize.py
[`test_proc.py`]: test/test_proc.py

[`on_conflict`]: src/utz/environ.py#L9-13
[`on_exit`]: src/utz/environ.py#L16-19

[`click`]: https://click.palletsprojects.com/
[memray]: https://bloomberg.github.io/memray/
[Pandas]: https://pandas.pydata.org/
[Plotly]: https://plotly.com/python/
[`pytest.mark.parametrize`]: https://docs.pytest.org/en/stable/how-to/parametrize.html
[`dataclass`]: https://docs.python.org/3/library/dataclasses.html

[hudcostreets/nj-crashes utz.plots]: https://github.com/search?q=repo%3Ahudcostreets%2Fnj-crashes%20utz.plot&type=code
[ryan-williams/arrayloader-benchmarks utz.plots]: https://github.com/search?q=repo%3Aryan-williams%2Farrayloader-benchmarks%20utz.plot&type=code

[tdbs parametrize_cases]: https://github.com/single-cell-data/TileDB-SOMA/blob/1.14.2/apis/python/tests/parametrize_cases.py
[roundtrips]: https://github.com/single-cell-data/TileDB-SOMA/blob/1.14.2/apis/python/tests/test_dataframe_io_roundtrips.py
