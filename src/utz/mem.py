from __future__ import annotations

from asyncio import gather, set_event_loop
from os import getcwd, remove, makedirs
from os.path import splitext, exists, dirname

import asyncio
import json
import memray
from contextlib import AbstractContextManager, AbstractAsyncContextManager
from subprocess import DEVNULL
from tempfile import NamedTemporaryFile
from types import TracebackType
from typing import Literal, Self

from utz import err
from utz.aio import proc
from utz.process.log import Log, silent


Verbosity = Literal[0, 1, 2]


class Tracker(AbstractContextManager, AbstractAsyncContextManager):
    def __init__(
        self,
        path: str | None = None,
        keep: bool | None = None,
        native_traces: bool = True,
        follow_fork: bool = True,
        log: Log | bool | Verbosity = None,
        stats: bool = True,
        flamegraph: bool = True,
        **kwargs,
    ):
        if not stats and not flamegraph and not keep:
            raise ValueError("At least one of {stats, flamegraph, keep} should be True")
        self.path = path
        self.keep = keep
        self.verbose = 1
        if log is True:
            log = err
        elif isinstance(log, int) and log > 0:
            self.verbose = log
            log = err
        elif not log:
            log = silent
            self.verbose = 0
        self.log = log
        self.tmpfile = False
        self.kwargs = dict(
            native_traces=native_traces,
            follow_fork=follow_fork,
            **kwargs,
        )
        self.peak_mem = None
        self.stats = None
        self.compute_stats = stats
        self.compute_flamegraph = flamegraph
        self.tracker = None

    def __enter__(self) -> Self:
        self.peak_mem = self.stats = None
        assert not self.tracker, f"Attempted to `__enter__` MemTracker before `__exit__`ing"
        path = self.path
        if path is None:
            path = self.path = NamedTemporaryFile(dir=getcwd(), suffix=".memray").name
            self.tmpfile = True
        elif exists(path):
            self.log(f"mem.Tracker removing {path}")
            remove(path)

        makedirs(dirname(path), exist_ok=True)
        self.log(f"memray logging to {path}")
        self.tracker = memray.Tracker(path, **self.kwargs)
        self.tracker.__enter__()
        return self

    async def __aenter__(self) -> Self:
        return self.__enter__()

    @property
    def stats_path(self) -> str | None:
        path = self.path
        if path is None:
            return path
        else:
            return f'{splitext(self.path)[0]}.stats.json'

    @property
    def flamegraph_path(self) -> str | None:
        path = self.path
        if path is None:
            return path
        else:
            return f'{splitext(self.path)[0]}.html'

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        self.tracker.__exit__(exc_type, exc_value, exc_tb)
        self.tracker = None
        rm = self.keep is False or (self.keep is None and self.tmpfile)
        coros = []
        if self.compute_stats:
            stats_path = self.stats_path
            if not exc_value:
                coros.append(
                    proc.run(
                        'memray', 'stats', '--json', '-fo', stats_path, self.path,
                        log=self.log,
                        **(dict() if self.verbose > 1 else dict(stdout=DEVNULL)),
                    )
                )
        if self.compute_flamegraph:
            flamegraph_path = self.flamegraph_path
            if not exc_value:
                coros.append(
                    proc.run(
                        'memray', 'flamegraph', '-fo', flamegraph_path, self.path,
                        log=self.log,
                        **(dict() if self.verbose > 1 else dict(stdout=DEVNULL)),
                    )
                )

        await gather(*coros)
        if rm:
            remove(self.path)
            self.path = None
        if exc_value:
            raise exc_value
        with open(stats_path, 'r') as f:
            stats = json.load(f)
        if rm:
            remove(stats_path)
        self.stats = stats
        self.peak_mem = stats['metadata']['peak_memory']

        pass

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        coro = self.__aexit__(exc_type, exc_value, exc_tb)
        try:
            # If we're already in an event loop
            loop = asyncio.get_running_loop()
            loop.run_until_complete(coro)
        except RuntimeError:
            # If no event loop is running, create one
            loop = asyncio.new_event_loop()
            set_event_loop(loop)
            try:
                loop.run_until_complete(coro)
            finally:
                loop.close()
