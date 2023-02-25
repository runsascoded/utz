#!/usr/bin/env python

from pandas import Series
from math import exp, log
from numpy import nan
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
        self.msg = f'Expected {expected}, actual {actual}'
        super().__init__(self.msg)


class WrongKeys(ValueError):
    def __init__(self, expected, actual):
        self.missing = set(expected).difference(actual)
        self.extra = set(actual).difference(expected)
        self.msg = f'Expected {expected}, actual {actual}. Extra: {self.extra}, missing: {self.missing}'
        super().__init__()


def singleton(elems, fn=None, empty_ok=False, name='elems', dedupe=True, key=None):
    if isinstance(elems, Series):
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
    if fn:
        elems = [elem for elem in elems if fn(elem)]
    else:
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
