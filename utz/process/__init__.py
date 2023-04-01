#!/usr/bin/env python

from json import loads
import shlex
from subprocess import check_call, check_output, CalledProcessError, DEVNULL
from sys import stderr


def err(msg):
    stderr.write(msg)
    stderr.write('\n')


def parse_cmd(cmd):
    """Stringify and potentially unwrap a command"""

    def flatten(args):
        if isinstance(args, list) or isinstance(args, tuple):
            return tuple(
                a
                for arg in args
                for a in flatten(arg)
            )
        else:
            return (args,)

    return [
        str(arg)
        for arg in flatten(cmd)
        if arg is not None
    ]


def lines(*cmd, keep_trailing_newline=False, dry_run=False, err_ok=False, **kwargs):
    """Return the lines written to stdout by a command"""
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


def line(*cmd, empty_ok=False, err_ok=False, **kwargs):
    """Run a command, verify that it returns a single line of output, and return that line"""
    _lines = lines(*cmd, err_ok=err_ok, **kwargs)
    if (empty_ok or err_ok) and not _lines:
        return None
    elif len(_lines) == 1:
        return _lines[0]
    else:
        raise ValueError(f'Expected 1 line, found {len(_lines)}:\n\t%s' % '\n\t'.join(_lines))


ELIDED = '****'


def mk_cmd_str(cmd, elide=None):
    shlex_join = getattr(shlex, 'join', ' '.join)  # shlex.join only exists in Python ≥3.8
    cmd_str = shlex_join(cmd)
    if elide:
        if isinstance(elide, str): elide = [elide]
        for s in elide:
            cmd_str = cmd_str.replace(s, ELIDED)
    return cmd_str


def run(*cmd, dry_run=False, elide=None, log=err, **kwargs):
    """Convenience wrapper for check_call"""
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


def output(*cmd, dry_run=False, err_ok=False, elide=None, log=err, **kwargs):
    """Convenience wrapper for check_output"""
    cmd = parse_cmd(cmd)
    cmd_str = mk_cmd_str(cmd, elide)
    if dry_run:
        if log:
            log(f'Would run: {cmd_str}')
        return None
    else:
        if log:
            log(f'Running: {cmd_str}')
        try:
            return check_output(cmd, **kwargs)
        except CalledProcessError as e:
            if err_ok:
                return None
            else:
                raise e


def json(*cmd, dry_run=False, **kwargs):
    """Run a command, parse the output as JSON, and return the parsed object"""
    out = output(*cmd, dry_run=dry_run, **kwargs)
    if out is None:
        return None
    return loads(out.decode())


def check(*cmd, stdout=DEVNULL, stderr=DEVNULL, **kwargs):
    """Return True iff a command run successfully (i.e. exits with code 0)"""
    try:
        run(*cmd, stdout=stdout, stderr=stderr, **kwargs)
        return True
    except CalledProcessError:
        return False


__all__ = ['check', 'err', 'line', 'lines', 'output', 'run', 'sh', ]
