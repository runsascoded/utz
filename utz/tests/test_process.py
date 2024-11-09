from os.path import join

from io import StringIO

import json
import pytest
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile, TemporaryDirectory

from utz import process
from utz.process import *

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

        assert process.json('cat', path) == obj
        assert process.json('cat', 'nonexistent-file', err_ok=True) is None
        with pytest.raises(CalledProcessError):
            process.json('cat', 'nonexistent-file')


def test_line():
    assert line('echo', 'yay') == 'yay'
    assert line('echo', '-n', 'yay') == 'yay'

    assert line('echo', '') == ''
    assert line('echo', '-n', '', empty_ok=True) is None
    with pytest.raises(ValueError):
        line('echo', '-n', '')
    assert line('[', '1', '==', '2', ']', err_ok=True) is None
    with pytest.raises(CalledProcessError):
        line('[', '1', '==', '2', ']')


def test_check():
    assert check('which', 'echo')
    assert not check('which', 'echoz')


def test_cmd_arg_flattening():
    assert output('echo', '-n', None, strs, ['aaa', [None, 'bbb', 'ccc']]).decode() == ' '.join(
        strs + ['aaa', 'bbb', 'ccc', ])


def test_pipeline():
    assert pipeline(['seq 10', 'head -n5']) == '1\n2\n3\n4\n5\n'

    with TemporaryDirectory() as tmpdir:
        tmp_path = join(tmpdir, 'tmp.txt')
        pipeline(['seq 10', 'head -n5'], tmp_path)
        with open(tmp_path) as f:
            assert f.read() == '1\n2\n3\n4\n5\n'
