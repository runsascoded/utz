from __future__ import annotations

import typing
from click import command
from click.testing import CliRunner
from functools import partial
from typing import Literal

from utz.cli import cmd, count, num, obj, flag, parse_int, multi

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
    assert actual_lines == list(expected_lines)
    assert res.exit_code == exit_code
    if not exit_code:
        assert res.exception is None
    if msg is not None:
        assert res.exception.args == (msg,)


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
