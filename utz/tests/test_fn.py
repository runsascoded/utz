from functools import wraps

from utz import recvs


def fn1(a, b):
    pass


@wraps(fn1)
def fn2(a, c, **kwargs):
    pass


def test_recvs():
    assert recvs(fn1, 'a')
    assert recvs(fn1, 'b')
    assert not recvs(fn1, 'c')

    assert recvs(fn2, 'a')
    assert recvs(fn2, 'b')
    assert recvs(fn2, 'c')
    assert not recvs(fn2, 'd')
