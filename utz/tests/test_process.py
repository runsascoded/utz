
import pytest

from utz.process import *

strs = ['one','two','three']

def test_lines():
    assert lines('echo','\n'.join(strs)) == strs
    assert lines('echo','-n','\n'.join(strs)) == strs
    assert lines('[','1','==','2',']',err_ok=True) is None
    with pytest.raises(CalledProcessError):
        lines('[','1','==','2',']')

def test_output():
    assert output('echo','\n'.join(strs)).decode() == '\n'.join(strs+[''])
    assert output('echo','-n','\n'.join(strs)).decode() == '\n'.join(strs)
    assert output('[','1','==','2',']',err_ok=True) is None
    with pytest.raises(CalledProcessError):
        output('[','1','==','2',']')

def test_line():
    assert line('echo','yay') == 'yay'
    assert line('echo','-n','yay') == 'yay'

    assert line('echo','') == ''
    assert line('echo','-n','', empty_ok=True) is None
    with pytest.raises(ValueError):
        line('echo','-n','')
    assert line('[','1','==','2',']',err_ok=True) is None
    with pytest.raises(CalledProcessError):
        line('[','1','==','2',']')

def test_check():
    assert check('which','echo')
    assert not check('which','echoz')

def test_cmd_arg_flattening():
    assert output('echo','-n',None,strs,['aaa',[None,'bbb','ccc']]).decode() == ' '.join(strs + ['aaa','bbb','ccc',])
