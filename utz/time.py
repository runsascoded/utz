
from datetime import datetime as dt
from sys import stderr

from .o import o

class now:
    EPOCH = dt(1970,1,1)

    try:
        # import pytz
        from pytz import UTC
        pytz = True
        # UTC = pytz.UTC
        def tz(d): return d.astimezone(now.UTC)
    except ImportError:
        pytz = False
        UTC = None
        def tz(d): return d

    FMTS = o(
        iso='%Y-%m-%dT%H:%M:%SZ',
        short='%Y%m%dT%H%M%SZ',
    )
    @property
    def fmts(self): return self.FMTS
    def __init__(self, fmt=None):
        FMTS = self.FMTS
        if fmt is None: fmt = FMTS.iso
        elif isinstance(fmt, str):
            if hasattr(FMTS, fmt):
                fmt = getattr(FMTS, fmt)
        self.time = dt.now()
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


class today(now):
    FMTS = o(
        iso='%Y-%m-%d',
        short='%Y%m%d',
    )

