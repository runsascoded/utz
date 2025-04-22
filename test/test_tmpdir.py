from os import getcwd, makedirs
from os.path import basename, join, exists, realpath, isdir, dirname
from tempfile import TemporaryDirectory

from utz import tmp_ensure_dir, TmpDir, TmpPath

cwd = getcwd()


def test_TmpDir():
    with TmpDir(dir='.') as subdir:
        name = basename(subdir)
        assert realpath(subdir) == join(cwd, name)
        assert exists(subdir)
    assert not exists(subdir)

    with TmpDir(dir='abc') as subdir:
        name = basename(subdir)
        assert realpath(subdir) == join(cwd, 'abc', name)
        assert exists(subdir)
    assert not exists(subdir)

    with TmpDir('name', dir='abc') as subdir:
        assert basename(subdir) == 'name'
        slug = basename(dirname(subdir))
        assert realpath(subdir) == join(cwd, 'abc', slug, 'name')
        assert exists(subdir)
    assert not exists(subdir)

    with TmpDir('name') as subdir:
        assert basename(subdir) == 'name'
        parent = dirname(subdir)
        assert exists(subdir)
    assert not exists(subdir)
    assert not exists(parent)


def test_tmp_ensure_dir():
    with TemporaryDirectory(dir='.') as tmpdir:
        name = basename(tmpdir)
        assert realpath(tmpdir) == join(cwd, name)
        dir1 = join(name, 'aaa')
        makedirs(dir1)
        dir2 = join(dir1, 'bbb')
        with tmp_ensure_dir(dir2):
            assert exists(dir2)
            assert isdir(dir2)
        assert not exists(dir2)
        assert exists(dir1)

        dir3 = join(dir2, 'ccc')
        with tmp_ensure_dir(dir3):
            assert exists(dir2)
            assert exists(dir3)
            assert isdir(dir2)
            assert isdir(dir3)
        assert not exists(dir2)
        assert not exists(dir3)
        assert exists(dir1)
    assert not exists(dir1)


def test_TmpPath():
    name = 'foo.txt'
    with TmpPath(name, dir='.') as path:
        assert basename(path) == name
        assert not exists(path)
        parent = dirname(path)
        slug = basename(parent)
        assert exists(parent)
        assert isdir(parent)
        assert realpath(path) == join(cwd, slug, name)
    assert not exists(parent)

    relpath = join('dir1', 'dir2', name)
    with TmpPath(relpath, dir='.') as path:
        assert basename(path) == name
        assert not exists(path)
        dir2 = dirname(path)
        assert basename(dir2) == 'dir2'
        dir1 = dirname(dir2)
        assert basename(dir1) == 'dir1'
        parent = dirname(dir1)
        slug = basename(parent)
        assert exists(parent)
        assert isdir(parent)
        assert realpath(path) == join(cwd, slug, relpath)
    assert not exists(parent)
