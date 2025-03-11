from unittest.mock import patch

from datetime import datetime
import pytest
from pytest import approx
from pytz import UTC

from utz import b62, b64, b90, now, o, today, Time

to_dt = now.to_dt


def test_now():
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
    assert 0 <= Δ1 < .1, Δ1
    assert 0 <= Δ2 < .1, Δ2

    Δ1 = int(n2) - int(n1)
    Δ2 = int(n3) - int(n2)
    assert 0 <= Δ1 <= 1, Δ1
    assert 0 <= Δ2 <= 1, Δ2
    assert Δ1 == 0 or Δ2 == 0


@pytest.mark.parametrize("debug", [False])  # set to true to print the expected values for new test cases
@pytest.mark.parametrize(
    "codec,cases,t2021",
    (
        (
            b64,
            (
                    o(unit= 's', ch='+', len=6, first_until='2038-08-04T09:32:48Z', len_until='4182-03-14T03:28:00Z'),
                    o(unit='ms', ch='M', len=7, first_until='2026-08-27T02:19:40.480000Z', len_until='2111-08-01T07:19:33.184000Z'),
                    o(unit='us', ch='3', len=9, first_until='2032-07-30T09:31:33.747776Z', len_until='2549-11-30T12:09:02.965824Z'),
            ),
            ('+SuZKz', 'KNuCZyz', '2gvgesKyz'),
        ),
        (
            b62,
            (
                    o(unit= 's', ch='A', len=6, first_until='2028-07-15T14:30:34Z', len_until='3799-06-08T08:23:06Z'),
                    o(unit='ms', ch='d', len=7, first_until='2025-10-29T11:47:34.506000Z', len_until='2083-06-04T14:46:33.194000Z'),
                    o(unit='us', ch='G', len=9, first_until='2025-06-19T02:29:50.672362Z', len_until='2406-01-02T18:06:37.841642Z'),
            ),
            ('At4G0V', 'bTwXvhz', 'GWAZusO3r'),
        ),
        (
            b90,
            (
                    o(unit= 's', ch=':', len=5, first_until='2026-02-27T15:46:30Z', len_until='2159-03-22T15:46:30Z'),
                    o(unit='ms', ch='#', len=7, first_until='2037-07-20T20:40:47.190000Z', len_until='3502-09-11T10:10:47.190002Z'),
                    o(unit='us', ch='D', len=8, first_until='2026-02-04T20:12:22.247190Z', len_until='2107-12-11T09:33:22.247190Z'),
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
    last = codec.i2s[-1]
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
            unit_str = '% 4s' % f"'{unit}'"

            def fmt(d):
                if unit == 's':
                    return str(now(d=d))
                else:
                    return str(now(fmt='micro', d=d))

            print(f"o(unit={unit_str}, ch='{s[0]}', len={N}, first_until='{fmt(first_until)}', len_until='{fmt(len_until)}'),")
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


class FakeTimer:
    def __init__(self, start=0.0, increment=0.1):
        self.value = start
        self.increment = increment
        # self.orig_increment = increment

    def __call__(self):
        result = self.value
        self.value += self.increment
        # self.increment += self.orig_increment

        return result


def test_timer():
    with patch('utz.time.perf_counter', FakeTimer()):
        time = Time()
        time("a")
        time("b")
        time("c")
        time()

    assert time.times == approx({
        'a': 0.1,
        'b': 0.1,
        'c': 0.1,
    })


def test_timer_ctx():
    with patch('utz.time.perf_counter', FakeTimer()):
        time = Time()
        with time("a"):
            time("b")
            time("c")

        with time("d"):
            pass

        with time("e"), time("f"):
            with time("g"):
                time("h")
                time()

    assert time.times == approx({
        'a': 0.4,
        'b': 0.1,
        'c': 0.1,
        'd': 0.1,
        'e': 0.9,
        'f': 0.6,
        'g': 0.3,
        'h': 0.1,
    })
