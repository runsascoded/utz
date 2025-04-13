import asyncio

from abc import ABC
from asyncio import iscoroutine
from os.path import dirname, join

import json
from typing import Iterable

import pytest
from pytest import fixture, raises

from utz import cd, env

parametrize = pytest.mark.parametrize
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile, TemporaryDirectory

from utz import proc
from utz.proc import *
from utz.process import aio


TESTS = dirname(__file__)
SCRIPT = join(TESTS, 'streams-test.sh')
STRS = ['one', 'two', 'three']


def eq(actual, expected):
    if iscoroutine(actual):
        actual = asyncio.run(actual)
    if expected is None:
        assert actual is None
    else:
        assert actual == expected


def wait(v):
    if iscoroutine(v):
        return asyncio.run(v)
    else:
        return v


class Base(ABC):
    @staticmethod
    def test_lines(mod):
        lines = mod.lines
        eq(lines('echo', '\n'.join(STRS)), STRS)
        eq(lines('echo', '-n', '\n'.join(STRS)), STRS)
        eq(lines('[', '1', '==', '2', ']', err_ok=None), None)
        eq(lines('[', '1', '==', '2', ']', err_ok=True), [])
        with raises(CalledProcessError):
            wait(lines('[', '1', '==', '2', ']'))

    @staticmethod
    def test_output(mod):
        text = mod.text
        output = mod.output
        eq(text('echo', '\n'.join(STRS)), '\n'.join(STRS + ['']))
        eq(text('echo', '-n', '\n'.join(STRS)), '\n'.join(STRS))
        eq(output('[', '1', '==', '2', ']', err_ok=None), None)
        eq(output('[', '1', '==', '2', ']', err_ok=True), b'')
        with raises(CalledProcessError):
            wait(output('[', '1', '==', '2', ']'))

    @staticmethod
    def test_expandvars(mod):
        line = mod.line
        interpolated = f'{env["USER"]} {env["HOME"]}'
        eq(line('echo $USER $HOME', shell=True), interpolated)
        eq(line('echo', '$USER $HOME'), '$USER $HOME')
        eq(line('echo', '$USER $HOME', expandvars=True), interpolated)
        with raises(ValueError, match="Can't `expand{user,vars}` in shell mode"):
            wait(line('echo $USER $HOME', shell=True, expandvars=True))

    @staticmethod
    def test_json(mod):
        obj = [{ 'a': { 'b': 123 } }]
        with NamedTemporaryFile() as f:
            path = f.name
            with open(path, 'w') as fd:
                json.dump(obj, fd)

            eq(mod.json('cat', path), obj)
            eq(mod.json('cat', 'nonexistent-file', err_ok=True), None)
            with raises(CalledProcessError):
                wait(mod.json('cat', 'nonexistent-file'))

    @staticmethod
    def test_line(mod):
        line = mod.line
        eq(line('echo', 'yay'), 'yay')
        eq(line('echo $var', env={'var': 'aaa'}), 'aaa')
        eq(line('echo yay'), 'yay')  # Single string ⟹ `shell=True`
        eq(line('echo', '-n', 'yay'), 'yay')
        eq(line('echo', ''), '')
        eq(line('echo', '-n', '', empty_ok=True), None)
        with raises(ValueError):
            wait(line('echo', '-n', ''))
        eq(line('[', '1', '==', '2', ']', err_ok=None), None)
        eq(line('[', '1', '==', '2', ']', err_ok=True), None)
        with raises(CalledProcessError):
            wait(line('[', '1', '==', '2', ']'))

    @staticmethod
    def test_check(mod):
        check = mod.check
        eq(check('which', 'echo'), True)
        eq(check('which', 'echoz'), False)

    @staticmethod
    def test_cmd_arg_flattening(mod):
        eq(
            mod.text('echo', '-n', None, STRS, ['aaa', [None, 'bbb', 'ccc']]),
            ' '.join(STRS + ['aaa', 'bbb', 'ccc', ]),
        )

    @staticmethod
    def test_interleaved_stdout_stderr(mod):
        lines = mod.lines
        eq(lines(SCRIPT), ['stdout 1', 'stdout 2'])
        eq(lines([SCRIPT]), ['stdout 1', 'stdout 2'])
        eq(lines(SCRIPT, both=True), ['stdout 1', 'stderr 1', 'stdout 2', 'stderr 2'])
        eq(lines([SCRIPT], both=True), ['stdout 1', 'stderr 1', 'stdout 2', 'stderr 2'])


class TestSubProc(Base):
    @fixture
    def mod(self):
        return proc


class TestAioProc(Base):
    @fixture
    def mod(self):
        return aio


