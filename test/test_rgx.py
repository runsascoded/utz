from __future__ import annotations

import re
from re import Pattern

from utz.rgx import Includes, Excludes


def check(
    pats: list[str],
    trues: list[str],
    falses: list[str],
    **kwargs,
):
    def _check(pats: list[str | Pattern]):
        incs = Includes(pats, **kwargs)
        excs = Excludes(pats, **kwargs)
        for val in trues:
            assert incs(val)
            assert not excs(val)

        for val in falses:
            assert not incs(val)
            assert excs(val)

    _check(pats)
    _check([ re.compile(pat) for pat in pats ])


def test_patterns():
    check(
        ['a.', 'b'],
        ['aa', 'bc', 'cb'],
        ['c', 'a', 'AA', 'B'],
    )


def test_ignorecase():
    check(
        ['a.', 'b'],
        ['aa', 'AA', 'B', 'bc', 'cb'],
        ['c', 'a'],
        flags=re.I,
    )


def test_fullmatch():
    check(
        ['a.', 'b'],
        ['aa', 'b'],
        ['bc', 'c', 'cb', 'a', 'AA', 'B'],
        search=False,
    )
