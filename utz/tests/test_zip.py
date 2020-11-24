
from os.path import exists, isdir, isfile, join
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from utz.zip import try_unzip

def test_unzip():
    files = {
        'a': 'yay',
        'b/c': 'CCC',
        'b/d': 'DDD',
    }

    with TemporaryDirectory() as tmpdir:
        name = 'test'
        zip_path = join(tmpdir, f'{name}.zip')
        with ZipFile(zip_path,'w') as z:
            for path, contents in files.items():
                z.writestr(path, contents)

        zip_dir = join(tmpdir, name)
        assert try_unzip(zip_path) == zip_dir
        assert not exists(zip_path)
        assert exists(zip_dir)
        assert isdir(zip_dir)

        for path, contents in files.items():
            with open(join(zip_dir,path),'r') as f:
                assert f.read() == contents

        a_path = join(zip_dir,'a')
        assert try_unzip(a_path) == a_path
        assert isfile(a_path)

    with TemporaryDirectory() as tmpdir:
        name = 'test'
        zip_path = join(tmpdir, name)
        with ZipFile(zip_path,'w') as z:
            for path, contents in files.items():
                z.writestr(path, contents)

        zip_dir = zip_path
        assert try_unzip(zip_path) == zip_dir
        assert not exists(f'{zip_path}.zip')
        assert exists(zip_dir)
        assert isdir(zip_dir)

        for path, contents in files.items():
            with open(join(zip_dir,path),'r') as f:
                assert f.read() == contents

        a_path = join(zip_dir,'a')
        assert try_unzip(a_path) == a_path
        assert isfile(a_path)
