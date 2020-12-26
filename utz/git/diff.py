from ..process import *


def exists(untracked=True, unstaged=True):
    lns = lines('git','status','--porcelain')
    if not untracked:
        lns = [ ln for ln in lns if not ln.startswith('??') ]
    if not unstaged:
        lns = [ ln for ln in lns if not ln.startswith(' ') ]
    return bool(lns)

