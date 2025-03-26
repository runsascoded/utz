from __future__ import annotations

import pytest
import typing
from click import command, argument
from click.testing import CliRunner
from functools import partial
from typing import Literal

from utz.cli import cmd, count, num, obj, flag, parse_int, multi, inc_exc, incs, multi_cb, excs
from utz.rgx import Patterns, Includes

parametrize = pytest.mark.parametrize

Verbosity = Literal["warn", "info", "debug"]
Verbosities = typing.get_args(Verbosity)


def _check(
    cli,
    args: list[str],
    *expected_lines: str,
    exit_code: int = 0,
    msg: str | None = None,
):
    runner = CliRunner()
    res = runner.invoke(cli, args)
    actual_lines = res.output.split('\n')
    if not actual_lines[-1]:
        actual_lines.pop()

    expected = [ list(expected_lines), exit_code ]
    actual = [ actual_lines, res.exit_code ]
    if exit_code == 0 and res.exit_code != 0:
        raise res.exception
    if msg is not None:
        expected.append((msg,))
        actual.append(res.exception.args)
    assert actual == expected


def checks(cli):
    return partial(_check, cli), partial(_check, cli, exit_code=2)


def test_count_enum():
    @command
    @count('-v', '--verbosity', values=Verbosities, help="0x: warn, 1x: info, 2x: debug")
    def count_cli(verbosity: Verbosity):
        print(verbosity)

    check, fail = checks(count_cli)
    check([], "warn")
    check(['-v'], 'info')
    check(['-vv'], 'debug')
    check(['-v', '-v'], 'debug')
    fail(
        ['-vvv'],
        "Usage: count-cli [OPTIONS]",
        "Try 'count-cli --help' for help.",
        "",
        "Error: Invalid value for '-v' / '--verbosity': expected [0,3), found 3",
    )


def test_count():
    @command
    @count('-v', '--verbosity', help="0x: warn, 1x: info, 2x: debug")
    def count_cli(verbosity: int):
        print(verbosity)

    check, _ = checks(count_cli)
    check([], '0')
    check(['-v'], '1')
    check(['-vv'], '2')
    check(['-v', '-v'], '2')
    check(['-vvv'], '3')


def test_num_opt():
    @command
    @num('-n', '--num')
    def num_opt_cli(num: int | None):
        if num is not None:
            assert isinstance(num, int)
        print(num)

    check, fail = checks(num_opt_cli)
    check([], 'None')
    check(['-n', '123'], '123')
    check(['-n10k'], '10000')
    check(['-n10Ki'], '10240')
    check(['-n1.0123m'], '1012300')
    check(['-n1Gi'], str(2**30))
    fail(
        ['-n1bi'],
        "Usage: num-opt-cli [OPTIONS]",
        "Try 'num-opt-cli --help' for help.",
        "",
        "Error: Invalid value for '-n' / '--num': failed to parse \"1bi\"",
    )


def test_num():
    @command
    @num('-n', '--num', default=111)
    def num_cli(num: int):
        print(num)

    check, fail = checks(num_cli)
    check(['-n', '123'], '123')
    check(['-n10k'], '10000')
    check(['-n10Ki'], '10240')
    check(['-n1.0123m'], '1012300')
    check([], '111')


def test_num_required():
    @command
    @num('-n', '--num', required=True)
    def num_cli(num: int):
        print(num)

    check, fail = checks(num_cli)
    check(['-n', '123'], '123')
    check(['-n10k'], '10000')
    check(['-n10Ki'], '10240')
    check(['-n1.0123m'], '1012300')
    fail(
        [],
        'Usage: num-cli [OPTIONS]',
        "Try 'num-cli --help' for help.",
        '',
        "Error: Missing option '-n' / '--num'.",
    )


def test_obj():
    @cmd
    @obj('-e', '--env')
    @flag('-v', '--verbose')
    def obj_cli(env: dict[str, str], verbose: bool):
        for k, v in env.items():
            if verbose:
                print(f'{k=} {v=}')
            else:
                print(f'{k}={v}')

    check, fail = checks(obj_cli)
    check(['-e', 'NUM=111'], 'NUM=111')
    check(['-e', 'NUM=111', '-eSTR=abc'], 'NUM=111', 'STR=abc')
    check([])
    check(['--env', '==', '-e===', '-v'], "k='' v='=='")
    fail(
        ['-e', '123'],
        "Usage: obj-cli [OPTIONS]",
        "Try 'obj-cli --help' for help.",
        "",
        "Error: Invalid value for '-e' / '--env': bad value: 123",
    )


def test_obj_parse():
    @command
    @obj('-n', '--num', 'nums', parse=parse_int)
    @flag('-v', '--verbose')
    def obj_cli(nums: dict[str, int], verbose: bool):
        for k, v in nums.items():
            if verbose:
                print(f'{k=} {v=}')
            else:
                print(f'{k}={v:,}')

    check, fail = checks(obj_cli)
    check(['-n', 'lo=10k'], 'lo=10,000')
    check(['-n', 'lo=111', '-nhi=222'], 'lo=111', 'hi=222')
    check([])
    fail(['--num', '='], exit_code=1, msg='Failed to parse ""')
    fail(
        ['-n', '123'],
        "Usage: obj-cli [OPTIONS]",
        "Try 'obj-cli --help' for help.",
        "",
        "Error: Invalid value for '-n' / '--num': bad value: 123",
    )


