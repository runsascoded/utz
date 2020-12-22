
from datetime import datetime
import pytest
from pytz import UTC

from utz import b62, b64, b90, now, o, today
to_dt = now.to_dt

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


@pytest.mark.parametrize("debug",[False])  # set to true to print the expected values for new test cases
@pytest.mark.parametrize(
    "codec,cases,t2021",
    (
        (
            b64,
            (
                o(unit='s', ch='+', len=6, first_until='2038-08-04 05:32:48', len_until='4182-03-13 23:28:00'),
                o(unit='ms', ch='K', len=7, first_until='2022-04-19 04:50:27.008000', len_until='2111-08-01 03:19:33.184000'),
                o(unit='us', ch='2', len=9, first_until='2023-08-29 10:01:57.037120', len_until='2549-11-30 07:09:02.965824'),
            ),
            ('+SuZKz', 'KNuCZyz', '2gvgesKyz'),
        ),
        (
            b62,
            (
                o(unit= 's', ch='A', len=6, first_until='2028-07-15 10:30:34',        len_until='3799-06-08 04:23:06'),
                o(unit='ms', ch='b', len=7, first_until='2022-03-24 12:06:23.338000', len_until='2083-06-04 10:46:33.194000'),
                o(unit='us', ch='G', len=9, first_until='2025-06-18 22:29:50.672362', len_until='2406-01-02 13:06:37.841642'),
            ),
            ('At4G0V', 'bTwXvhz', 'GWAZusO3r',),
        ),
        (
            b90,
            (
                o(unit= 's', ch='8', len=5, first_until='2021-12-31 16:46:30',        len_until='2159-03-22 11:46:30'),
                o(unit='ms', ch='#', len=7, first_until='2037-07-20 16:40:47.190000', len_until='3502-09-11 06:10:47.190002'),
                o(unit='us', ch='A', len=8, first_until='2021-07-19 22:07:52.247190', len_until='2107-12-11 04:33:22.247190'),
            ),
            ('8Od[z', '#"R^v[z', 'AZK=Tv[z'),
        ),
    ),
)
def test_encodings(debug, codec, cases, t2021):
    # For each unit (s,ms,us), serialize the current epoch time using `b64`, and verify a few properties:
    # - `ch`: first char of serialized string (which changes least frequently)
    # - `len`: serialized string length
    # - `first_until`: time when the first char will change
    # - `len_until`: time when the length will change
    last = codec.I2S[-1]
    for case in cases:
        unit = case.unit
        t = now()
        n = getattr(t, unit)
        s = codec(n)
        N = len(s)
        s2dt = getattr(now, f'from_{unit}')
        first_until = s2dt(codec(s[0] + last*(N-1)))
        len_until = s2dt(codec(last*N))

        if debug:
            print(f"o(unit='{unit}', ch='{s[0]}', len={N}, first_until='{first_until}', len_until='{len_until}'),")
        else:
            assert s[0] == case.ch
            assert N == case.len
            assert first_until == to_dt(case.first_until)
            assert len_until == to_dt(case.len_until)

    instant = to_dt('20210101')
    assert (
        codec(now(d=instant). s),
        codec(now(d=instant).ms),
        codec(now(d=instant).us),
    ) == t2021
