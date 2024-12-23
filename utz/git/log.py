
from ..proc import line, output


def msg(ref=None):
    return output('git','log','-n1','--format=%B',ref).decode().strip()


def fmt(*refs: str, fmt: str = '%h', **kwargs) -> str:
    return line('git', 'log', '-1', f'--format={fmt}', *refs, **kwargs)


def sha(ref: str, **kwargs) -> str:
    return fmt(ref, fmt='%H', **kwargs)


def short_sha(ref: str, **kwargs) -> str:
    return fmt(ref, fmt='%h', **kwargs)
