from __future__ import annotations

from typing import Tuple

from subprocess import Popen

from utz import process
from utz.process import err
from utz.process.named_pipes import named_pipes
from utz.process.pipeline import pipeline


def diff_cmds(
    cmds1: list[str],
    cmds2: list[str],
    verbose: bool = False,
    color: bool = False,
    unified: int | None = None,
    ignore_whitespace: bool = False,
    **kwargs,
):
    """Run two sequences of piped commands and diff their output.

    Args:
        cmds1: First sequence of commands to pipe together
        cmds2: Second sequence of commands to pipe together
        verbose: Whether to print commands being executed
        color: Whether to show colored diff output
        unified: Number of unified context lines, or None
        ignore_whitespace: Whether to ignore whitespace changes
        **kwargs: Additional arguments passed to subprocess.Popen

    Each command sequence will be piped together before being compared.
    For example, if cmds1 = ['cat foo.txt', 'sort'], the function will
    execute 'cat foo.txt | sort' before comparing with cmds2's output.

    Adapted from https://stackoverflow.com/a/28840955"""
    with named_pipes(n=2) as pipes:
        (pipe1, pipe2) = pipes
        diff_cmd = [
            'diff',
            *(['-w'] if ignore_whitespace else []),
            *(['-U', str(unified)] if unified is not None else []),
            *(['--color=always'] if color else []),
            pipe1,
            pipe2,
        ]
        diff = Popen(diff_cmd)
        processes = [diff]

        for pipe, cmds in ((pipe1, cmds1), (pipe2, cmds2)):
            if verbose:
                err(f"Running pipeline: {' | '.join(cmds)}")

            processes += pipeline(cmds, pipe, wait=False, **kwargs)

        for p in processes:
            p.wait()


def main():
    from click import argument, option, command

    @command('diff-x', short_help='Diff two files after running them through a pipeline of other commands', no_args_is_help=True)
    @option('-c', '--color', is_flag=True, help='Colorize the output')
    @option('-S', '--no-shell', is_flag=True, help="Don't pass `shell=True` to Python `subprocess`es")
    @option('-U', '--unified', type=int, help='Number of lines of context to show (passes through to `diff`)')
    @option('-v', '--verbose', is_flag=True, help="Log intermediate commands to stderr")
    @option('-w', '--ignore-whitespace', is_flag=True, help="Ignore whitespace differences (pass `-w` to `diff`)")
    @option('-x', '--exec-cmd', 'exec_cmds', multiple=True, help='Command(s) to execute before diffing; alternate syntax to passing commands as positional arguments')
    @argument('args', metavar='[exec_cmd...] <path>', nargs=-1)
    def cli(
        color: bool,
        no_shell: bool,
        unified: int | None,
        verbose: bool,
        ignore_whitespace: bool,
        exec_cmds: Tuple[str, ...],
        args: Tuple[str, ...],
    ):
        if len(args) < 2:
            raise ValueError('Must provide at least two files to diff')
        *cmds, path1, path2 = args
        cmds = list(exec_cmds) + cmds
        if cmds:
            first, *rest = cmds
            cmds1 = [ f'{first} {path1}', *rest ]
            cmds2 = [ f'{first} {path2}', *rest ]
            diff_cmds(
                cmds1,
                cmds2,
                shell=not no_shell,
                verbose=verbose,
                color=color,
                unified=unified,
                ignore_whitespace=ignore_whitespace,
            )
        else:
            process.run(['diff', path1, path2])

    cli()


if __name__ == '__main__':
    main()
