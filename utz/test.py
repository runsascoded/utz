from contextlib import contextmanager
import pytest


@contextmanager
def raises(exc, msg):
    with pytest.raises(exc) as ex:
        yield
    if isinstance(msg, list):
        msgs = msg
        assert str(ex.value) in msgs
    else:
        assert str(ex.value) == msg, f'{ex.value} != {msg}'

