
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

    n1 = now()
    n2 = now()
    n3 = now()
    Δ1 = float(n2) - float(n1)
    Δ2 = float(n3) - float(n2)
    assert 0 <= Δ1 and Δ1 < .1, Δ1
    assert 0 <= Δ2 and Δ2 < .1, Δ2

    Δ1 = int(n2) - int(n1)
    Δ2 = int(n3) - int(n2)
    assert 0 <= Δ1 and Δ1 <= 1, Δ1
    assert 0 <= Δ2 and Δ2 <= 1, Δ2
    assert Δ1 == 0 or Δ2 == 0
