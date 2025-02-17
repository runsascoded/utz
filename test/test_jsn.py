from utz import dataclass, Encoder, json, fromtimestamp
from utz.time import utc


def test_datetimes():
    epoch = fromtimestamp(0, tz=utc)
    assert json.dumps({ 'epoch': epoch}, cls=Encoder) == '{"epoch": "1970-01-01 00:00:00"}'
    assert json.dumps({ 'epoch': epoch}, cls=Encoder, indent=2) == '\n'.join([
        '{',
        '  "epoch": "1970-01-01 00:00:00"',
        '}',
    ])
    assert json.dumps({ 'epoch': epoch}, cls=Encoder("%Y-%m-%d")) == '{"epoch": "1970-01-01"}'
    assert json.dumps({ 'epoch': epoch}, cls=Encoder("%Y-%m-%d"), indent=2) == '\n'.join([
        '{',
        '  "epoch": "1970-01-01"',
        '}',
    ])


@dataclass
class A:
    n: int


@dataclass
class B:
    arr: list[A]


def test_dataclasses():
    assert json.dumps(A(111), cls=Encoder) == '{"n": 111}'
    b = B([A(111), A(222)])
    b_str = '{"arr": [{"n": 111}, {"n": 222}]}'
    assert json.dumps(b, cls=Encoder) == b_str
    assert json.dumps({ 'b': b }, cls=Encoder) == '{"b": %s}' % b_str
