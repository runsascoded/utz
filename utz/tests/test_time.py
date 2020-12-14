
from datetime import datetime
from pytz import UTC

from utz.time import now, today


def test_time():
    fmt = '%Y-%m-%dT%H:%M:%SZ'
    assert fmt == now.FMTS.iso

    nw = now()
    assert str(nw) == datetime.now().astimezone(UTC).strftime(fmt)

    fmt = '%Y-%m-%d'
    assert fmt == today.FMTS.iso
    tdy = today()
    assert str(tdy) == datetime.now().astimezone(UTC).strftime(fmt)
