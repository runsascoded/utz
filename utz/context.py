#!/usr/bin/env python

# # Context Manager utilities

# General/Common imports:

from contextlib import AbstractContextManager, contextmanager, suppress


# ## `nullcontext`
# Define `nullcontext` in a cross-version way:
try:
    # Python ≥3.7
    from contextlib import nullcontext
except ImportError:
    # Python <3.7
    class nullcontext(object):
        def __enter__(self): pass
        def __exit__(self, *args): pass


# Verify it works:
with nullcontext(): pass


# ## `catch`: context manager for catching+verifying `Exception`s
class catch(AbstractContextManager):
    def __init__(self, *excs):
        self.excs = excs

    def __exit__(self, exc_type, exc_value, traceback):
        if not exc_type:
            if len(self.excs) == 1:
                raise AssertionError(f'No {self.excs[0].__name__} was thrown')
            else:
                raise AssertionError(f'None of {",".join([e.__name__ for e in self.excs])} were thrown')
        
        if not [ isinstance(exc_value, exc) for exc in self.excs ]:
            raise exc_value

        return True


# ## `no`: context manager for verifying `NameError`s (undefined variable names)
no = catch(NameError)


def run_then_raise(fns, vals=None):
    """Run multiple functions, catching all Exceptions and raise-chaining them at the end"""
    if not fns: return vals
    if not vals: vals = []
    (fn, *fns) = fns
    try:
        vals.append(fn())
    except Exception as e:
        run_then_raise(fns, vals=vals)
        raise e
    else:
        return run_then_raise(fns, vals=vals)


def bind_exit(ctx): return lambda: ctx.__exit__(None, None, None)


@contextmanager
def ctxs(ctxs):
    vals = []
    try:
        for ctx in ctxs:
            val = ctx.__enter__()
            vals.append(val)
        yield vals
    except Exception as e:
        run_then_raise(
            reversed([
                bind_exit(ctx)
                for ctx in ctxs[:len(vals)]  # truncate to just the ctxs that were successfully entered
            ])
        )
        raise e
    else:
        fns = [ bind_exit(ctx) for ctx in reversed(ctxs) ]
        run_then_raise(fns)


def contexts(ctxs):
    @contextmanager
    def fn(ctxs):
        if not ctxs:
            yield
        else:
            [ ctx, *rest ] = ctxs
            with ctx as v, fn(rest) as vs:
                yield [ v, *vs ]
    return fn(ctxs)
