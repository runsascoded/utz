from __future__ import annotations

from functools import partial

from typing import Sequence, Any, Callable

import re
from re import fullmatch, IGNORECASE

from click import command as cmd, Context, option, option as opt, Parameter, BadParameter

INT_RGX = re.compile(r'(?P<base>[\d.]+)(?P<suffix>[kmbg]i?)', flags=IGNORECASE)
ORDERS_SI  = { 'k': 2**10, 'm': 2**20, 'g': 2**30 }
ORDERS_IEC = { 'k': 1e3  , 'm': 1e6  , 'g': 1e9  , 'b': 1e9 }


def parse_int(value: str | int | None) -> int:
    if isinstance(value, int):
        return value
    m = fullmatch(INT_RGX, value.lower())
    if m:
        n = float(m['base'])
        suffix = m['suffix']
        if suffix.endswith('i'):
            suffix = suffix[:-1]
            orders = ORDERS_SI
        else:
            orders = ORDERS_IEC
        if suffix not in orders:
            raise ValueError(f'Failed to parse "{value}"')
        order = orders[suffix]
        return int(n * order)
    else:
        try:
            return int(float(value))
        except Exception:
            raise ValueError(f'Failed to parse "{value}"')


def int_cb(ctx: Context, param: Parameter, value: str | int | None) -> int:
    if value is None:
        raise BadParameter(f"expected value, received None", ctx=ctx, param=param)
    try:
        return parse_int(value)
    except Exception:
        raise BadParameter(f'failed to parse "{value}"', ctx=ctx, param=param)


def parse_int_opt(ctx: Context, param: Parameter, value: str) -> int | None:
    if value is None:
        return None
    else:
        return int_cb(ctx, param, value)


def num(
    *args,
    required: bool = False,
    default: int | str | None = None,
    **kwargs,
):
    return option(
        *args,
        required=required,
        default=str(default) if isinstance(default, int) else default,
        callback=int_cb if required or default else parse_int_opt,
        **kwargs,
    )


number = num


def count(
    *args,
    values: Sequence[Any] | None = None,
    **kwargs,
):
    def count_enum_cb(ctx: Context, param: Parameter, value: int):
        if values is not None:
            if value >= len(values):
                raise BadParameter(f"expected [0,{len(values)}), found {value}", ctx=ctx, param=param)
            value = values[value]
        if 'callback' in kwargs:
            return kwargs['callback'](value)
        else:
            return value

    return option(
        *args,
        count=True,
        callback=count_enum_cb,
        **kwargs,
    )


Parse = Callable[[str], Any]


def dict_cb(
    ctx: Context,
    param: Parameter,
    value: tuple[str, ...],
    parse: Parse | None = None,
) -> dict[str, str]:
    """``click.option`` ``callback`` that loads multiple "k=v"-style values into a ``dict``."""
    rv = {}
    for kv in value:
        pcs = kv.split('=', 1)
        if len(pcs) != 2:
            raise BadParameter(f"bad value: {kv}")
        k, v = pcs
        if parse:
            v = parse(v)
        rv[k] = v
    return rv


def obj(
    *args: str,
    parse: Parse | None = None,
    **kwargs,
):
    """``click.option`` wrapper that loads multiple "k=v"-style values into a ``dict``."""
    return option(
        *args,
        multiple=True,
        callback=partial(dict_cb, parse=parse),
        **kwargs,
    )


def multi_cb(
    ctx: Context,
    param: Parameter,
    value: tuple[str, ...],
    sep: str = ',',
    parse: Parse | None = None,
) -> tuple[str, ...]:
    """``click.option`` ``callback`` that combines multiple ``sep``-delimited strings into a ``tuple``."""
    rv = []
    for v in value:
        for s in v.split(sep):
            if parse:
                try:
                    s = parse(s)
                except Exception:
                    raise BadParameter(f'failed to parse "{s}"', ctx=ctx, param=param)
            rv.append(s)
    return tuple(rv)


def multi(
    *args: str,
    sep: str = ',',
    parse: Parse | None = None,
    multiple: bool = True,
    **kwargs,
):
    """``click.option`` wrapper that combines multiple ``sep``-delimited strings into a ``tuple``."""
    return opt(
        *args,
        callback=partial(multi_cb, sep=sep, parse=parse),
        multiple=multiple,
        **kwargs,
    )


paths = partial(multi, sep=':')


def flag(*names, default=None, **kwargs):
    def long_opt(name):
        _default = False
        if name.startswith('no-'):
            name = name[3:]
            _default = True

        arg = f'--{name}/--no-{name}'
        return dict(
            name=name,
            default=_default,
            arg=arg,
        )

    def short_opt(name):
        if len(name) != 1:
            raise ValueError(f'Unrecognized short option name: -{name}')
        _default = name.isupper()
        name = name.lower()
        arg = f'-{name}/-{name.upper()}'
        return dict(
            name=name,
            default=_default,
            arg=arg,
        )

    def make_opt(name):
        if name.startswith('--'):
            return long_opt(name[2:])
        elif name.startswith('-'):
            return short_opt(name[1:])
        elif len(name) > 1:
            return long_opt(name)
        elif len(name) == 1:
            return short_opt(name)
        else:
            raise ValueError('Empty flag')

    opts = [ make_opt(name) for name in names ]
    if default is None:
        defaults = set([ o['default'] for o in opts ])
        if len(defaults) > 1: raise ValueError(f'Conflicting defaults: {opts}')
        [default] = defaults

    return opt(
        *[ o['arg'] for o in opts ],
        default=default,
        **kwargs
    )
