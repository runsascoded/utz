#!/usr/bin/env python
import shlex
from functools import partial
from json import loads
from subprocess import check_call, check_output, CalledProcessError, DEVNULL, Popen, PIPE, STDOUT
from sys import stderr
from typing import Optional, List, Tuple, Callable, Union, Dict

err = partial(print, file=stderr)
Log = Optional[Callable[..., None]]
Arg = Union[None, str, int, List['Arg'], Tuple['Arg']]


def silent(*args) -> None:
    pass


def flatten(args: Union[List[Arg], Tuple[Arg, ...]]) -> Tuple:
    """Recursively flatten a nested list of arguments."""
    if isinstance(args, list) or isinstance(args, tuple):
        return tuple(
            a
            for arg in args
            for a in flatten(arg)
        )
    else:
        return (args,)


def parse_cmd(cmd: Tuple[Arg, ...]) -> List[str]:
    """Flatten and stringify a command."""
    return [
        str(arg)
        for arg in flatten(cmd)
        if arg is not None
    ]


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


ELIDED = '****'
Elides = Union[None, str, List[str]]


def mk_cmd_str(cmd: List[str], elide: Elides = None) -> str:
    """Convert a command to a string, optionally eliding known sensitive values."""
    cmd_str = shlex.join(cmd)
    if elide:
        if isinstance(elide, str):
            elide = [elide]
        for s in elide:
            cmd_str = cmd_str.replace(s, ELIDED)
    return cmd_str


def run(
    *cmd: Arg,
    dry_run: bool = False,
    elide: Elides = None,
    log: Log = err,
    **kwargs,
) -> None:
    """Convenience wrapper for ``subprocess.check_call``."""
    cmd = parse_cmd(cmd)
    cmd_str = mk_cmd_str(cmd, elide)
    if dry_run:
        if log:
            log(f'Would run: {cmd_str}')
    else:
        if log:
            log(f'Running: {cmd_str}')
        check_call(cmd, **kwargs)


sh = run


def interleaved_output(cmd: List[str], err_ok: bool = False) -> bytes:
    try:
        proc = Popen(cmd, stdout=PIPE, stderr=STDOUT)

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
            err(e.output.decode())
            raise e


def output(
    *cmd: Arg,
    dry_run: bool = False,
    both: bool = False,
    err_ok: bool = False,
    elide: Elides = None,
    log: Log = err,
    **kwargs,
) -> Optional[bytes]:
    """Convenience wrapper for ``subprocess.check_output``.

    By default, logs commands to `err` (stderr) before running (pass `log=None` to disable).

    If `err_ok=True`, exceptions will be caught, and `None` returned.

    If `both=True`, stdout and stderr will both be captured (interleaved), and returned.
    """

    cmd = parse_cmd(cmd)
    cmd_str = mk_cmd_str(cmd, elide)
    if dry_run:
        if log:
            log(f'Would run: {cmd_str}')
        return None
    else:
        if log:
            log(f'Running: {cmd_str}')
        if both:
            return interleaved_output(cmd, err_ok=err_ok)
        else:
            try:
                return check_output(cmd, **kwargs)
            except CalledProcessError as e:
                if err_ok:
                    return None
                else:
                    raise e


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


# Omit "json", to avoid colliding with stdlib
__all__ = [ 'check', 'err', 'flatten', 'interleaved_output', 'line', 'lines', 'output', 'run', 'sh', 'silent', ]
