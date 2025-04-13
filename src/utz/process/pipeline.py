from __future__ import annotations

from io import UnsupportedOperation, StringIO
from subprocess import Popen, PIPE, STDOUT, CalledProcessError
from typing import AnyStr, IO, Literal

from utz.process import Cmd


def pipeline(
    cmds: list[str] | list[list[str]] | list[Cmd],
    out: str | IO[AnyStr] | None = None,
    mode: Literal['b', 't', None] = None,
    wait: bool = True,
    both: bool = False,
    err_ok: bool = False,
    **kwargs,
) -> str | list[Popen] | None:
    """Run a pipeline of commands, writing the final stdout to a file or ``IO``, or returning it as a ``str``"""
    processes = []
    prev_process: Popen | None = None

    cmds = [
        cmd if isinstance(cmd, Cmd) else
        Cmd.mk(cmd, **kwargs)
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

    # Collect stderr for error reporting (if not redirecting stderr to stdout)
    stderr_pipes = [] if not both else None

    for i, cmd in enumerate(cmds):
        is_last = i + 1 == len(cmds)

        # For the first process, take input from the original source
        stdin = None if prev_process is None else prev_process.stdout

        def mkproc(stdout=PIPE):
            args, kwargs = cmd.compile(both=both)
            kwargs['stderr'] = STDOUT if both else PIPE
            return Popen(
                args,
                stdin=stdin,
                stdout=stdout,
                **kwargs,
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
        if not both:
            stderr_pipes.append(proc.stderr)
        prev_process = proc

    if not wait:
        return processes

    for p in processes:
        p.wait()

    def get_output():
        if isinstance(out, str):
            with open(out, 'rt') as f:
                return f.read()
        else:
            return out.getvalue()

    if not err_ok:
        # Check for errors + `raise`
        for i, p in enumerate(processes):
            returncode = p.returncode

            if returncode != 0:
                # Collect stderr from the process, if available
                stdout_output = p.stdout.read()
                if isinstance(stdout_output, bytes):
                    stdout_output = stdout_output.decode('utf-8', errors='replace')

                if stderr_pipes:
                    stderr_output = stderr_pipes[i].read()
                elif p.stderr:
                    stderr_output = p.stderr.read()
                else:
                    stderr_output = None
                if isinstance(stderr_output, bytes):
                    stderr_output = stderr_output.decode('utf-8', errors='replace')

                # Prepare the original command for the error message
                cmd_args, _ = cmds[i].compile()
                cmd_str = ' '.join(str(arg) for arg in cmd_args) if isinstance(cmd_args, list) else cmd_args

                if not stdout_output and (not both or not stderr_output):
                    stdout_output = get_output()
                raise CalledProcessError(
                    returncode,
                    cmd_str,
                    output=stdout_output,
                    stderr=stderr_output,
                )

    if return_output:
        return get_output()
