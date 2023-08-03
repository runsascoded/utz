# Optional-import helper
from .imports import _try

from os import environ as env

# Import most of the Python standard library
with _try: from stdlb import *

# ### Date/Time
with _try: from dateutil.parser import parse
with _try: from pytz import UTC
from .time import now, today

# Import other utilities from this repo:

from .backoff import backoff
from .bases import b62, b64, b90
from .path import mkdir, mkpar
from os import path
from .tmpdir import tmpdir

from . import process
from .process import *

from . import fn
from .fn import decos, args

with _try:
    from . import pnds
    from .pnds import *

from .cd import cd

from . import docker
from .docker.dsl import *

from .o import o
from .use import use
with _try:
    from .ym import YM
    from .ymd import YMD

with _try:
    from git import Git, Repo
    from .git import make_repo

from .git import github

from .context import *

with _try:
    from .collections import coerce, singleton, only, is_subsequence

from .defaultdict import DefaultDict, Unset

# ## Optional Modules

# joblib: easy parallelization
with _try:
    from joblib import Parallel, delayed
from .parallel import parallel

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

__version__ = pkg_version('utz')
