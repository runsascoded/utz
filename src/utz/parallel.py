from os import cpu_count
from typing import Callable


def parallel(elems, fn: Callable, n_jobs: int = 0):
    if n_jobs == 1:
        return [ fn(elem) for elem in elems ]
    try:
        from joblib import Parallel, delayed
        if not n_jobs:
            n_jobs = cpu_count()
        p = Parallel(n_jobs=n_jobs)
        return p(delayed(fn)(elem) for elem in elems)
    except ImportError:
        return [ fn(elem) for elem in elems ]
