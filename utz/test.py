from contextlib import contextmanager
import pytest


@contextmanager
def raises(exc, msg):
    with pytest.raises(exc) as ex:
        yield
    assert str(ex.value) == msg

