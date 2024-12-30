from os.path import join, dirname

import json
import pytest
from pytest import fixture, raises

from utz import env

parametrize = pytest.mark.parametrize
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile, TemporaryDirectory

from utz import proc
from utz.proc import *

TESTS = dirname(__file__)
SCRIPT = join(TESTS, 'streams-test.sh')
STRS = ['one', 'two', 'three']


def test_lines():
    assert lines('echo', '\n'.join(STRS)) == STRS
    assert lines('echo', '-n', '\n'.join(STRS)) == STRS
    assert lines('[', '1', '==', '2', ']', err_ok=True) is None
    with pytest.raises(CalledProcessError):
        lines('[', '1', '==', '2', ']')


def test_output():
    assert output('echo', '\n'.join(STRS)).decode() == '\n'.join(STRS + [''])
    assert output('echo', '-n', '\n'.join(STRS)).decode() == '\n'.join(STRS)
    assert output('[', '1', '==', '2', ']', err_ok=True) is None
    with pytest.raises(CalledProcessError):
        output('[', '1', '==', '2', ']')


def test_expandvars():
    interpolated = f'{env["USER"]} {env["HOME"]}'
    assert line('echo $USER $HOME', shell=True) == interpolated
    with raises(ValueError, match="Can't `expand{user,vars}` in shell mode"):
        assert line('echo $USER $HOME', shell=True, expandvars=True)
    assert line('echo', '$USER $HOME') == '$USER $HOME'
    assert line('echo', '$USER $HOME', expandvars=True) == interpolated


def test_json():
    obj = [{ 'a': { 'b': 123 } }]
    with NamedTemporaryFile() as f:
        path = f.name
        with open(path, 'w') as fd:
            json.dump(obj, fd)

        assert proc.json('cat', path) == obj
        assert proc.json('cat', 'nonexistent-file', err_ok=True) is None
        with raises(CalledProcessError):
            proc.json('cat', 'nonexistent-file')


def test_line():
    assert line('echo', 'yay') == 'yay'
    assert line('echo', '-n', 'yay') == 'yay'

    assert line('echo', '') == ''
    assert line('echo', '-n', '', empty_ok=True) is None
    with raises(ValueError):
        line('echo', '-n', '')
    assert line('[', '1', '==', '2', ']', err_ok=True) is None
    with raises(CalledProcessError):
        line('[', '1', '==', '2', ']')


def test_check():
    assert check('which', 'echo')
    assert not check('which', 'echoz')


def test_cmd_arg_flattening():
    assert output('echo', '-n', None, STRS, ['aaa', [None, 'bbb', 'ccc']]).decode() == ' '.join(
        STRS + ['aaa', 'bbb', 'ccc', ])


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
        output = pipeline(
            [['cat', '$FILE'], ['head', '-n5']],
            shell=False,
            expandvars=True,
        )
    assert output == '1\n2\n3\n4\n5\n'


def test_pipeline_vars_shell(tmp_text_file):
    output = pipeline(
        ['cat $FILE', 'head -n5'],
        shell=True,
        env={ **env, 'FILE': tmp_text_file },
    )
    assert output == '1\n2\n3\n4\n5\n'


def test_interleaved_stdout_stderr():
    assert proc.lines(SCRIPT) == ['stdout 1', 'stdout 2']
    assert proc.lines([SCRIPT], shell=False) == ['stdout 1', 'stdout 2']
    assert proc.lines(SCRIPT, both=True) == ['stdout 1', 'stderr 1', 'stdout 2', 'stderr 2']
    assert proc.lines([SCRIPT], shell=False, both=True) == ['stdout 1', 'stderr 1', 'stdout 2', 'stderr 2']


def test_interleaved_pipelines():
    assert pipeline([SCRIPT]) == 'stdout 1\nstdout 2\n'
    assert pipeline([SCRIPT, 'wc -l']) == '2\n'
    assert pipeline([SCRIPT], both=True) == 'stdout 1\nstderr 1\nstdout 2\nstderr 2\n'
    assert pipeline([SCRIPT, 'wc -l'], both=True) == '4\n'
