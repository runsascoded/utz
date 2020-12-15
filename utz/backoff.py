
from datetime import datetime as dt
from sys import stdout
import time

def backoff(fn, init=1, step=2, reps=5, max=None, out=stdout, now=False, msg=None, fmt='%.1f', pred=None, exc=False):
    attempts = 0
    n = 0
    sleep = init
    start = dt.now()
    if exc:
        if exc is True:
            exc = Exception
        else:
            assert isinstance(exc, Exception)
        def check(v):
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
            time.sleep(sleep)
            out.write('.')
        done, v = check()
        if done:
            return v
        n += 1
        attempts += 1
        if n == reps:
            n = 0
            sleep *= step
            if max and sleep >= max:
                raise TimeoutError(msg or ('Failed after %d attempts / %ss' % (attempts, int((dt.now() - start).total_seconds()))))
