from __future__ import annotations

from inspect import getfullargspec
from typing import Callable, Sequence

Deco = Callable[[Callable], Callable]


def decos(*args: Deco | Sequence[Deco]):
    """Compose decorators."""
    decos = [
        deco
        for decos in args
        for deco in (decos if isinstance(decos, Sequence) else [decos])
    ]

    def _fn(fn):
        for deco in reversed(decos):
            fn = deco(fn)
        return fn

    return _fn


def args(fn, kwargs):
    """Filter kwargs to match function signature."""
    return { k: v for k, v in kwargs.items() if recvs(fn, k) }


def call(fn, *_args, **kwargs):
    """Call a function with only the kwargs that it is able to receive."""
    return fn(*_args, **args(fn, kwargs))


def recvs(fn: Callable, k: str) -> bool:
    """True if ``fn`` takes a kwarg ``k``, or a var-kwargs and a wrapped descendant function does."""
    spec = getfullargspec(fn)
    if k in spec.args or k in spec.kwonlyargs:
        return True
    if spec.varkw:
        wrapped = getattr(fn, '__wrapped__', None)
        if wrapped:
            return recvs(wrapped, k)
    return False
