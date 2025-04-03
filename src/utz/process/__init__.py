#!/usr/bin/env python
from __future__ import annotations

from json import loads
from sys import stderr

import subprocess
from functools import partial
from subprocess import check_call, CalledProcessError, CompletedProcess, DEVNULL, Popen, PIPE
from typing import Union

from .cmd import Cmd
from .log import Log, silent
from .util import Arg, Elides, parse_cmd

err = partial(print, file=stderr)


Json = Union[None, list, dict, str, int, float, bool]


def run(
    *args: Arg,
    dry_run: bool = False,
    log: Log = err,
    check: bool = True,
    **kwargs,
) -> CompletedProcess | None:
    """Convenience wrapper for ``subprocess.check_call``."""
    cmd = Cmd.mk(*args, **kwargs)
    if dry_run:
        if log:
            log(f'Would run: {cmd}')
    else:
        args, kwargs = cmd.compile(log=log)
        if check:
            check_call(args, **kwargs)
            return None
        else:
            return subprocess.run(args, **kwargs)


sh = run


def output(
    *args: Arg,
    dry_run: bool = False,
    both: bool = False,
    err_ok: bool | None = False,
    log: Log = err,
    **kwargs,
) -> bytes | None:
    """Convenience wrapper for ``subprocess.check_output``.

    By default, logs commands to `err` (stderr) before running (pass `log=None` to disable).

    If ``err_ok=True``, exceptions will be caught and suppressed, and the stdout up to that point will be returned.
    If ``err_ok=None``, exceptions will be caught and suppressed, and ``None`` will be returned.

    ``both=True`` is an alias for ``stderr=STDOUT``.
    """
    cmd = Cmd.mk(*args, **kwargs)
    if dry_run:
        if log:
            log(f'Would run: {cmd}')
        return None
    else:
        args, kwargs = cmd.compile(log=log, both=both)
        try:
            proc = Popen(args, stdout=PIPE, **kwargs)

            # Stream and capture the output in real-time
            output = b''
            for line in proc.stdout:
                output += line

            proc.wait()
            if proc.returncode != 0:
                raise CalledProcessError(proc.returncode, cmd, output=output)
            else:
                return output
        except CalledProcessError as e:
            if err_ok is True:
                return e.output
            elif err_ok is None:
                return None
            else:
                raise e


def text(*args, **kwargs) -> str | None:
    return output(*args, **kwargs).decode()


def json(
    *cmd: Arg,
    dry_run: bool = False,
    err_ok: bool = False,
    **kwargs,
) -> Json:
    """Run a command, parse the output as JSON, and return the parsed object."""
    out = output(*cmd, dry_run=dry_run, err_ok=err_ok, **kwargs)
    if out is None or err_ok is True and not out:
        return None
    return loads(out.decode())


def check(
    *cmd: Arg,
    stdout=DEVNULL,
    stderr=DEVNULL,
    **kwargs,
):
    """Run a command, return True iff it runs successfully (i.e. exits with code 0)."""
    try:
        run(*cmd, stdout=stdout, stderr=stderr, **kwargs)
        return True
    except CalledProcessError:
        return False


def lines(
    *cmd: Arg,
    dry_run: bool = False,
    err_ok: bool = False,
    keep_trailing_newline: bool = False,
    **kwargs,
) -> list[str] | None:
    """Return the lines written to stdout by a command."""
    out = output(*cmd, dry_run=dry_run, err_ok=err_ok, **kwargs)
    if err_ok is None and out is None:
        return None

    lines = [
        line.rstrip('\n')
        for line in
        out.decode().split('\n')
    ]

    if not keep_trailing_newline and lines and not lines[-1]:
        lines = lines[:-1]

    return lines


def line(
    *cmd: Arg,
    empty_ok: bool = False,
    err_ok: bool = False,
    **kwargs,
) -> str | None:
    """Run a command, verify that it returns a single line of output, and return that line."""
    _lines = lines(*cmd, err_ok=err_ok, **kwargs)
    if (empty_ok or err_ok is not False) and not _lines:
        return None
    elif len(_lines) == 1:
        return _lines[0]
    else:
        raise ValueError(f'Expected 1 line, found {len(_lines)}:\n\t%s' % '\n\t'.join(_lines))


from . import aio
from .pipeline import pipeline
from .named_pipes import named_pipes


# Omit "json", to avoid colliding with stdlib
__all__ = [
    'check',
    'err',
    'line',
    'lines',
    'named_pipes',
    'output',
    'pipeline',
    'run',
    'sh',
    'silent',
    'text',
    'Arg',
    'Cmd',
    'Elides',
    'Log',
]
