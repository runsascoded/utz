from subprocess import Popen

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