def test_multi():
    @command
    @multi('-n', '--num', 'nums', parse=parse_int)
    def obj_cli(nums: tuple[int, ...]):
        assert isinstance(nums, tuple)
        if nums:
            print(f"{', '.join(f'{n:,}' for n in nums)}")

    check, fail = checks(obj_cli)
    check(['-n', '10k,1m,111'], '10,000, 1,000,000, 111')
    check(['-n', '10k,1m', '--num', '111'], '10,000, 1,000,000, 111')
    # check(['-n', 'lo=111', '-nhi=222'], 'lo=111', 'hi=222')
    check([])
    fail(
        ['--num', ''],
        "Usage: obj-cli [OPTIONS]",
        "Try 'obj-cli --help' for help.",
        "",
        "Error: Invalid value for '-n' / '--num': failed to parse \"\"",
    )
    fail(
        ['-n', '111', '--num', '12a'],
        "Usage: obj-cli [OPTIONS]",
        "Try 'obj-cli --help' for help.",
        "",
        "Error: Invalid value for '-n' / '--num': failed to parse \"12a\"",
    )


# Example strings to test vs. regexs /a./ and /b/ below
matches = ['aa', 'bc', 'cb']
misses = ['c', 'a', 'AA', 'B']
both = matches + misses


def test_inc_exc():
    @command
    @inc_exc(
        multi('-i', '--include', help="Print arguments iff they match at least one of these regexs; comma-delimited, and can be passed multiple times"),
        multi('-x', '--exclude', help="Print arguments iff they don't match any of these regexs; comma-delimited, and can be passed multiple times"),
    )
    @argument('vals', nargs=-1)
    def cli(patterns: Patterns, vals: tuple[str, ...]):
        for val in vals:
            assert patterns.pats != []  # patterns.pats should be `None` when no patterns are passed, which also implies `not bool(patterns)`
            if patterns(val):
                print(val)

    check, fail = checks(cli)
    check(both, *both)
    check(['-i', 'a.,b', *both], *matches)
    check(['-i', 'a.', '--include', 'b', *both], *matches)
    check(['-x', 'a.,b', *both], *misses)
    check(['-x', 'a.', '--exclude', 'b', *both], *misses)
    fail(['-i', 'a', '-x', 'b'], msg='Pass -i/--include xor -x/--exclude', exit_code=1)


@parametrize(
    'deco,args,expected', [
        *[
            (deco, args, expected)
            for deco in [
                # `incs` can receive a fully-constructed `click` decorator, e.g. using the `multi` helper:
                incs(multi('-i', '--include', 'patterns', help="Print arguments iff they match at least one of these regexs; comma-delimited, and can be passed multiple times")),
                # `incs` can also receive args/kwargs that will be passed to `click.option`, to construct a decorator; this example recreates what `multi` does above:
                incs('-i', '--include', 'patterns', multiple=True, callback=multi_cb, help="Print arguments iff they match at least one of these regexs; comma-delimited, and can be passed multiple times"),
            ]
            for args, expected in [
                ([*both], both),
                ([ '-i', 'a.,b', *both], matches),
                ([ '-i', 'a.', '--include', 'b', *both], matches),
                ([ '-i', '[A-Z]', 'AAA', 'bbb', 'CCC', 'ddd', ], ['AAA', 'CCC']),
            ]
        ],
        *[
            (
                # Simple, non-"multi" version:
                incs('-i', '--include', 'patterns', help="Print arguments iff they match at least one of these regexs; comma-delimited"),
                args, expected,
            ) for args, expected in [
                ([ '-i', '[A-Z]', 'AAA', 'bbb', 'CCC', 'ddd', ], ['AAA', 'CCC']),
                ([ 'AAA', 'bbb', 'CCC', 'ddd', ], [ 'AAA', 'bbb', 'CCC', 'ddd', ]),
            ]
        ],
        *[
            (deco, args, expected)
            for deco in [
                # Similarly, `excs` can receive a fully-constructed `click` decorator, e.g. using the `multi` helper:
                excs(multi('-x', '--exclude', 'patterns', help="Print arguments iff they don't match any of these regexs; comma-delimited, and can be passed multiple times")),
                # `excs` can also receive args/kwargs that will be passed to `click.option`, to construct a decorator; this example recreates what `multi` does above:
                excs('-x', '--exclude', 'patterns', multiple=True, callback=multi_cb, help="Print arguments iff they don't match any of these regexs; comma-delimited, and can be passed multiple times"),
            ]
            for args, expected in [
                ([*both], both),
                ([ '-x', 'a.,b', *both], misses),
                ([ '-x', 'a.', '--exclude', 'b', *both], misses),
                ([ '-x', '[A-Z]', 'AAA', 'bbb', 'CCC', 'ddd', ], ['bbb', 'ddd']),
            ]
        ],
        *[
            (
                # Simple, non-"multi" version:
                excs('-x', '--exclude', 'patterns', help="Print arguments iff they don't match any of these regexs; comma-delimited"),
                args, expected,
            ) for args, expected in [
                ([ '-x', '[A-Z]', 'AAA', 'bbb', 'CCC', 'ddd', ], ['bbb', 'ddd']),
                ([ 'AAA', 'bbb', 'CCC', 'ddd', ], [ 'AAA', 'bbb', 'CCC', 'ddd', ]),
            ]
        ],
    ],
)
def test_incs(deco, args, expected):
    @command
    @deco
    @argument('vals', nargs=-1)
    def cli(patterns: Patterns, vals: tuple[str, ...]):
        for val in vals:
            if patterns(val):
                print(val)

    check, _ = checks(cli)
    check(args, *expected)


def test_incs_arg():
    @command
    @argument('val_str')
    # `incs` can even accept a `click.argument`; in this case, multiple comma-delimited strings are accepted:
    @incs(argument('includes', callback=multi_cb, nargs=-1))
    def cli(val_str: str, includes: Includes):
        for val in val_str.split(' '):
            if includes(val):
                print(val)

    check, _ = checks(cli)
    check([' '.join(both), 'a.', 'b'], *matches)
    check([' '.join(both), 'a.,b'], *matches)
