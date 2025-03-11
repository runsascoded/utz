import asyncio
from asyncio import sleep

from contextlib import contextmanager, asynccontextmanager

from pytest import raises
from tempfile import NamedTemporaryFile

from utz import exists, AbstractContextManager, contexts, acontexts, Time


class EnterException(Exception): pass
class ExitException(Exception): pass


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
            raise EnterException
        self.state = 'entered'
        return self.n

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.state = 'exiting'
        if self.raise_on == 'exit':
            raise ExitException
        self.state = 'exited'


def test_contexts_tempfiles():
    files = [
        NamedTemporaryFile(suffix='111'),
        NamedTemporaryFile(suffix='222'),
        NamedTemporaryFile(suffix='333'),
    ]
    with contexts(files) as fds:
        assert [ exists(f.name) for f in fds ] == [True] * len(files)
        assert [ f.name for f in files ] == [ f.name for f in fds ]

    assert [ exists(f.name) for f in files ] == [False] * len(files)


def test_contexts_complex():
    f1 = NamedTemporaryFile()
    f2 = NamedTemporaryFile()
    f3 = NamedTemporaryFile()
    for f in [ f1, f2, f3 ]:
        assert exists(f.name)

    with raises(EnterException):
        with contexts(
            f1,
            TestCtx(111),
            TestCtx(222),
            TestCtx(333, raise_on='enter'),
            TestCtx(444),
            f2,
            TestCtx(555, raise_on='exit'),
            TestCtx(666),
            f3,
        ) as (F1, c1, c2, c3, c4, F2, c5, c6, F3):
            raise AssertionError  # we never get here bc c3 raises during __enter__

    # NamedTemporaryFile() creates temp file during __init__, not __enter__! Unfortunate…
    assert [ exists(f.name) for f in [ f1, f2, f3 ] ] == [ False, True, True, ]
    f2.close()
    f3.close()
    assert [ exists(f.name) for f in [ f1, f2, f3 ] ] == [ False, False, False, ]

    assert { i.n: i.state for i in TestCtx.instances } == {
        111: 'exited',
        222: 'exited',
        333: 'entering',
        444: 'init',
        555: 'init',
        666: 'init',
    }


n = 2


@contextmanager
def double():
    global n
    n = n * 2
    yield


@contextmanager
def to_str():
    global n
    n = str(n)
    yield


def test_contexts_order():
    global n
    n = 2
    with contexts(double(), to_str()) as (_n, _s):
        assert n == '4'
    n = 2
    with contexts(to_str(), double()) as (_s, _n):
        assert n == '22'


@asynccontextmanager
async def exit_sleep(s: float):
    try:
        yield
    finally:
        await sleep(s)


async def _test_acontexts(time: Time):
    async with acontexts(
        exit_sleep(0.1),
        exit_sleep(0.1),
        exit_sleep(0.1),
    ):
        with time("inside"):
            pass


def test_acontexts():
    time = Time()
    with time("acontexts"):
        asyncio.run(_test_acontexts(time))

    inside = time.times["inside"]
    assert 0 < inside < 1e-5
    total = time.times["acontexts"]
    assert 0.1 < total < 0.11
