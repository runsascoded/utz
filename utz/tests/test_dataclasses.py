from dataclasses import dataclass, asdict
from typing import Optional, List

from utz.dataclasses import from_dict
from utz.test import raises


@dataclass
class A:
    s: str
    n: int
    b: Optional[bool] = None


@dataclass
class B:
    f: float
    arr: List[A]
    obj: dict[str, A]


@dataclass
class O1:
    obj: Optional[dict[int, Optional[A]]] = None


@dataclass
class O2:
    arr: Optional[List[Optional[A]]] = None


class C:
    s: str
    n: int

    def __init__(self, s, n):
        self.s = s
        self.n = n


@dataclass
class D:
    c: C


def check(dc):
    assert from_dict(dc.__class__, asdict(dc)) == dc


def test_roundtrips():
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
    check(O1())
    check(O1({111: A('aa', 11), 222: None}))
    check(O2())
    check(O2([A('aa', 11), None, A('bb', 22)]))


def test_bad_dicts():
    with raises(TypeError, "A.__init__() missing 1 required positional argument: 'n'"):
        from_dict(A, { 's': 'aa' })

    with raises(KeyError, "'c'"):
        from_dict(A, { 's': 'aa', 'n': 11, 'c': 'invalid key' })

    with raises(ValueError, "Invalid value '!!!' (expected one of ['bool', 'NoneType'])"):
        from_dict(A, { 's': 'aa', 'n': 11, 'b': '!!!' })

    with raises(ValueError, "111 (int) is not of expected type float"):
        from_dict(B, { 'f': 111, 'arr': [], 'obj': {} })


def test_non_dataclasses():
    with raises(TypeError, '`fields` must be called with a dataclass type or instance, not C'):
        from_dict(C, { 's': 'aa', 'n': 11 })

    with raises(TypeError, '`fields` must be called with a dataclass type or instance, not C'):
        from_dict(D, { 'c': { 's': 'aa', 'n': 11 } })

