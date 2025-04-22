from os import getcwd
from os.path import basename, join, exists
from tempfile import TemporaryDirectory

from utz import cd, cd_tmpdir

cwd = getcwd()


def test_cd():
    with TemporaryDirectory(dir='.') as subdir:
        name = basename(subdir)
        with cd(name):
            assert getcwd() == join(cwd, name)
            with cd('..'):
                assert getcwd() == cwd
        assert getcwd() == cwd
    assert not exists(subdir)


def test_cd_tmpdir():
    with cd_tmpdir(dir='.') as subdir:
        name = basename(subdir)
        assert getcwd() == join(cwd, name)
    assert not exists(subdir)

    with cd_tmpdir(dir='abc') as subdir:
        name = basename(subdir)
        assert getcwd() == join(cwd, 'abc', name)
    assert not exists(subdir)
