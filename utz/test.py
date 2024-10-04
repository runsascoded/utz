from contextlib import contextmanager
import pytest


@contextmanager
def raises(exc, msg):
    with pytest.raises(exc) as exc:
        yield
    if isinstance(msg, list):
        msgs = msg
        assert str(exc.value) in msgs
    else:
        assert str(exc.value) == msg, f'{exc.value} != {msg}'

