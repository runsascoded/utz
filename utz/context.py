# # Context Manager utilities

from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager
from typing import ContextManager, Generator, Sequence, TypeVar

T = TypeVar("T")

# Shorthand for common return type of ``@contextmanager``-decorated functions
Yield = Generator[T, None, None]


def contexts(*ctxs: ContextManager | Sequence[ContextManager]) -> ContextManager:
    """Compose context managers."""
    ctxs = [
        ctx
        for _ctxs in ctxs
        for ctx in (
            _ctxs
            if isinstance(_ctxs, Sequence)
            else [_ctxs]
        )
    ]

    @contextmanager
    def fn(ctxs):
        if not ctxs:
            yield
        else:
            [ ctx, *rest ] = ctxs
            with ctx as v, fn(rest) as vs:
                yield [ v, *(vs if vs else []) ]

    return fn(ctxs)


ctxs = contexts


class catch(AbstractContextManager):
    """``contextmanager`` that catches+verifies ``Exception``s"""
    def __init__(self, *excs):
        self.excs = excs

    def __exit__(self, exc_type, exc_value, traceback):
        if not exc_type:
            if len(self.excs) == 1:
                raise AssertionError(f'No {self.excs[0].__name__} was thrown')
            else:
                raise AssertionError(f'None of {",".join([e.__name__ for e in self.excs])} were thrown')
        
        if not [ isinstance(exc_value, exc) for exc in self.excs ]:
            raise exc_value

        return True


# ## `no`: context manager for verifying `NameError`s (undefined variable names)
no = catch(NameError)
