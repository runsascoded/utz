from __future__ import annotations

from warnings import warn

from io import UnsupportedOperation, StringIO
from os import environ as env, path
from subprocess import Popen, PIPE
from typing import Literal, AnyStr, IO


class Unset:
    def __bool__(self):
        return False


_Unset = Unset()


def pipeline(
    cmds: list[str] | list[list[str]],
    out: str | IO[AnyStr] | None = None,
    mode: Literal['b', 't', None] = None,
    shell: bool | str | None = _Unset,
    executable: str | None = _Unset,
    wait: bool = True,
    expanduser: bool | None = None,
    expandvars: bool | None = None,
    **kwargs,
) -> str | list[Popen] | None:
    """Run a pipeline of commands, writing the final stdout to a file or ``IO``, or returning it as a ``str``"""
    processes = []
    prev_process: Popen | None = None

    if 'shell_executable' in kwargs:
        msg = "`shell_executable` kwarg is deprecated, use `executable` instead"
        if executable is _Unset:
            executable = kwargs.pop('shell_executable')
            warn(msg, FutureWarning, stacklevel=2)
        else:
            raise ValueError(msg)

    if executable:
        if shell is _Unset:
            shell = True

    if isinstance(shell, str):
        if executable is _Unset:
            executable = shell
            shell = True
        else:
            if shell != executable:
                raise ValueError(f"Pass `shell` xor `executable` (or make sure they match): {shell} != {executable}")

    if shell and executable is _Unset:
        executable = env.get('SHELL')

    if shell is not _Unset:
        kwargs['shell'] = shell

    if executable is not _Unset:
        kwargs['executable'] = executable

    return_output = False
    if out is None:
        out = StringIO()
        return_output = True
        if not wait:
            raise ValueError("Can't return output with `wait=False`")

    if mode is None:
        mode = 't' if isinstance(out, StringIO) else 'b'

    if shell:
        # `expand{user,vars}` are implicitly True in "shell" mode
        if expanduser is False:
            raise ValueError("`expanduser` is implicitly True when `shell=True`, `expanduser=False` not allowed")
        if expandvars is False:
            raise ValueError("`expandvars` is implicitly True when `shell=True`, `expandvars=False` not allowed")
    else:
        # `expand{user,vars}` default to False in non-shell mode
        if expanduser:
            cmds = [
                [ path.expanduser(arg) for arg in cmd ]
                for cmd in cmds
            ]
        if expandvars:
            cmds = [
                [ path.expandvars(arg) for arg in cmd ]
                for cmd in cmds
            ]

    # If out is StringIO/BytesIO, use PIPE instead
    use_pipe = False
    if hasattr(out, 'write'):
        try:
            out.fileno()
        except UnsupportedOperation:
            use_pipe = True

    for i, cmd in enumerate(cmds):
        is_last = i + 1 == len(cmds)

        # For the first process, take input from the original source
        stdin = None if prev_process is None else prev_process.stdout

        def mkproc(stdout=PIPE):
            return Popen(
                cmd,
                stdin=stdin,
                stdout=stdout,
                **kwargs
            )

        # For the last process
        if is_last:
            if use_pipe:
                proc = mkproc()
                # Read the output and write to the StringIO/BytesIO
                output = proc.stdout.read()
                if mode == 't' and isinstance(output, bytes):
                    output = output.decode()
                out.write(output)
            else:
                with (open(out, f'w{mode}') if isinstance(out, str) else out) as pipe_fd:
                    proc = mkproc(pipe_fd)
        # For intermediate processes, output to a pipe
        else:
            proc = mkproc()

        if prev_process is not None:
            prev_process.stdout.close()

        processes.append(proc)
        prev_process = proc

    if not wait:
        return processes

    for p in processes:
        p.wait()

    if return_output:
        return out.getvalue()
