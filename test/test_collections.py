from utz.collections import *
from utz.test import raises


def test_singleton():
    assert singleton([123]) == 123
    with raises(Expected1FoundN, '2 elems found: 123,456'):
        singleton([123, 456])

    assert singleton([123, 123], dedupe=True) == 123
    with raises(Expected1FoundN, '2 elems found: 123,123'):
        singleton([123, 123], dedupe=False)

    with raises(Expected1Found0, 'No elems found'):
        singleton([])

    assert singleton([["aaa"]]) == ["aaa"]
    assert solo([["aaa"]]) == ["aaa"]

    assert singleton({ 'a': 1 }) == ('a', 1)
    with raises(Expected1FoundN, r"2 elems found: (?:\('a', 1\),\('b', 2\)|\('b', 2\),\('a', 1\))"):
        singleton({ 'a': 1, 'b': 2, })
    with raises(Expected1Found0, 'No elems found'):
        singleton({})

    assert singleton({ 'aaa': 111 }) == ('aaa', 111)
    assert singleton({ 'aaa': 111 }, key='aaa') == 111
    with raises(WrongKey, 'Expected key "bbb", found "aaa"'):
        assert singleton({ 'aaa': 111 }, key='bbb') == 111

    assert solo([ { 'a': 1, 'b': 2 } ]) == { 'a': 1, 'b': 2 }
    with raises(Expected1FoundN, '3 elems found: 1,1,1'):
        assert solo([ 1, 1, 1 ]) == 1
    with raises(Expected1FoundN, '3 elems found: 1,2,1'):
        assert solo([ 1, 2, 1 ])
    with raises(Expected1FoundN, '3 elems found: 1,1,2'):
        assert solo([ 1, 1, 2 ])

    assert solo([2, 3, 4], pred=lambda n: n % 2) == 3
    assert solo([{'a': 1}, {'b': 2}], pred=lambda o: 'a' in o) == {'a': 1}
