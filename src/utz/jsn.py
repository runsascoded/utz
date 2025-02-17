from __future__ import annotations

from json import JSONEncoder

from dataclasses import is_dataclass, asdict
from datetime import datetime
from typing import Callable, Union

DEFAULT_FMT = "%Y-%m-%d %H:%M:%S"
DatetimeFmt = Union[str, Callable[[datetime], str]]


class Encoder(JSONEncoder, Callable[[...], JSONEncoder]):
    """``JSONEncoder`` that handles ``datatime``s and ``dataclass``es by default.

    Pass to ``json.dump`` or ``json.dumps`` like:

    >>> from utz import dataclass, Encoder, fromtimestamp, json  # Convenience imports from standard library
    >>> epoch = fromtimestamp(0)
    >>> json.dumps({ 'epoch': epoch }, cls=Encoder)
    '{"epoch": "1969-12-31 19:00:00"}'
    >>> json.dumps({ 'epoch': epoch }, cls=Encoder("%Y-%m-%d"), indent=2)
    '''{
      "epoch": "1969-12-31"
    }'''
    >>> @dataclass
    >>> class A:
    >>>     n: int
    >>>
    >>> json.dumps(A(111), cls=Encoder)
    '{"n": 111}'
    """
    def __init__(
        self,
        dt_fmt: DatetimeFmt | None = DEFAULT_FMT,
        dataclasses: bool = True,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.dt_fmt = dt_fmt
        self.dataclasses = dataclasses

    def default(self, o) -> "str":
        if self.dataclasses and is_dataclass(o):
            return asdict(o)
        elif isinstance(o, datetime):
            dt_fmt = self.dt_fmt or DEFAULT_FMT
            if callable(dt_fmt):
                return dt_fmt(o)
            elif isinstance(dt_fmt, str):
                return o.strftime(self.dt_fmt)
            else:
                raise ValueError(f"Unexpected {dt_fmt=}")
        else:
            return super().default(o)

    def __call__(self, *args, **kwargs) -> "Encoder":
        """Convenience wrapper, allowing an ``Encoder`` instance to be passed to e.g. ``json.dump(cls=...)``."""
        return Encoder(
            dt_fmt=self.dt_fmt,
            dataclasses=self.dataclasses,
            *args,
            **kwargs,
        )
