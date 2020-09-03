import pytest
from pytest import raises
from utz.o import o

def test_kwargs():
    o1 = o(a=1,b=2)
    assert o1.a == 1
    assert o1.b == 2
    with raises(AttributeError):
        o1.c


def test_dict():
    x={'c':3,'d':4}
    o2 = o(x)

    assert o2.c == 3
    assert o2.d == 4

    # mutations in each direction
    x['e'] = 5
    assert o2.e == 5

    o2.c = 'ccc'
    assert x['c'] == 'ccc'

    # membership
    assert 'c' in o2
    assert not 'z' in o2

    # str/repr
    assert str(o2) == "{'c': 'ccc', 'd': 4, 'e': 5}"
    assert repr(o2) == "{'c': 'ccc', 'd': 4, 'e': 5}"


def test_nested():
    o1 = o(a={'b':1})
    o2 = o(a={'b':1})
    o3 = o(a=o(b=1))

    assert o1 is not o2
    assert o1 is not o3
    assert o2 is not o3

    def eq(l, r):
        assert l == r
        assert r == l

    def ne(l, r):
        assert l != r
        assert r != l

    eq(o1, o2)
    eq(o1, o3)
    eq(o2, o3)

    eq(o1, {'a':{'b':1}})
    eq(o1.a, {'b':1})
    eq(o1.a, o(b=1))

    ne(o1, o(a=o(b=2)))
    ne(o1, o(a=o(b=1,c=3)))
    ne(o1, o(a=o(b=1),c=3))

    assert o1.get('b', 'default') == 'default'
    assert o1.get('a', 'default') == o(b=1)
    assert o1('a', 'b', default='default') == 1
    assert o1('a', 'c', default='default') == 'default'
    assert o1('a', 'c') == None
    assert o1('a', 'c', 'b') == None

    assert o1.a.b == 1
    with raises(AttributeError):
        o1.a.b.c
    with raises(AttributeError):
        o1.a.c


def test_list():
    _o = o(a=1, b=2)
    assert list(iter(_o)) == [ 'a', 'b' ]
    assert list(_o.items()) == [ ('a',1), ('b',2) ]
