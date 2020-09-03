#!/usr/bin/env python

import click
from click import command as cmd, option as opt


def paths(*args, sep=',', **kwargs):
    return opt(
        *args,
        callback=lambda ctx, param, value: [
            s
            for v in value
            for s in v.split(sep)
        ],
        multiple=True,
        **kwargs,
    )


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
        defaults = set([ opt['default'] for opt in opts ])
        if len(defaults) > 1: raise ValueError(f'Conflicting defaults: {opts}')
        [default] = defaults

    return opt(
        *[ opt['arg'] for opt in opts ],
        default=default,
        **kwargs
    )
