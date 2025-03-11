from __future__ import annotations

from contextlib import contextmanager

from typing import KeysView, ItemsView, ValuesView, Callable

from datetime import datetime as dt, timezone
from sys import stderr
from time import perf_counter
from types import TracebackType

from utz.proc import err
from utz.o import o


utc = timezone.utc


class Time:
    """Simple "timer" class.

    >>> from time import sleep
    >>> time = Time()
    >>> time("step 1")
    >>> sleep(1)
    >>> time("step 2")
    >>> sleep(1)
    >>> time()  # "close" "step 2"
    >>> print(f'Step 1 took {time["step 1"]:.1f}s, step 2 took {time["step 2"]:.1f}s.'

    Can also be used as a contextmanager:

    >>> time = Time()
    >>> with time("run"):
    >>>     sleep(1)
    >>> print(f'Run took {time["run"]:.1f}s')
    """
    def __init__(self, log: str | True | Callable[[str, float], str] | None = None):
        self.times = {}
        self._cur_timer = None
        self._cur_start = 0
        # `__{enter,exit}__`s push and pop timer names to and from this stack
        self._ctx_stack = []

        if log is True:
            log = "{k} took {v:.3g}s"
        if isinstance(log, str):
            def fmt_fn(k, v):
                return log.format(k=k, v=v)
            self._log = fmt_fn
        elif log is None:
            self._log = None
        else:
            self._log = log

    def save(self, name: str, duration: float):
        """Record a duration associated with a timer name, and optionally log a message about it."""
        self.times[name] = duration
        if self._log:
            err(self._log(name, duration))

    def end(self, ts: float | None = None):
        """End and save any active timer."""
        if self._cur_timer:
            prev_end = ts or perf_counter()
            duration = prev_end - self._cur_start
            self.save(self._cur_timer, duration)
            self._cur_timer = None
            self._cur_start = 0

    def __call__(self, name: str | None = None) -> "Time":
        """Primary method for recording a named timer."""
        self.end()  # End any active timer
        if name:
            # Start a new timer
            self._cur_timer = name
            self._cur_start = perf_counter()
        return self

    @contextmanager
    def ctx(self, name: str):
        with self(name):
            yield

    def __enter__(self):
        """Push the current timer onto the "context stack"."""
        if self._cur_timer is not None:
            self._ctx_stack.append((self._cur_timer, perf_counter()))
            self._cur_timer = None
            self._cur_start = 0
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        """End the most-recently `__enter__`d timer."""
        end = perf_counter()
        self.end(end)
        if self._ctx_stack:
            name, start = self._ctx_stack.pop()
            duration = end - start
            self.save(name, duration)

        if exc_value:
            raise exc_value

    def fmt(self, fmt_spec: str = ".3g") -> dict[str, float]:
        """Format the accumulated timings."""
        fmt_str = "{:%s}" % fmt_spec
        return {
            k: float(fmt_str.format(v))
            for k, v in self.times.items()
        }

    def __getitem__(self, name: str) -> float:
        return self.times[name]

    def keys(self) -> KeysView[str]:
        return self.times.keys()

    def values(self) -> ValuesView[float]:
        return self.times.values()

    def items(self) -> ItemsView[str, float]:
        return self.times.items()


class now:
    try:
        from pytz import UTC
        pytz = True
        def tz(d): return d.astimezone(now.UTC)
    except ImportError:
        pytz = False
        UTC = None
        def tz(d): return d

    EPOCH = dt(1970, 1, 1).replace(tzinfo=UTC)
    FMTS = o(
        iso='%Y-%m-%dT%H:%M:%SZ',
        short='%Y%m%dT%H%M%SZ',
        micro='%Y-%m-%dT%H:%M:%S.%fZ',
    )

    @property
    def fmts(self):
        return self.FMTS

    def __init__(self, fmt=None, d=None):
        FMTS = self.FMTS
        if fmt is None:
            fmt = FMTS.iso
        elif isinstance(fmt, str):
            if hasattr(FMTS, fmt):
                fmt = getattr(FMTS, fmt)
        if d is None:
            self.time = dt.now()
        elif isinstance(d, str):
            from dateutil.parser import parse
            self.time = parse(d)
        elif isinstance(d, dt):
            self.time = d
        if now.pytz:
            self.time = self.time.astimezone(now.UTC)
        else:
            # timezone will be local, not UTC; don't imply UTC in format
            stderr.write('pytz not installed; now()/today() will be based on OS TZ, which may not be UTC\n')
            assert fmt[-1] == 'Z'
            fmt = fmt[:-1]

        self.fmt = fmt

    def __call__(self, fmt): return self.time.strftime(fmt)
    def __getattr__(self, k): return getattr(self.time, k)
    def __str__(self): return self.time.strftime(self.fmt)
    def __repr__(self): return str(self)
    def __int__(self): return int((self.time - now.tz(now.EPOCH)).total_seconds())
    def __float__(self): return (self.time - now.tz(now.EPOCH)).total_seconds()

    @property
    def s(self): return int(self)

    @property
    def ds(self): return self.ms // 100

    @property
    def cs(self): return self.ms // 10

    @property
    def ms(self): return int(float(self) * 1e3)

    @property
    def μs(self): return int(float(self) * 1e6)

    @property
    def us(self): return int(float(self) * 1e6)

    @staticmethod
    def to_dt(s):
        from dateutil.parser import parse
        parsed = parse(s)
        if not parsed.tzinfo:
            parsed = parsed.replace(tzinfo=now.UTC)
        return parsed

    @staticmethod
    def fromtimestamp(s, tz=UTC): return dt.fromtimestamp(s, tz=tz)

    @staticmethod
    def from_s(s): return now.fromtimestamp(s)

    @staticmethod
    def from_ms(ms): return now.fromtimestamp(ms / 1e3)

    @staticmethod
    def from_μs(us): return now.fromtimestamp(us / 1e6)

    @staticmethod
    def from_us(us): return dt.fromtimestamp(us / 1e6, tz=now.UTC)


class today(now):
    FMTS = o(
        iso='%Y-%m-%d',
        short='%Y%m%d',
    )
