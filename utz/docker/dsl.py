
from .file import File


def _method(name):
    def impl(*args, **kwargs):
        file = File._file
        if not file:
            raise RuntimeError('No active Dockerfile')
        getattr(file,name)(*args,**kwargs)

    return impl

COPY = _method('COPY')
NOTE = _method('NOTE')
ENV = _method('ENV')
LABEL = _method('LABEL')
FROM = _method('FROM')
LN = _method('LN')
WORKDIR = _method('WORKDIR')
ENTRYPOINT = _method('ENTRYPOINT')
USER = _method('USER')
