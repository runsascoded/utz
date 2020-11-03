
from os.path import join
from os import remove
from tempfile import NamedTemporaryFile

from .process import run, sh

class File:
    def __init__(self, path=None, tag=None, ctx=None, dir=None, rm=None, copy_dir=None):
        if path:
            self.rm = bool(rm)
        else:
            path = NamedTemporaryFile(prefix='Dockerfile.', dir=dir).name
            self.rm = rm != False
        self.path = path
        self.fd = None
        self.tag = tag
        self.ctx = ctx
        self.copy_dir = copy_dir

    def write(self, *lines):
        if not self.fd:
            self.fd = open(self.path,'w')
        for line in lines:
            self.fd.write('%s\n' % line)

    def build(self, tag=None, ctx=None, **build_args):
        if self.fd:
            self.fd.close()
            self.fd = None

        tag = tag or self.tag
        ctx = ctx or self.ctx or '.'
        if not tag:
            raise ValueError(f'Missing tag for image build')

        run(
            'docker','build',
            '-f',self.path,
            '-t',tag,
            [ ['--build-arg',f'{k}={v}'] for k,v in build_args.items() ],
            ctx
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

    def NOTE(self, *lines):
        self.write(*[f'# {line}' for line in lines])

    def RUN(self, *cmds):
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

    def WORKDIR(self, dst='/'):
        self.write(f'WORKDIR {dst}')

    def ENTRYPOINT(self, arg):
        self.write('ENTRYPOINT %s' % str(arg))


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
