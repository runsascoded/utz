from utz.collections import *
from utz.test import raises

def test_singleton():
    assert singleton([123]) == 123
    with raises(ValueError, '2 elems found: 456,123'):
        singleton([123,456])

    assert singleton([123,123]) == 123
    with raises(ValueError, '2 elems found: 123,123'):
        singleton([123,123], dedupe=False)

    with raises(ValueError, 'No elems found'):
        singleton([])
