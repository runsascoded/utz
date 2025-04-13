from __future__ import annotations

from os import path

import shlex
from typing import Sequence, Union

Arg = Union[None, str, int, list['Arg'], tuple['Arg']]
ELIDED = '****'
Elides = Union[None, str, list[str]]


def flatten(args: Sequence[Arg]) -> tuple:
    """Recursively flatten a nested list of arguments."""
    if isinstance(args, list) or isinstance(args, tuple):
        return tuple(
            a
            for arg in args
            for a in flatten(arg)
        )
    else:
        return (args,)


def mk_cmd_str(cmd: Sequence[str] | str, elide: Elides = None) -> str:
    """Convert a command to a string, optionally eliding known sensitive values."""
    cmd_str = cmd if isinstance(cmd, str) else shlex.join(cmd)
    if elide:
        if isinstance(elide, str):
            elide = [elide]
        for s in elide:
            cmd_str = cmd_str.replace(s, ELIDED)
    return cmd_str


def parse_cmd(
    cmd: Sequence[Arg] | str,
    shell: bool | None = None,
    expanduser: bool | None = None,
    expandvars: bool | None = None,
    elide: Elides = None,
) -> tuple[list[str] | str, str]:
    """Flatten and stringify a command."""
    if shell:
        if not isinstance(cmd, str):
            raise ValueError("Expected string command in shell mode")
        if expanduser:
            cmd = path.expanduser(cmd)
        if expandvars:
            cmd = path.expandvars(cmd)
    else:
        cmd = [
            str(arg)
            for arg in flatten(cmd)
            if arg is not None
        ]
        if expanduser:
            cmd = [ path.expanduser(arg) for arg in cmd ]
        if expandvars:
            cmd = [ path.expandvars(arg) for arg in cmd ]

    cmd_str = mk_cmd_str(cmd, elide)
    return cmd, cmd_str
