from utz.collections import *
from utz.test import raises


def test_singleton():
    assert singleton([123]) == 123
    with raises(ValueError, '2 elems found: 456,123'):
        singleton([123, 456])

    assert singleton([123, 123]) == 123
    with raises(ValueError, '2 elems found: 123,123'):
        singleton([123, 123], dedupe=False)

    with raises(ValueError, 'No elems found'):
        singleton([])

    assert singleton({ 'a': 1 }) == ('a', 1)
    with raises(ValueError, [ "2 elems found: ('a', 1),('b', 2)", "2 elems found: ('b', 2),('a', 1)", ]):
        singleton({ 'a': 1, 'b': 2, })
    with raises(ValueError, 'No elems found'):
        singleton({})

    assert singleton({ 'aaa': 111 }) == ('aaa', 111)
    assert singleton({ 'aaa': 111 }, key='aaa') == 111
    with raises(WrongKey, 'Expected bbb, actual aaa'):
        assert singleton({ 'aaa': 111 }, key='bbb') == 111
