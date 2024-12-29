#!/usr/bin/env python
from __future__ import annotations

from json import loads
from sys import stderr

import subprocess
from functools import partial
from subprocess import check_call, check_output, CalledProcessError, CompletedProcess, DEVNULL, Popen, PIPE, STDOUT
from typing import Callable, Dict, List, Optional, Union

from .cmd import Cmd
from .util import Arg, Elides, parse_cmd

err = partial(print, file=stderr)
Log = Optional[Callable[..., None]]


def silent(*args) -> None:
    pass


def lines(
    *cmd: Arg,
    keep_trailing_newline: bool = False,
    dry_run: bool = False,
    err_ok: bool = False,
    **kwargs,
) -> Optional[List[str]]:
    """Return the lines written to stdout by a command."""
    out = output(*cmd, dry_run=dry_run, err_ok=err_ok, **kwargs)
    if err_ok and out is None:
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
) -> Optional[str]:
    """Run a command, verify that it returns a single line of output, and return that line."""
    _lines = lines(*cmd, err_ok=err_ok, **kwargs)
    if (empty_ok or err_ok) and not _lines:
        return None
    elif len(_lines) == 1:
        return _lines[0]
    else:
        raise ValueError(f'Expected 1 line, found {len(_lines)}:\n\t%s' % '\n\t'.join(_lines))


def run(
    *args: Arg,
    dry_run: bool = False,
    elide: Elides = None,
    log: Log = err,
    check: bool = True,
    shell: bool | None = None,
    expanduser: bool | None = None,
    expandvars: bool | None = None,
    **kwargs,
) -> CompletedProcess | None:
    """Convenience wrapper for ``subprocess.check_call``."""
    cmd = Cmd.mk(
        *args,
        shell=shell,
        expanduser=expanduser,
        expandvars=expandvars,
        elide=elide,
        **kwargs,
    )
    if dry_run:
        if log:
            log(f'Would run: {cmd}')
    else:
        if log:
            log(f'Running: {cmd}')
        args, kwargs = cmd.compile()
        if check:
            check_call(args, **kwargs)
            return None
        else:
            return subprocess.run(args, **kwargs)


sh = run


def interleaved_output(
    cmd: List[str] | str,
    err_ok: bool = False,
    **kwargs,
) -> bytes:
    try:
        proc = Popen(cmd, stdout=PIPE, stderr=STDOUT, **kwargs)

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
        if err_ok:
            return e.output
        else:
            raise e


def output(
    *args: Arg,
    dry_run: bool = False,
    both: bool = False,
    err_ok: bool = False,
    elide: Elides = None,
    log: Log = err,
    shell: bool | None = None,
    expanduser: bool | None = None,
    expandvars: bool | None = None,
    **kwargs,
) -> Optional[bytes]:
    """Convenience wrapper for ``subprocess.check_output``.

    By default, logs commands to `err` (stderr) before running (pass `log=None` to disable).

    If `err_ok=True`, exceptions will be caught, and `None` returned.

    If `both=True`, stdout and stderr will both be captured (interleaved), and returned.
    """
    cmd = Cmd.mk(
        *args,
        shell=shell,
        expanduser=expanduser,
        expandvars=expandvars,
        elide=elide,
        **kwargs,
    )
    if dry_run:
        if log:
            log(f'Would run: {cmd}')
        return None
    else:
        if log:
            log(f'Running: {cmd}')
        if both:
            args, kwargs = cmd.compile()
            return interleaved_output(args, err_ok=err_ok, **kwargs)
        else:
            try:
                args, kwargs = cmd.compile()
                return check_output(args, **kwargs)
            except CalledProcessError as e:
                if err_ok:
                    return None
                else:
                    raise e


def text(*args, **kwargs):
    return output(*args, **kwargs).decode()


def json(
    *cmd: Arg,
    dry_run: bool = False,
    **kwargs,
) -> Union[None, List, Dict, str, int, float, bool]:
    """Run a command, parse the output as JSON, and return the parsed object."""
    out = output(*cmd, dry_run=dry_run, **kwargs)
    if out is None:
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


from .pipeline import pipeline
from .named_pipes import named_pipes


# Omit "json", to avoid colliding with stdlib
__all__ = [
    'check',
    'err',
    'interleaved_output',
    'line',
    'lines',
    'named_pipes',
    'output',
    'pipeline',
    'run',
    'sh',
    'silent',
    'text',
]
