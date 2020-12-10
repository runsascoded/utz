import subprocess
import time
from contextlib import AbstractContextManager
from subprocess import CalledProcessError, PIPE, Popen

from utz.process import check


class Tunnel(AbstractContextManager):
    def __init__(
        self,
        proxy,
        src_port,
        dst='localhost',
        dst_port=None,
        src_host='localhost',
        sleep=1,
        timeout=1,
    ):
        src_port = str(src_port)
        dst_host = dst
        if not dst_port:
            dst_port = src_port
        dst_port = str(dst_port)

        self.proxy = proxy

        self.src_host = src_host
        self.src_port = src_port

        self.dst_host = dst_host
        self.dst_port = dst_port

        self.sleep = sleep
        self.timeout = timeout

    @property
    def src(self): return f'{self.src_host}:{self.src_port}'

    @property
    def dst(self): return f'{self.dst_host}:{self.dst_port}'

    def start(self):
        return self.__enter__()

    def __enter__(self):
        self.proc = Popen(['ssh','-N','-L',f'{self.src}:{self.dst}',self.proxy])
        try:
            if self.sleep is not None:
                # Give SSH some time to connect before attempting to connect over it:
                time.sleep(self.sleep)

                if not check('which','telnet'):
                    raise RuntimeError("`telnet` required to test SSH connection")

                # Verify telnet connectivity
                cmd = ['telnet',self.src_host,self.src_port]
                p = subprocess.run(cmd, input=b'\035\n', stderr=PIPE, timeout=self.timeout)
                if p.returncode:
                    raise CalledProcessError(p.returncode, cmd)
        except Exception as e:
            self.proc.kill()
            raise e

    def __exit__(self, exc_type, exc_val, exc_tb): self.proc.kill()
    def stop(self): self.__exit__(None, None, None)
    def close(self): self.__exit__(None, None, None)
