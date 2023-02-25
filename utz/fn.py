from inspect import getfullargspec
from typing import Collection


def decos(*decs):
    if len(decs) == 1 and isinstance(decs, Collection):
        decs = decs[0]

    def _fn(fn):
        for dec in reversed(decs):
            fn = dec(fn)
        return fn

    return _fn


def args(fn, kwargs):
    spec = getfullargspec(fn)
    args = spec.args
    return { k: v for k, v in kwargs.items() if k in args }
