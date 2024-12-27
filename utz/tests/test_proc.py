from os.path import join

import json
from utz import env
import pytest
from pytest import fixture, raises, warns
parametrize = pytest.mark.parametrize
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile, TemporaryDirectory

from utz import proc
from utz.proc import *

strs = ['one', 'two', 'three']


def test_lines():
    assert lines('echo', '\n'.join(strs)) == strs
    assert lines('echo', '-n', '\n'.join(strs)) == strs
    assert lines('[', '1', '==', '2', ']', err_ok=True) is None
    with pytest.raises(CalledProcessError):
        lines('[', '1', '==', '2', ']')


def test_output():
    assert output('echo', '\n'.join(strs)).decode() == '\n'.join(strs + [''])
    assert output('echo', '-n', '\n'.join(strs)).decode() == '\n'.join(strs)
    assert output('[', '1', '==', '2', ']', err_ok=True) is None
    with pytest.raises(CalledProcessError):
        output('[', '1', '==', '2', ']')


def test_json():
    obj = [{
        'a': {
            'b': 123
        }
    }]
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
    assert output('echo', '-n', None, strs, ['aaa', [None, 'bbb', 'ccc']]).decode() == ' '.join(
        strs + ['aaa', 'bbb', 'ccc', ])


@parametrize(
    'cmds,shell,output', [
        (['seq 10', 'head -n5'], True, '1\n2\n3\n4\n5\n'),
        ([['seq', '10'], ['head', '-n5']], False, '1\n2\n3\n4\n5\n'),
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
            env={ **env, 'FILE': tmp_text_file },
        )
    assert output == '1\n2\n3\n4\n5\n'


def test_pipeline_vars_shell(tmp_text_file):
    output = pipeline(
        ['cat $FILE', 'head -n5'],
        shell=True,
        env={ **env, 'FILE': tmp_text_file },
    )
    assert output == '1\n2\n3\n4\n5\n'


def test_pipeline_shell_executable_warning():
    with warns(FutureWarning, match="`shell_executable` kwarg is deprecated"):
        pipeline(['seq 10', 'head -n5'], shell_executable=env['SHELL'])
