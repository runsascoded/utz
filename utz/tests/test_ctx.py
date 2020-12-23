
import pytest
from tempfile import NamedTemporaryFile

from utz import ctxs, exists, contextmanager, AbstractContextManager


class TestCtx(AbstractContextManager):
    instances = []
    def __init__(self, n, raise_on=None):
        self.n = n
        self.state = 'init'
        self.raise_on = raise_on
        self.instances += [self]

    def __enter__(self):
        self.state = 'entering'
        if self.raise_on == 'enter':
            raise Exception('error during __enter__')
        self.state = 'entered'
        return self.n

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.state = 'exiting'
        if self.raise_on == 'exit':
            raise Exception('error during __exit__')
        self.state = 'exited'


def test_ctxs_tempfiles():
    files = [
        NamedTemporaryFile(suffix='111'),
        NamedTemporaryFile(suffix='222'),
        NamedTemporaryFile(suffix='333'),
    ]
    with ctxs(files) as (f1, f2, f3):
        assert [ exists(f.name) for f in [f1, f2, f3] ] == [True]*3
        assert [ f.name for f in files ] == [ f.name for f in [f1, f2, f3] ]

    assert [ exists(f.name) for f in files ] == [False]*3


def test_ctxs_complex():
    f1 = NamedTemporaryFile()
    f2 = NamedTemporaryFile()
    f3 = NamedTemporaryFile()
    for f in [ f1, f2, f3 ]:
        assert exists(f.name)

    with pytest.raises(Exception) as e:
        with ctxs([
            f1,
            TestCtx(111), TestCtx(222),
            TestCtx(333, raise_on='enter'),
            TestCtx(444), f2,
            TestCtx(555, raise_on='exit'),
            TestCtx(666), f3,
        ]) as (F1, c1, c2, c3, c4, F2, c5, c6, F3):
            raise AssertionError  # we never get here bc c3 raises during __enter__

    # NamedTemporaryFile() creates temp file during __init__, not __enter__! Unfortunate…
    assert [ exists(f.name) for f in [ f1, f2, f3 ] ] == [ False, True, True, ]
    f2.close()
    f3.close()
    assert [ exists(f.name) for f in [ f1, f2, f3 ] ] == [ False, False, False, ]

    assert dict([ (i.n, i.state) for i in TestCtx.instances ]) == {
        111: 'exited', 222: 'exited',
        333: 'entering',
        444: 'init', 555: 'init', 666: 'init',
    }
