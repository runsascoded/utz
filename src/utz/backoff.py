
from datetime import datetime as dt
from sys import stderr
import time
from typing import Union


def backoff(
    fn,
    init=1, step=2, reps=5, max=None,
    out=stderr,
    now=False,
    msg=None,
    fmt='%.1f',
    pred=bool,
    exc: Union[bool, Exception] = False,
):
    attempts = 0
    n = 0
    sleep = init
    start = dt.now()
    if exc:
        if exc is True:
            exc = Exception
        else:
            assert issubclass(exc, Exception)
        def check():
            try:
                return True, fn()
            except exc as e:
                return False, e
    elif callable(pred):
        def check():
            v = fn()
            return pred(v), v
    else:
        def check():
            v = fn()
            return v == pred, v
    while True:
        if now:
            now = False
        else:
            if not n:
                if attempts: out.write('\n')
                out.write(('Sleeping %ss: ' % fmt) % sleep)
                out.flush()
            time.sleep(sleep)
            out.write('.')
            out.flush()
        done, v = check()
        if done:
            return v
        n += 1
        attempts += 1
        if n == reps:
            n = 0
            sleep *= step
            if max and sleep > max:
                raise TimeoutError(msg or ('Failed after %d attempts / %ss' % (attempts, int((dt.now() - start).total_seconds()))))
