import re
from dataclasses import dataclass
from datetime import datetime as dt, date, timedelta
from functools import wraps
from typing import Union

from utz import Yield


# Types that can be passed to the Month constructor
Monthy = Union['YMD', str, int, None]


@dataclass(init=False, order=True, eq=True, unsafe_hash=True)
class YMD:
    y: int
    m: int
    d: int

    RGX = re.compile(r'(?P<year>\d{4})(?:-?(?P<month>\d\d)(?:-?(?P<day>\d\d))?)?')

    def _init_from_str(self, arg):
        m = self.RGX.fullmatch(arg)
        if not m:
            raise ValueError('Invalid month string: %s' % arg)
        year = int(m['year'])
        month = int(m['month']) if m['month'] else 1
        day = int(m['day']) if m['day'] else 1
        if month > 12:
            raise ValueError(f"Invalid month {month} ({arg})")
        self.__init__(year, month, day)

    def _verify(self):
        if not isinstance(self.y, int):
            raise ValueError('Year %s must be int, not %s' % (str(self.y), type(self.y)))
        if not isinstance(self.m, int):
            raise ValueError('Month %s must be int, not %s' % (str(self.m), type(self.m)))
        if not isinstance(self.d, int):
            raise ValueError('Day %s must be int, not %s' % (str(self.d), type(self.d)))

    def _init_now(self):
        now = dt.now()
        self.y = now.year
        self.m = now.month
        self.d = now.day

    def __init__(self, *args, **kwargs):
        if kwargs:
            if args:
                raise ValueError(f'Pass args xor kwargs: {args}, {kwargs}')
            keys = list(kwargs.keys())
            if keys == ['y', 'm', 'd']:
                self.y = kwargs['y']
                self.m = kwargs['m']
                self.d = kwargs['d']
            else:
                raise ValueError(f"Unrecognized kwargs: {kwargs}")
        elif len(args) == 3:
            self.y, self.m, self.d = int(args[0]), int(args[1]), int(args[2])
            self._verify()
        elif len(args) == 1:
            arg = args[0]
            if isinstance(arg, str):
                self._init_from_str(arg)
            elif isinstance(arg, int):
                self._init_from_str(str(arg))
            elif hasattr(arg, 'year') and hasattr(arg, 'month') and hasattr(arg, 'day'):
                self.y = arg.year
                self.m = arg.month
                self.d = arg.day
                self._verify()
            elif arg is None:
                self._init_now()
            elif 'year' in arg and 'month' in arg and 'day' in arg:
                self.y = int(arg['year'])
                self.m = int(arg['month'])
                self.d = int(arg['day'])
                self._verify()
            else:
                raise ValueError('Unrecognized argument: %s' % str(arg))
        elif not args:
            self._init_now()
        else:
            raise ValueError('Unrecognized arguments: %s' % str(args))

    @property
    def year(self):
        return self.y

    @property
    def month(self):
        return self.m

    @property
    def day(self):
        return self.d

    def str(self, sep=''):
        return '%d%s%02d%s%02d' % (self.y, sep, self.m, sep, self.d)

    def __str__(self):
        return self.str()

    def __int__(self):
        return int(str(self))

    def format(self, url, **kwargs):
        return url.format(ymd=str(self), y=str(self.y), m=str(self.m), d=str(self.d), **kwargs)

    @property
    def dt(self):
        import pandas as pd
        return pd.to_datetime('%d-%02d-%02d' % (self.y, self.m, self.d))

    @property
    def date(self) -> date:
        return self.dt.date()

    def __add__(self, n: int) -> 'YMD':
        if not isinstance(n, int):
            raise ValueError('%s: can only add an integer to a Month, not %s: %s' % (str(self), str(type(n)), str(n)))
        return YMD(self.date + timedelta(days=n))

    def __sub__(self, n: int) -> 'YMD':
        if not isinstance(n, int):
            raise ValueError('%s: can only add an integer to a Month, not %s: %s' % (str(self), str(type(n)), str(n)))
        return YMD(self.date - timedelta(days=n))

    def until(self, end: 'YMD' = None, step: int = 1) -> Yield['YMD']:
        cur: YMD = YMD(self)
        while end is None \
                or (step > 0 and cur < end) \
                or (step < 0 and cur > end):
            yield cur
            cur = cur + step


def dates(*flags, default_start=None, default_end=None, help=None):
    if not flags:
        flags = ('-d', '--dates')

    from click import option

    def _dates(fn):
        @option(*flags, help=help)
        @wraps(fn)
        def _fn(*args, dates=None, **kwargs):
            if dates:
                pcs = dates.split('-')
                if len(pcs) == 2:
                    [ start, end ] = pcs
                    start = YMD(start) if start else default_start
                    end = YMD(end) if end else default_end
                elif len(pcs) == 1:
                    [ym] = pcs
                    ym = YMD(ym)
                    start = ym
                    end = ym + 1
                else:
                    raise ValueError(f"Unrecognized {'/'.join(flags)}: {dates}")
            else:
                start, end = default_start, default_end
            fn(*args, start=start, end=end, **kwargs)

        return _fn

    return _dates
