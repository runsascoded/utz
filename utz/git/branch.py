from subprocess import CalledProcessError

from ..proc import *
from . import diff


def mv(old, new, untracked=False, checkout=False):
    if current() == old:
        if diff.exists(untracked=untracked):
            raise ValueError(f"Local changes found; refusing to reset --hard")
        else:
            run('git','reset','--hard',new)
    else:
        run('git','branch','-f',old,new)

    if checkout:
        run('git','checkout',new)

def ls():
    return lines('git','for-each-ref','--format=%(refname:short)','refs/heads')
        
def exists(name):
    return check('git','show-ref','--verify','--quiet',f'refs/heads/{name}')

def current(sha_ok=False):
    if sha_ok:
        try:
            return line('git','symbolic-ref','-q','--short','HEAD')
        except CalledProcessError:
            return line('git','log','--no-walk','--format=%h')
    elif sha_ok is None:
        return line('git','symbolic-ref','-q','--short','HEAD', err_ok=True)
    else:
        return line('git','symbolic-ref','-q','--short','HEAD')

