from contextlib import contextmanager
from ..process import run
from . import branch as _branch

class Checkout:
    def __call__(checkout, branch, ref=None, create_ok=False, ctx=True, sha_ok=True):
        prev = _branch.current(sha_ok=sha_ok)
        exists = _branch.exists(branch)
        if not exists and not create_ok:
            raise ValueError(f"Branch {branch} doesn't exist")
        if exists and not ref:
            run('git','checkout',branch)
        else:
            run('git','checkout','-B',branch,ref)
        
        if ctx:
            @contextmanager
            def ret():
                try:
                    yield prev
                finally:
                    checkout(prev, ctx=False)
            
            return ret()
        else:
            return prev
    
    def mk(checkout, branch, ref=None, **kwargs):
        return checkout(branch, ref=ref, create_ok=True, **kwargs)

