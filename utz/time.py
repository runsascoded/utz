
from datetime import datetime as dt
from sys import stderr

from .o import o

class now:
    try:
        from pytz import UTC
        pytz = True
        def tz(d): return d.astimezone(now.UTC)
    except ImportError:
        pytz = False
        UTC = None
        def tz(d): return d

    EPOCH = dt(1970,1,1).replace(tzinfo=UTC)

    FMTS = o(
        iso='%Y-%m-%dT%H:%M:%SZ',
        short='%Y%m%dT%H%M%SZ',
        micro='%Y-%m-%dT%H:%M:%S.%fZ',
    )
    @property
    def fmts(self): return self.FMTS
    def __init__(self, fmt=None, d=None):
        FMTS = self.FMTS
        if fmt is None: fmt = FMTS.iso
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

