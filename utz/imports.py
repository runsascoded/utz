#!/usr/bin/env python

# # imports
# Common Jupyter imports and helpers to wildcard import from other notebooks

# Helper for optional imports:

import contextlib
from contextlib import suppress
_try = suppress(ImportError, ModuleNotFoundError)


# ## stdlib
# Common imports (and associated helpers) from the Python standard library:

# ### Date/Time

import datetime
from datetime import datetime as dt, date
with _try: from dateutil.parser import parse
with _try: from pytz import UTC

now = dt.now()
ISO_DATE_FMT = '%Y-%m-%dT%H:%M:%S'
runtime = now.strftime(ISO_DATE_FMT)
today = now.strftime('%Y-%m-%d')


# ### Paths

from pathlib import Path
def mkdir(path, *args, exist_ok=True, **kwargs):
    os.makedirs(str(path), *args, exist_ok=exist_ok, **kwargs)
    return path

def mkpar(path, *args, **kwargs):
    if isinstance(path, Path):
        path.parent.mkdir(exist_ok=True, parents=True)
    else:
        mkdir(dirname(path))
    return path


# ### Other
import argparse
from argparse import ArgumentParser

import configparser
from configparser import ConfigParser

import dataclasses
from dataclasses import dataclass

import functools
try:
    # Python 3.8
    from functools import cached_property, singledispatchmethod
except ImportError:
    try:
        # Python ≤3.7; pip install cached-property
        from cached_property import cached_property
    except ImportError as e:
        pass

import functools
from functools import partial, lru_cache, namedtuple, reduce, singledispatch

from glob import glob

import hashlib
from hashlib import md5, sha256

import io
from io import BytesIO, StringIO

import itertools
from itertools import combinations, combinations_with_replacement, permutations

import json

import math
from math import acos, asin, atan, ceil, floor, pi, exp, log, log2, log10, cos, sin, sqrt, tan

import os
from os import chdir, cpu_count, environ as env, getcwd, listdir
from os.path import abspath, basename, dirname, exists, expanduser, expandvars, isabs, isdir, isfile, islink, join, normpath, realpath, relpath, sep, splitext

import re
from re import match, fullmatch, IGNORECASE, MULTILINE, DOTALL, search, split, sub

import shlex
import shutil
from shutil import copy, copyfileobj, move, rmtree

import subprocess
from subprocess import check_call, check_output, CalledProcessError, DEVNULL, PIPE, Popen

import sys
from sys import stdout, stderr, executable as python, exit, platform

import tempfile
from tempfile import NamedTemporaryFile, TemporaryDirectory, TemporaryFile

import time
from time import sleep

import typing
from typing import Any, Callable, Collection, Generator, Iterable, Iterator, List, Optional, Sequence, Set, Sized, Union

# ## Sibling modules
# Import other utilities from this repo:

from . import process
from .process import *

with _try:
    from . import pnds
    from .pnds import *

from .cd import cd
from . import docker
from .o import o
from .use import use

with _try:
    from .git import Git, Repo, make_repo

from .args_parser import *

from .context import *

with _try:
    from .collections import coerce, singleton


# ## Optional Modules

# joblib: easy parallelization
with _try:
    from joblib import Parallel, delayed
    parallel = Parallel(n_jobs=cpu_count())

# yaml
with _try:
    import yaml
    # Fix a bad default in PyYAML (cf. https://github.com/yaml/pyyaml/issues/110)
    yaml.dump = partial(yaml.dump, sort_keys=False)
    yaml.safe_dump = partial(yaml.safe_dump, sort_keys=False)

# requests
with _try:
    from requests import           get as   GET,          post as  POST,           put as   PUT,         patch as PATCH


# ## PyData / Scientific Python

with _try:
    import numpy as np
    from numpy import concatenate, array, ndarray, matrix, nan

with _try: import seaborn as sns
with _try: import matplotlib.pyplot as plt
with _try: from scipy.sparse import spmatrix, coo_matrix, csr_matrix, csc_matrix

