from __future__ import annotations

from json import loads

import asyncio
from subprocess import CalledProcessError, PIPE, CompletedProcess, DEVNULL

from utz.process import Cmd, err, Arg, Log, Json


async def run(
    *args: Arg,
    dry_run: bool = False,
    log: Log = err,
    check: bool = True,
    **kwargs,
) -> CompletedProcess | None:
    """Async convenience wrapper for subprocess execution."""
    cmd = Cmd.mk(*args, **kwargs)
    if dry_run:
        if log:
            log(f'Would run: {cmd}')
    else:
        args, kwargs = cmd.compile(log=log)
        proc = await asyncio.create_subprocess_exec(*args, **kwargs)
        await proc.wait()

        if check:
            if proc.returncode != 0:
                raise CalledProcessError(proc.returncode, args)
            return None
        else:
            # Creating CompletedProcess to match subprocess.run's return type
            return CompletedProcess(
                args=args,
                returncode=proc.returncode,
                # Only include stdout/stderr if they were captured
                stdout=None if proc.stdout is None else await proc.stdout.read(),
                stderr=None if proc.stderr is None else await proc.stderr.read(),
            )


sh = run


async def output(
    *args: Arg,
    dry_run: bool = False,
    both: bool = False,
    err_ok: bool | None = False,
    log: Log = err,
    **kwargs,
) -> bytes | None:
    """Async convenience wrapper for subprocess output capture.

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
            if kwargs['shell']:
                # For shell=True, we need to join args into a single string
                # and use create_subprocess_shell
                proc = await asyncio.create_subprocess_shell(
                    args,
                    stdout=PIPE,
                    **kwargs
                )
            else:
                proc = await asyncio.create_subprocess_exec(
                    *args,
                    stdout=PIPE,
                    **kwargs
                )

            # Stream and capture the output in real-time
            output = b''
            assert proc.stdout  # for type checking
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                output += line

            await proc.wait()
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


async def text(*args, **kwargs) -> str | None:
    return (await output(*args, **kwargs)).decode()


async def json(
    *cmd: Arg,
    dry_run: bool = False,
    err_ok: bool = False,
    **kwargs,
) -> Json:
    """Run a command, parse the output as JSON, and return the parsed object."""
    out = await output(*cmd, dry_run=dry_run, err_ok=err_ok, **kwargs)
    if out is None or err_ok is True and not out:
        return None
    return loads(out.decode())


async def check(
    *cmd: Arg,
    stdout=DEVNULL,
    stderr=DEVNULL,
    **kwargs,
):
    """Run a command, return True iff it runs successfully (i.e. exits with code 0)."""
    try:
        await run(*cmd, stdout=stdout, stderr=stderr, **kwargs)
        return True
    except CalledProcessError:
        return False


async def lines(
    *cmd: Arg,
    keep_trailing_newline: bool = False,
    dry_run: bool = False,
    err_ok: bool = False,
    **kwargs,
) -> list[str] | None:
    """Return the lines written to stdout by a command."""
    out = await output(*cmd, dry_run=dry_run, err_ok=err_ok, **kwargs)
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


async def line(
    *cmd: Arg,
    empty_ok: bool = False,
    err_ok: bool = False,
    **kwargs,
) -> str | None:
    """Run a command, verify that it returns a single line of output, and return that line."""
    _lines = await lines(*cmd, err_ok=err_ok, **kwargs)
    if (empty_ok or err_ok is not False) and not _lines:
        return None
    elif len(_lines) == 1:
        return _lines[0]
    else:
        raise ValueError(f'Expected 1 line, found {len(_lines)}:\n\t%s' % '\n\t'.join(_lines))


__all__ = [
    'text',
    'json',
    'check',
    'line',
    'lines',
    'run',
    'output',
    'sh',
]
