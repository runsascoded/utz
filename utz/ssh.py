from contextlib import AbstractContextManager, contextmanager
from ctypes import py_object, pythonapi
import subprocess
from subprocess import check_call, CalledProcessError, PIPE
import threading
from threading import Thread
import time

from .process import check, run


class CtxThread(AbstractContextManager, Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        Thread.__init__(self, group=group, target=target, name=name, args=args, kwargs=kwargs)
        AbstractContextManager.__init__(self)

    def __enter__(self):
        print('starting thread')
        self.start()
        print('started thread')

    def get_id(self):
        # returns id of the respective thread 
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f'exiting thread: {exc_type}, {exc_val}, {exc_tb}')
        thread_id = self.get_id()
        print(f'thread_id: {thread_id}')
        res = pythonapi.PyThreadState_SetAsyncExc(thread_id, py_object(SystemExit))
        if res > 1:
            pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')

    def stop(self):
        self.__exit__(None, None, None)


@contextmanager
def tunnel(
    proxy,
    src_port,
    dst='localhost',
    dst_port=None,
    src_host='localhost',
    sleep=1,
    timeout=1,
):
    ''''''

    src = f'{src_host}:{src_port}'
    src_port = str(src_port)
    dst_host = dst
    if not dst_port:
        dst_port = src_port
    dst_port = str(dst_port)
    dst = f'{dst_host}:{dst_port}'

    def ssh_tunnel(src, dst, proxy):
        run('ssh','-N','-L',f'{src}:{dst}',proxy)

    with CtxThread(target=ssh_tunnel, args=(src, dst, proxy)):
        print('entered ctxthread')
        if sleep is not None:
            # Give SSH some time to connect before attempting to connect over it:
            time.sleep(sleep)

            if not check('which','telnet'):
                raise RuntimeError("`telnet` required to test SSH connection")

            # Verify telnet connectivity
            cmd = ['telnet',src_host,src_port]
            p = subprocess.run(cmd, input=b'\035\n', stderr=PIPE, timeout=timeout)
            if p.returncode:
                raise CalledProcessError(p.returncode, cmd)
        yield
