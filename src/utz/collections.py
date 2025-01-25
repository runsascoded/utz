from __future__ import annotations

from typing import Callable, Iterable

try:
    from pandas import Series
except ImportError:
    Series = None
from math import exp, log
from sys import stderr


class Expected1Found0(ValueError): pass


class Expected1FoundN(ValueError):
    def __init__(self, name, num, elems, show_num=10):
        self.name = name
        self.num = num
        self.elems = elems
        self.msg = f'{len(elems)} {name} found: {",".join([str(elem) for elem in list(elems)[:show_num]])}'
        super().__init__(self.msg)


class WrongKey(ValueError):
    def __init__(self, expected, actual):
        self.expected = expected
        self.actual = actual
        self.msg = f'Expected key "{expected}", found "{actual}"'
        super().__init__(self.msg)


class WrongKeys(ValueError):
    def __init__(self, expected, actual):
        self.missing = set(expected).difference(actual)
        self.extra = set(actual).difference(expected)
        self.msg = f'Expected {expected}, actual {actual}. Extra: {self.extra}, missing: {self.missing}'
        super().__init__()


def singleton(
    elems: Iterable,
    pred: Callable = None,
    empty_ok: bool = False,
    name: str = 'elems',
    dedupe: bool | None = None,
    key: str | None = None,
):
    """Verify ``elems`` contains exactly one element, and return it.

    :param elems: Iterable of elements to check
    :param pred: Optional predicate to apply to each element
    :param empty_ok: If ``True``, return ``None`` if no matching element is found
    :param name: Name for elements of ``elems``, used in error messages
    :param dedupe: If ``True``, remove duplicates from ``elems`` before checking its length
    :param key: If ``elems`` is a dict, return the value for this key
    """
    if Series and isinstance(elems, Series):
        elems = elems.unique().tolist()
    elif isinstance(elems, dict):
        if key:
            keys = list(elems.keys())
            actual_key = singleton(keys)
            if actual_key != key:
                raise WrongKey(key, actual_key)
            return elems[key]
        else:
            elems = elems.items()
    if pred:
        elems = [elem for elem in elems if pred(elem)]
    else:
        if dedupe is None:
            if elems and isinstance(next(iter(elems)), dict):
                dedupe = False
            else:
                dedupe = True
        if dedupe:
            elems = set(elems)
    if not elems:
        if empty_ok:
            return None
        raise Expected1Found0(f'No {name} found')
    if len(elems) > 1:
        raise Expected1FoundN(name, len(elems), elems)
    [elem] = elems
    return elem


solo = singleton
"""Alias for ``singleton``."""


def only(obj, *keys):
    if not keys:
        return obj
    [ keys, *rest ] = keys
    key, scalar = None, False
    if isinstance(keys, str):
        key, scalar = keys, True
        keys = [key]
    actual_keys = list(sorted(obj.keys()))
    expected_keys = list(sorted(keys))
    if expected_keys != actual_keys:
        raise WrongKeys(expected_keys, actual_keys)
    if scalar:
        return only(obj[key], *rest)
    else:
        return [ only(obj[k], *rest) for k in keys ]


def coerce(value, choices, ε=1e-2, multi_ok=False, errors='raise', warn=True):
    assert errors in ['raise', 'coerce', 'ignore', ]
    elems = sorted(
        [
            dict(
                ratio=abs(log(value / choice)),
                choice=choice
            )
            for choice in choices
        ],
        key=lambda r: r['ratio']
    )
    log_ε = log(1 + ε)
    valids = [elem for elem in elems if elem['ratio'] <= log_ε]
    best = elems[0]
    choice = best['choice']
    if not valids:
        msg = f'Best choice {choice} for value {value} has error {exp(best["ratio"]) - 1} > {ε}'
        if errors == 'raise':
            raise ValueError(msg)
        if warn:
            stderr.write(msg + '\n')
        if errors == 'coerce':
            try:
                from numpy import nan
            except ImportError:
                nan = None
            return nan
        else:
            return value
    if len(valids) > 1 and not multi_ok:
        raise ValueError(
            '%d choices passed ε<%f filter:\n\t%s' % (
                len(valids),
                ε,
                "\n\t".join([str(r["choice"]) for r in valids]),
            )
        )
    return best['choice']


def is_subsequence(seq, s):
    if not seq:
        return True
    [ ch, *rest ] = seq
    idx = s.find(ch)
    return is_subsequence(rest, s[(idx+1):]) if idx >= 0 else False
