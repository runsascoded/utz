# # Context Manager utilities

from __future__ import annotations

from asyncio import gather

from contextlib import AbstractContextManager, contextmanager, asynccontextmanager, AbstractAsyncContextManager, \
    AsyncExitStack
from typing import AsyncContextManager, ContextManager, Generator, Sequence, TypeVar, Iterator, Union

T = TypeVar("T")

# Shorthand for common return type of ``@contextmanager``-decorated functions
Yield = Generator[T, None, None]


def contexts(*ctxs: ContextManager | Sequence[ContextManager] | Iterator) -> ContextManager:
    """Compose context managers."""
    ctxs = [
        ctx
        for _ctxs in ctxs
        for ctx in (
            _ctxs
            if isinstance(_ctxs, Sequence)
            else [_ctxs]
        )
    ]

    @contextmanager
    def fn(ctxs):
        if not ctxs:
            yield
        else:
            [ ctx, *rest ] = ctxs
            with ctx as v, fn(rest) as vs:
                yield [ v, *(vs if vs else []) ]

    return fn(ctxs)


ctxs = contexts


async def aenter_ctx(ctx):
    """Enter an async context manager or adapt a sync one."""
    if hasattr(ctx, '__aenter__'):
        return await ctx.__aenter__()
    elif hasattr(ctx, '__enter__'):
        return ctx.__enter__()
    else:
        raise TypeError(f"Object {ctx} is not a context manager")

async def aexit_ctx(ctx, exc_type, exc_val, exc_tb):
    """Exit an async context manager or adapt a sync one."""
    if hasattr(ctx, '__aexit__'):
        return await ctx.__aexit__(exc_type, exc_val, exc_tb)
    elif hasattr(ctx, '__exit__'):
        return ctx.__exit__(exc_type, exc_val, exc_tb)
    else:
        raise TypeError(f"Object {ctx} is not a context manager")


CtxMgr = Union[ContextManager[T], AsyncContextManager[T]]


def acontexts(*ctxs: CtxMgr | Sequence[CtxMgr] | Iterator) -> AsyncContextManager:
    """Compose context managers, running their __aenter__ and __aexit__ methods concurrently."""
    # Flatten the list of context managers
    flat_ctxs = []
    for _ctxs in ctxs:
        if isinstance(_ctxs, Sequence):
            flat_ctxs.extend(_ctxs)
        else:
            flat_ctxs.append(_ctxs)

    @asynccontextmanager
    async def async_composed():
        exit_stack = []
        exc_details = (None, None, None)
        try:
            # Run all __aenter__ methods concurrently
            values = await gather(*(aenter_ctx(ctx) for ctx in flat_ctxs))
            exit_stack = list(flat_ctxs)  # Track contexts that need to be exited
            yield values
        except BaseException as e:
            # Store exception details for __aexit__ methods
            exc_details = (type(e), e, e.__traceback__)
            raise
        finally:
            # Run all __aexit__ methods concurrently
            if exit_stack:
                exit_results = await gather(
                    *(aexit_ctx(ctx, *exc_details) for ctx in reversed(exit_stack)),
                    return_exceptions=True
                )
                # Re-raise any exceptions from __aexit__ if no other exception is being propagated
                if exc_details[0] is None:
                    for result in exit_results:
                        if isinstance(result, BaseException):
                            raise result

    return async_composed()


actxs = acontexts
asyncnullcontext = AsyncExitStack  # https://stackoverflow.com/a/61488069


class WithExitHook(ContextManager[T], AsyncContextManager[T]):
    def __init__(self, ctx: CtxMgr[T], exit_hook: CtxMgr):
        self.ctx = ctx
        if not isinstance(exit_hook, (AbstractContextManager, AbstractAsyncContextManager)):
            raise ValueError("exit_hook must be an AbstractContextManager or AbstractAsyncContextManager")

        self.exit_hook = exit_hook

    def __enter__(self) -> T:
        return self.ctx.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self.exit_hook:
            return self.ctx.__exit__(exc_type, exc_val, exc_tb)

    def __aenter__(self) -> T:
        return self.ctx.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if isinstance(self.exit_hook, AbstractContextManager):
            with self.exit_hook:
                return await self.ctx.__aexit__(exc_type, exc_val, exc_tb)
        else:
            async with self.exit_hook:
                return await self.ctx.__aexit__(exc_type, exc_val, exc_tb)


with_exit_hook = WithExitHook


class catch(AbstractContextManager):
    """``contextmanager`` that catches+verifies ``Exception``s"""
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
