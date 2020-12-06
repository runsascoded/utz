
from contextlib import AbstractContextManager
import json
from os.path import exists, join
from os import getcwd, remove
import re
import shlex
from shutil import copy
from tempfile import NamedTemporaryFile
from types import TracebackType
from typing import Optional, Type

from .process import run, sh


def escape(*args):
    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, dict):
            return " ".join(escape(k, v) for k,v in arg.items())
        else:
            backslashes = re.sub(r'\\',r'\\\\',str(arg))
            return re.sub(r'(["\n])',r'\\\1',backslashes)
    elif len(args) == 2:
        k,v = args
        return f'"{escape(k)}"="{escape(v)}"'


class File(AbstractContextManager):
    def __init__(self, path=None, tag=None, rm=None, copy_dir=None, extend=None, **kwargs):
        if kwargs:
            if 'dir' in kwargs:
                dir = kwargs.pop('dir')
            else:
                dir = getcwd()
            if kwargs:
                raise ValueError(f'Unrecognized kwargs: {kwargs}')
        else:
            dir = getcwd()
        if path:
            self.rm = bool(rm)
        else:
            path = NamedTemporaryFile(prefix='Dockerfile.', dir=dir).name
            self.rm = rm != False
        self.path = path
        self.fd = None
        self.tag = tag
        self.dir = dir
        self.copy_dir = copy_dir
        if extend:
            copy(extend, path)

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType]
    ):
        self.close(closed_ok=True)
        if exists(self.path):
            remove(self.path)

    def write(self, *lines, open_ok=True):
        if not self.fd:
            if not open_ok:
                raise RuntimeError(f"Refusing to write to {self.path} that's not already open")
            if exists(self.path):
                mode = 'a'
            else:
                mode = 'w'
            self.fd = open(self.path,mode)
        for line in lines:
            self.fd.write('%s\n' % line)

    def close(self, closed_ok=False):
        if self.fd:
            self.fd.close()
            self.fd = None
        elif not closed_ok:
            raise RuntimeError(f"Can't close {self.path}; not open")

    def build(self, tag=None, dir=None, closed_ok=False, **build_args):
        self.close(closed_ok=closed_ok)

        tag = tag or self.tag
        dir = dir or self.dir or '.'
        if not tag:
            raise ValueError(f'Missing tag for image build')

        run(
            'docker','build',
            '-f',self.path,
            '-t',tag,
            [ ['--build-arg',f'{k}={v}'] for k,v in build_args.items() ],
            dir
        )
        if self.rm:
            remove(self.path)

        return Image(tag, self)

    def COPY(self, *args, **kwargs):
        (*srcs, dst) = args
        if 'dir' in kwargs:
            dir = kwargs.pop('dir')
            if kwargs:
                raise ValueError(f'Unexpected kwargs: {",".join(kwargs)}')
        else:
            dir = self.copy_dir
        if dir:
            srcs = [ join(dir, src) for src in srcs ]
        self.write(f'COPY {" ".join([*srcs, dst])}')

    def kvs(self, cmd, *args, **kwargs):
        flattened = []
        for arg in args:
            if isinstance(arg, str):
                flattened.append(arg)
            elif isinstance(arg, tuple):
                if len(arg) != 2:
                    raise RuntimeError(f'Invalid tuple arg (required len 2): %s' % str(arg))
                k,v = arg
                k = escape(str(k))
                v = escape(str(v))
                flattened.append(f'"{k}"="{v}"')
            elif isinstance(arg, dict):
                for k,v in arg.items():
                    flattened.append(f'"{escape(k)}"="{escape(v)}"')
            else:
                raise ValueError(f'Unrecognized argument to {cmd}: {arg}')
        for k,v in kwargs.items():
            flattened.append(f'"{escape(k)}"="{escape(v)}"')
        if flattened:
            self.write(f'{cmd} {" ".join(flattened)}')

    def NOTE(self, *lines):
        self.write(*[f'# {line}' for line in lines])

    def ENV(self, *args, **kwargs):
        return self.kvs('ENV', *args, **kwargs)

    def LABEL(self, *args, **kwargs):
        return self.kvs('LABEL', *args, **kwargs)

    def RUN(self, *cmds):
        if cmds:
            self.write('RUN %s' % ' \\\n && '.join(cmds))

    def ARG(self, k, v=None):
        if v is None:
            self.write(f'ARG {k}')
        else:
            self.write(f'ARG {k}={v}')

    def FROM(self, repo, tag=None, registry=None):
        if registry:
            repo = f'{registry}/{repo}'
        if tag:
            repo = f'{repo}:{tag}'
        self.write(f'FROM {repo}')

    def LN(self): self.write('')

    def WORKDIR(self, dst='/'): self.write(f'WORKDIR {dst}')

    def ENTRYPOINT(self, *args, shell=False):
        if shell:
            self.write(f'ENTRYPOINT {shlex.join(args)}')
        else:
            self.write(f'ENTRYPOINT {json.dumps(args)}')

    def USER(self, user, group=None):
        if group:
            self.write(f'USER {user}:{group}')
        else:
            self.write(f'USER {user}')

class Image:
    def __init__(self, url, file=None):
        self.url = url
        self.file = file

    def run(self, name=None, rm=False,):
        sh(
            'docker','run',
            ['--name',name] if name else None,
            '--rm' if rm else None,
            self.url,
        )
