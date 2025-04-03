from __future__ import annotations

from os.path import expandvars, expanduser
from subprocess import STDOUT

import shlex
from abc import ABC
from dataclasses import dataclass
from typing import Any, Sequence, Union

from utz.process.log import Log
from utz.process.util import Arg, Elides, flatten, ELIDED

Args = Union[str, list[str]]
Kwargs = dict[str, Any]
Compiled = tuple[Args, Kwargs]


class Cmd(ABC):
    """Interface for shell (`str`) and non-shell (`list[str]`) commands."""

    def compile(
        self,
        log: Log = None,
        both: bool = False,
    ) -> Compiled:
        """Compile a ``Cmd`` into ``args`` and ``kwargs`` suitable for passing to ``subprocess`` functions."""
        if log:
            log(f'Running: {self}')
        args, kwargs = self._compile()
        if both:
            if 'stderr' in kwargs and kwargs['stderr'] is not STDOUT:
                raise ValueError(f"`both=True` conflicts with `stderr={kwargs['stderr']}`")
            kwargs['stderr'] = STDOUT
        return args, kwargs

    def _compile(self):
        raise NotImplementedError

    @staticmethod
    def elide_cmd(cmd: str, elide: Elides) -> str:
        if elide:
            if isinstance(elide, str):
                elide = [elide]
            for s in elide:
                cmd = cmd.replace(s, ELIDED)
        return cmd

    def mk(
        *args: tuple[Arg, ...],
        sh: bool | str | None = None,
        shell: bool | str | None = None,
        executable: str | None = None,
        expanduser: bool | None = None,
        expandvars: bool | None = None,
        elide: Elides = None,
        **kwargs,
    ):
        """Construct a ``Cmd`` instance.

        - Handles `shell` and non-`shell` modes (including `shell` executable strings, with `sh` as a convenience alias
          for `shell`)
        - Optional strings to elide (e.g. secrets); **this has not been security-reviewed, and you should audit the
          relevant code paths if relying on it**.
        """
        if sh is not None:
            if shell is not None and sh != shell:
                raise ValueError(f"{sh=} != {shell=}")
            shell = sh
        if isinstance(shell, str):
            if executable and executable != shell:
                raise ValueError(f"{shell=} != {executable=}")
            executable = shell
            shell = True

        if len(args) == 1 and isinstance(args[0], str):
            if shell is True or shell is None:
                if expanduser or expandvars:
                    raise ValueError("Can't `expand{user,vars}` in shell mode")
                return ShellCmd(
                    args[0],
                    executable=executable,
                    elide=elide,
                    kwargs=kwargs,
                )
            else:
                raise ValueError("Expected `list[str]` command in non-shell mode")
        else:
            if shell is False or shell is None:
                return ArrayCmd(
                    args,
                    expanduser=expanduser,
                    expandvars=expandvars,
                    elide=elide,
                    kwargs=kwargs,
                )
            else:
                raise ValueError("Expected `str` command in shell mode")


@dataclass
class ShellCmd(Cmd):
    cmd: str
    executable: str | None = None
    elide: Elides = None
    kwargs: dict[str, Any] = None

    def __str__(self) -> str:
        return self.elide_cmd(self.cmd, self.elide)

    def _compile(self) -> tuple[str, Kwargs]:
        cmd = self.cmd
        if self.elide:
            if isinstance(self.elide, str):
                self.elide = [self.elide]
            for s in self.elide:
                cmd = cmd.replace(s, '****')

        return cmd, { **(self.kwargs or {}), 'shell': True, 'executable': self.executable, }


@dataclass
class ArrayCmd(Cmd):
    args: Sequence[Arg]
    expanduser: bool = False
    expandvars: bool = False
    elide: Elides = None
    kwargs: dict[str, Any] = None

    @property
    def cmd(self) -> list[str]:
        return [
            str(arg)
            for arg in flatten(self.args)
            if arg is not None
        ]

    def __str__(self) -> str:
        return self.elide_cmd(shlex.join(self.cmd), self.elide)

    def _compile(self) -> tuple[list[str], Kwargs]:
        cmd = self.cmd
        if self.expanduser:
            cmd = [ expanduser(arg) for arg in cmd ]
        if self.expandvars:
            cmd = [ expandvars(arg) for arg in cmd ]

        return cmd, { **(self.kwargs or {}), 'shell': False, }
