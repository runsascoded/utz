#!/usr/bin/env python
# coding: utf-8

# In[2]:


import shlex
from subprocess import check_call, check_output, CalledProcessError, DEVNULL
from collections.abc import Iterable


def parse_cmd(cmd):
    '''Stringify and potentially unwrap a command'''
    if len(cmd) == 1         and isinstance(cmd[0], Iterable)         and not isinstance(cmd[0], str):
        cmd = cmd[0]
    return [
        str(arg)
        for arg in cmd
        if arg is not None
    ]


def lines(*cmd, keep_trailing_newline=False, dry_run=False, **kwargs):
    '''Return the lines written to stdout by a command'''
    lines = [
        line.strip()
        for line in
        output(*cmd, dry_run=dry_run, **kwargs).decode().split('\n')
    ]

    if not keep_trailing_newline and lines and not lines[-1]:
        lines = lines[:-1]

    return lines


def line(*cmd, **kwargs):
    '''Run a command, verify that it returns a single line of output, and return that line'''
    _lines = lines(*cmd, **kwargs)
    if len(_lines) == 1:
        return _lines[0]
    else:
        raise ValueError(f'Expected 1 line, found {len(_lines)}:\n\t%s' % '\n\t'.join(_lines))

def run(*cmd, dry_run=False, **kwargs):
    '''Convenience wrapper for check_call'''
    cmd = parse_cmd(cmd)
    shlex_join = getattr(shlex, 'join', ' '.join)  # shlex.join only exists in Python ≥3.8
    if dry_run:
        print(f'Would run: {shlex_join(cmd)}')
    else:
        print(f'Running: {shlex_join(cmd)}')
        check_call(cmd, **kwargs)


def output(*cmd, dry_run=False, **kwargs):
    '''Convenience wrapper for check_output'''
    cmd = parse_cmd(cmd)
    shlex_join = getattr(shlex, 'join', ' '.join)  # shlex.join only exists in Python ≥3.8
    if dry_run:
        print(f'Would run: {shlex_join(cmd)}')
        return b''
    else:
        print(f'Running: {shlex_join(cmd)}')
        return check_output(cmd, **kwargs)


from json import loads
def json(*cmd, **kwargs):
    '''Run a command, parse the output as JSON, and return the parsed object'''
    return loads(output(*cmd, **kwargs).decode())


def check(*cmd):
    '''Return True iff a command run successfully (i.e. exits with code 0)'''
    try:
        run(*cmd, stderr=DEVNULL)
        return True
    except CalledProcessError:
        return False

