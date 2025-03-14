from functools import wraps

from utz import recvs, call


def fn1(a, b):
    return dict(a=a, b=b)


@wraps(fn1)
def fn2(a, c, **kwargs):
    return dict(a=a, c=c, kwargs=kwargs)


def test_recvs():
    assert recvs(fn1, 'a')
    assert recvs(fn1, 'b')
    assert not recvs(fn1, 'c')

    assert recvs(fn2, 'a')
    assert recvs(fn2, 'b')
    assert recvs(fn2, 'c')
    assert not recvs(fn2, 'd')


def test_call():
    assert call(fn1, a=1, b=2) == dict(a=1, b=2)
    assert call(fn1, a=1, b=2, c=3) == dict(a=1, b=2)

    assert call(fn2, a=1, b=2, c=3) == dict(a=1, c=3, kwargs=dict(b=2))
    assert call(fn2, a=1, b=2, c=3, d=4) == dict(a=1, c=3, kwargs=dict(b=2))
