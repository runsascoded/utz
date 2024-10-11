from __future__ import annotations

from inspect import getfullargspec
from typing import Callable, Sequence

Deco = Callable[[Callable], Callable]


def decos(*args: Deco | Sequence[Deco]):
    """Compose decorators."""
    decos = [ deco for decos in args for deco in decos ]

    def _fn(fn):
        for deco in reversed(decos):
            fn = deco(fn)
        return fn

    return _fn


def args(fn, kwargs):
    """Filter kwargs to match function signature."""
    spec = getfullargspec(fn)
    args = spec.args
    return { k: v for k, v in kwargs.items() if k in args }


def call(fn, *_args, **kwargs):
    """Call a function with only the kwargs that it is able to receive."""
    return fn(*_args, args(fn, **kwargs))
