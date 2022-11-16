from contextlib import AbstractContextManager
import json
from os.path import exists, join
from os import getcwd, remove
import shlex
from tempfile import NamedTemporaryFile
from types import TracebackType
from typing import Optional, Type

from ..context import nullcontext
from ..process import sh

from .image import Image
from .util import escape


class File(AbstractContextManager):
    _file = None

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
            self.rm = rm != False

        self.path = path
        self.fd = None
        self.tag = tag
        self.dir = dir
        self.copy_dir = copy_dir

        if extend:
            with open(extend, 'r') as f:
                self.lines = [line.rstrip('\n') for line in f.readlines()]
        else:
            self.lines = []

    def __enter__(self):
        if File._file:
            raise RuntimeError(f"Can't enter {self}, already entered {File._file}")
        File._file = self
        return self

    def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_value: Optional[BaseException],
            traceback: Optional[TracebackType]
    ):
        File._file = None
        if self.tag:
            self.build(self.tag)
        if self.path and exists(self.path) and self.rm:
            remove(self.path)

    def write(self, *lines):
        self.lines += lines

    def build(self, tag=None, dir=None, **build_args):
        tag = tag or self.tag
        if not tag:
            raise ValueError(f'Missing tag for image build')

        dir = dir or self.dir or '.'
        rm = self.rm
        path = self.path
        mode = 'w'

        if path:
            ctx = nullcontext()
            if exists(path):
                mode = 'a'
        else:
            ctx = NamedTemporaryFile(prefix='Dockerfile.', dir=dir, delete=rm)
            rm = False
            path = ctx.name

        with ctx:
            with open(path, mode) as fd:
                fd.writelines('%s\n' % l for l in self.lines)

            sh(
                'docker', 'build',
                '-f', path,
                '-t', tag,
                [['--build-arg', f'{k}={v}'] for k, v in build_args.items()],
                dir
            )

            if rm:
                remove(path)

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
            srcs = [join(dir, src) for src in srcs]
        self.write(f'COPY {" ".join([*srcs, dst])}')

    def kvs(self, cmd, *args, **kwargs):
        flattened = []
        for arg in args:
            if isinstance(arg, str):
                flattened.append(arg)
            elif isinstance(arg, tuple):
                if len(arg) != 2:
                    raise RuntimeError(f'Invalid tuple arg (required len 2): %s' % str(arg))
                k, v = arg
                k = escape(str(k))
                v = escape(str(v))
                flattened.append(f'"{k}"="{v}"')
            elif isinstance(arg, dict):
                for k, v in arg.items():
                    flattened.append(f'"{escape(k)}"="{escape(v)}"')
            else:
                raise ValueError(f'Unrecognized argument to {cmd}: {arg}')
        for k, v in kwargs.items():
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

    def LN(self):
        self.write('')

    def WORKDIR(self, dst='/'):
        self.write(f'WORKDIR {dst}')

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
