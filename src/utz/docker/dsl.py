
from .file import File


def _method(name):
    def impl(*args, **kwargs):
        file = File._file
        if not file:
            raise RuntimeError('No active Dockerfile')
        getattr(file, name)(*args, **kwargs)

    return impl

ARG = _method('ARG')
COPY = _method('COPY')
ENTRYPOINT = _method('ENTRYPOINT')
ENV = _method('ENV')
FROM = _method('FROM')
LABEL = _method('LABEL')
LN = _method('LN')
LINE = LN
NOTE = _method('NOTE')
RUN = _method('RUN')
WORKDIR = _method('WORKDIR')
USER = _method('USER')
