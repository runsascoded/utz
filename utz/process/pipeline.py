from __future__ import annotations

from io import UnsupportedOperation, StringIO
from subprocess import Popen, PIPE
from typing import Literal, AnyStr, IO

from utz.process import Cmd


def pipeline(
    cmds: list[str] | list[list[str]] | list[Cmd],
    out: str | IO[AnyStr] | None = None,
    mode: Literal['b', 't', None] = None,
    shell: bool | str | None = None,
    executable: str | None = None,
    wait: bool = True,
    expanduser: bool | None = None,
    expandvars: bool | None = None,
    **kwargs,
) -> str | list[Popen] | None:
    """Run a pipeline of commands, writing the final stdout to a file or ``IO``, or returning it as a ``str``"""
    processes = []
    prev_process: Popen | None = None

    cmds = [
        cmd if isinstance(cmd, Cmd) else
        Cmd.mk(
            cmd,
            shell=shell,
            executable=executable,
            expanduser=expanduser,
            expandvars=expandvars,
            **kwargs,
        )
        for cmd in cmds
    ]

    return_output = False
    if out is None:
        out = StringIO()
        return_output = True
        if not wait:
            raise ValueError("Can't return output with `wait=False`")

    if mode is None:
        mode = 't' if isinstance(out, StringIO) else 'b'

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
            args, kwargs = cmd.compile()
            return Popen(
                args,
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
