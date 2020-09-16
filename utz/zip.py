from os.path import join, splitext
from pathlib import Path
from zipfile import is_zipfile, ZipFile


def try_unzip(path):
    if isinstance(path, Path):
        path = str(path)
    if is_zipfile(path):
        from shutil import move
        name, ext = splitext(path)
        if ext == '.zip':
            zip_path = path
            path = join(path.parent, name)
        else:
            zip_path = join(path.parent, '%s.zip' % name)
            print('Renaming %s to %s' % (path, zip_path))
            move(path, zip_path)

        print('Extracting %s to %s' % (zip_path, path))
        with ZipFile(zip_path) as f:
            f.extractall(path)

        zip_path.unlink()

    return path