@parametrize(
    'cmds,shell,output', [
        (['seq 10', 'head -n5'], True, '1\n2\n3\n4\n5\n'),
        ([['seq', '10'], ['head', '-n5']], False, '1\n2\n3\n4\n5\n'),
        (['seq 5'], True, '1\n2\n3\n4\n5\n'),
        ([['seq', '5']], False, '1\n2\n3\n4\n5\n'),
    ]
)
def test_pipeline(cmds, shell, output):
    assert pipeline(cmds, shell=shell) == output

    with TemporaryDirectory() as tmpdir:
        tmp_path = join(tmpdir, 'tmp.txt')
        pipeline(cmds, shell=shell, out=tmp_path)
        with open(tmp_path) as f:
            assert f.read() == output


@fixture
def tmp_text_file():
    with NamedTemporaryFile(mode='w') as f:
        f.write('\n'.join([ f'{n}' for n in range(1, 11) ]))
        f.flush()
        yield f.name


def test_pipeline_vars_no_shell(tmp_text_file):
    with env(FILE=tmp_text_file):
        assert pipeline(
            [['cat', '$FILE'], ['head', '-n5']],
            expandvars=True,
        ) == '1\n2\n3\n4\n5\n'


def test_pipeline_vars_err():
    with raises(
        CalledProcessError,
        match=r"Command 'cat \$FILE' returned non-zero exit status 1\.",
    ) as ei:
        pipeline([['cat', '$FILE']])
    assert ei.value.stderr == "cat: '$FILE': No such file or directory\n"


def test_pipeline_vars_err2(tmp_text_file):
    with (
        env(FILE=tmp_text_file),
        raises(
            CalledProcessError,
            match=r"Command 'grep 11' returned non-zero exit status 1\.",
        ) as ei,
    ):
        pipeline([f'cat {tmp_text_file}', 'grep 11'])
    assert ei.value.stderr == ""


def test_pipeline_vars_shell(tmp_text_file):
    output = pipeline(
        ['cat $FILE', 'head -n5'],
        env={ **env, 'FILE': tmp_text_file },
    )
    assert output == '1\n2\n3\n4\n5\n'


def test_interleaved_pipelines():
    assert pipeline([SCRIPT]) == 'stdout 1\nstdout 2\n'
    assert pipeline([SCRIPT, 'wc -l']) == '2\n'
    assert pipeline([SCRIPT], both=True) == 'stdout 1\nstderr 1\nstdout 2\nstderr 2\n'
    assert pipeline([SCRIPT, 'wc -l'], both=True) == '4\n'


def test_pipeline_errs_both():
    with TemporaryDirectory() as tmpdir:
        def save(name: str, lines: Iterable):
            with open(join(tmpdir, name), 'w') as f:
                print('\n'.join([ str(l) for l in lines ]), file=f)

        save('1.txt', range(10))
        save('2.txt', range(10, 0, -2))
        expected = [
            '0',
            '1',
            '\t10',
            '2',
            '3',
            '4',
            '5',
            '6',
            '7',
            '\t\t8',
            'comm: file 2 is not in sorted order',
            '\t6',
            '\t4',
            '\t2',
            '9',
            'comm: input is not in sorted order',
            '',
        ]
        with cd(tmpdir):
            assert pipeline(['comm 1.txt 2.txt'], both=True, err_ok=True).split('\n') == expected
            with raises(CalledProcessError) as ei:
                pipeline(['comm 1.txt 2.txt'], both=True)
            exc = ei.value
            assert exc.stdout.split('\n') == expected
            assert exc.stderr is None


def test_pipeline_errs():
    with TemporaryDirectory() as tmpdir:
        def save(name: str, lines: Iterable):
            with open(join(tmpdir, name), 'w') as f:
                print('\n'.join([ str(l) for l in lines ]), file=f)

        save('1.txt', range(10))
        save('2.txt', range(10, 0, -2))
        expected = [
            '0',
            '1',
            '\t10',
            '2',
            '3',
            '4',
            '5',
            '6',
            '7',
            '\t\t8',
            '\t6',
            '\t4',
            '\t2',
            '9',
            '',
        ]
        with cd(tmpdir):
            assert pipeline(['comm 1.txt 2.txt'], err_ok=True).split('\n') == expected
            with raises(CalledProcessError) as ei:
                pipeline(['comm 1.txt 2.txt'])
            exc = ei.value
            assert exc.stdout.split('\n') == expected
            assert exc.stderr.split('\n') == [
                'comm: file 2 is not in sorted order',
                'comm: input is not in sorted order',
                '',
            ]
