
from ..process import output


def msg(ref=None):
    return output('git','log','-n1','--format=%B',ref).decode().strip()
