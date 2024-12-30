import json
from pytest import raises
from utz import o


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

    assert o1.get('b') is None
    assert o1.get('a') == o(b=1)
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


def test_serialization():
    _o = o(a=1, b={'c':3})
    _o.update(d=4)
    assert json.dumps(_o) == '{"a": 1, "b": {"c": 3}, "d": 4}'


def test_merge():
    d1 = { 'a':1,'b':2 }
    d2 = { 'a':11,'c':33 }
    o1 = o(d1).merge(d2)
    assert dict(o1) == { 'a':11,'b':2,'c':33 }
    assert (o1.a, o1.b, o1.c) == (11, 2, 33)
    assert d1 == {'a':1,'b':2}
    assert d2 == { 'a':11,'c':33 }


def test_merge_static():
    d1 = { 'a':1,'b':2 }
    d2 = { 'a':11,'c':33 }
    o1 = o.merge(d1, d2)
    assert dict(o1) == { 'a':11,'b':2,'c':33 }
    assert (o1.a, o1.b, o1.c) == (11, 2, 33)
    assert d1 == {'a':1,'b':2}
    assert d2 == { 'a':11,'c':33 }


def test_update():
    o1 = o(a=1,b=2)
    o1.update(b='bbb',c=3,d=4)
    assert dict(o1) == { 'a':1,'b':'bbb','c':3,'d':4 }
