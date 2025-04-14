from __future__ import annotations

import sys
from dataclasses import asdict, dataclass
from typing import Union

import pytest

from utz.dataclasses import from_dict
from utz.test import raises


@dataclass
class A1:
    s: str
    n: int
    b: bool | None = None


@dataclass
class B1:
    f: float
    arr: list[A1]
    obj: dict[str, A1]


@dataclass
class Obj1:
    obj: dict[int, A1 | None] | None = None


@dataclass
class Arr1:
    arr: list[A1 | None] | None = None


@dataclass
class A2:
    s: str
    n: int
    b: Union[bool, None] = None


@dataclass
class B2:
    f: float
    arr: list[A2]
    obj: dict[str, A2]


@dataclass
class Obj2:
    obj: Union[dict[int, Union[A2, None]], None] = None


@dataclass
class Arr2:
    arr: Union[list[Union[A2, None]], None] = None


def check(dc):
    assert from_dict(dc.__class__, asdict(dc)) == dc


@pytest.mark.parametrize(
    "A,B,Obj,Arr",
    [
        *([(A1, B1, Obj1, Arr1)] if sys.version_info >= (3, 10) else []),
        (A2, B2, Obj2, Arr2),
    ]
)
def test_roundtrips(A: type, B: type, Obj: type, Arr: type):
    check(A('aa', 11))
    check(A('aa', 11, True))
    check(
        B(
            1.11,
            [
                A('aa', 11),
                A('bb', 22),
            ],
            {
                'ccc': A('cc', 33),
                'ddd': A('dd', 44),
            }
        )
    )
    check(B(2.22, [], {}))
    check(Obj())
    check(Obj({111: A('aa', 11), 222: None}))
    check(Arr())
    check(Arr([A('aa', 11), None, A('bb', 22)]))


def test_bad_dicts():
    # Python 3.9 doesn't include the "A." at the start
    with raises(TypeError, r"(?:A.)?__init__\(\) missing 1 required positional argument: 'n'"):
        from_dict(A2, { 's': 'aa' })

    with raises(KeyError, "'c'"):
        from_dict(A2, { 's': 'aa', 'n': 11, 'c': 'invalid key' })

    with raises(ValueError, ["Invalid value '!!!' (expected one of ['bool', 'NoneType'])"]):
        from_dict(A2, { 's': 'aa', 'n': 11, 'b': '!!!' })

    with raises(ValueError, ["111 (int) is not of expected type float"]):
        from_dict(B2, { 'f': 111, 'arr': [], 'obj': {} })


class C:
    s: str
    n: int

    def __init__(self, s, n):
        self.s = s
        self.n = n


@dataclass
class D:
    c: C


def test_non_dataclasses():
    with raises(TypeError, '`fields` must be called with a dataclass type or instance, not C'):
        from_dict(C, { 's': 'aa', 'n': 11 })

    with raises(TypeError, '`fields` must be called with a dataclass type or instance, not C'):
        from_dict(D, { 'c': { 's': 'aa', 'n': 11 } })
