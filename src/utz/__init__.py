"""
"Export" most members of this module, as well as the standard library (c/o `stdlb`). Add:

```python
from utz import *
```

to notebooks (or your `$PYTHONSTARTUP` script) to save lots of `import` boilerplate.
"""

# Optional-import helper
from .imports import _try

from os import environ
from .environ import env

# Import most of the Python standard library
# `_try` wrap helps ensure `utz[setup]` can install properly
with _try: from stdlb import *

# ### Date/Time
with _try: from dateutil.parser import parse
with _try: from pytz import UTC
from .time import now, today, Time, utc

# ### Jupyter
with _try: from IPython.display import HTML, Image, Markdown, display

# Import other utilities from this repo:

from .backoff import backoff
from .bases import b26u, b26l, b36u, b36l, b52, b62, b64, b90
from .hash import hash_file, HashName
from .path import mkdir, mkpar
from .rgx import Patterns, Includes, Excludes
from os import path
from .tmpdir import tmpdir

from . import proc, process
from .process import *

from .escape import esc

from . import fn
from .fn import args, call, decos, recvs

from .gzip import deterministic_gzip_open, DeterministicGzipFile

from . import jsn
from .jsn import Encoder

from . import size
from .size import iec

with _try:
    from . import pnds
    from .pnds import *

from .cd import cd

from . import docker
from .docker.dsl import *

# `utz.Yield` is used by some modules below, e.g. `utz.ym`
from .context import *

from .o import o, rev
from .use import use
from .ym import YM
from .ymd import YMD

with _try:
    from git import Git, Repo
    from .git import make_repo

from .git import github

with _try:
    from .collections import coerce, only, is_subsequence, singleton, solo

from .defaultdict import DefaultDict, Unset

from .test import parametrize, raises

# ## Optional Modules

# joblib: easy parallelization
with _try:
    from joblib import Parallel, delayed
from .parallel import parallel

try:
    from . import plots
    from .plots import plot
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    pass

# yaml
with _try:
    import yaml
    # Fix a bad default in PyYAML (cf. https://github.com/yaml/pyyaml/issues/110)
    from functools import partial
    yaml.dump = partial(yaml.dump, sort_keys=False)
    yaml.safe_dump = partial(yaml.safe_dump, sort_keys=False)

# requests
with _try:
    from requests import \
        get as   GET, \
        post as  POST, \
        put as   PUT, \
        patch as PATCH

# ## PyData / Scientific Python

with _try:
    import numpy as np
    from numpy import concatenate, array, ndarray, matrix, nan

with _try: import seaborn as sns
with _try: import matplotlib.pyplot as plt
with _try: from scipy.sparse import spmatrix, coo_matrix, csr_matrix, csc_matrix

from .version import git_version, pkg_version
