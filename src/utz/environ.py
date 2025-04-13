from __future__ import annotations

import os
import enum
import warnings
from collections.abc import MutableMapping
from contextlib import contextmanager
from typing import Any, Iterator, overload


class OnConflict(enum.Enum):
    """How to handle variables that were changed during the context."""
    ERROR = "error"
    WARN = "warn"
    IGNORE = "ignore"


class OnExit(enum.Enum):
    """What to do with conflicted variables on context exit."""
    RESET = "reset"  # Reset conflicted vars to original value if it existed, otherwise remove
    SKIP = "skip"   # Leave conflicted values in place


class EnvPatchConflict(Exception):
    """Raised when environment variables were modified during the context."""
    def __init__(self, conflicts: dict[str, tuple[str, str]]):
        self.conflicts = conflicts
        items = [f"{k}: expected={v[0]!r}, found={v[1]!r}"
                 for k, v in conflicts.items()]
        super().__init__(
            "Environment variables were modified during the context:\n  " +
            "\n  ".join(items)
        )


class Env(MutableMapping):
    """
    A singleton wrapper around os.environ that provides dictionary-like access to environment
    variables and supports temporarily modifying values using a context manager.

    Usage:
        # Dictionary-like access
        env["MY_VAR"] = "value1"
        print(env["MY_VAR"])
        print(env.get("NON_EXISTENT", "default"))

        # Context manager usage with conflict handling
        with env({"MY_VAR": "temporary"},
                on_conflict=OnConflict.ERROR,
                on_exit=OnExit.RESET):
            print(env["MY_VAR"])  # temporary

        # Or with kwargs syntax
        with env(MY_VAR="temporary",
                _on_conflict=OnConflict.WARN,
                _on_exit=OnExit.SKIP):
            print(env["MY_VAR"])  # temporary
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Inherit all methods/attributes from os.environ that we haven't overridden
        self.__dict__.update(os.environ.__dict__)

    def __getitem__(self, key: str) -> str:
        return os.environ[key]

    def __setitem__(self, key: str, value: str) -> None:
        os.environ[key] = str(value)

    def __delitem__(self, key: str) -> None:
        del os.environ[key]

    def __iter__(self) -> Iterator[str]:
        return iter(os.environ)

    def __len__(self) -> int:
        return len(os.environ)

    @contextmanager
    def _patch(
        self,
        updates: dict[str, str],
        on_conflict: OnConflict = OnConflict.ERROR,
        on_exit: OnExit = OnExit.RESET,
    ):
        """Internal method for handling environment variable patching."""
        # Convert all values to strings and store originals
        updates = {k: str(v) for k, v in updates.items()}
        original_values = {
            k: os.environ.get(k) for k in updates
        }

        # Apply updates
        os.environ.update(updates)

        try:
            yield self
        finally:
            # Check for modifications during context
            conflicts = {}
            for key, expected in updates.items():
                current = os.environ.get(key)
                if current != expected:
                    conflicts[key] = (expected, current)

            # Always reset unmodified variables
            unmodified = set(updates) - set(conflicts)
            for key in unmodified:
                orig = original_values[key]
                if orig is None:
                    if key in os.environ:
                        del os.environ[key]
                else:
                    os.environ[key] = orig

            # Handle conflicted variables based on on_exit policy
            if conflicts and on_exit == OnExit.RESET:
                for key in conflicts:
                    orig = original_values[key]
                    if orig is None:
                        if key in os.environ:
                            del os.environ[key]
                    else:
                        os.environ[key] = orig

            if conflicts:
                if on_conflict == OnConflict.ERROR:
                    raise EnvPatchConflict(conflicts)
                elif on_conflict == OnConflict.WARN:
                    warnings.warn(
                        f"Environment variables were modified during the context: {conflicts}",
                        RuntimeWarning
                    )

    @overload
    def __call__(
        self,
        updates: dict[str, str],
        *,
        on_conflict: OnConflict = OnConflict.ERROR,
        on_exit: OnExit = OnExit.RESET,
    ) -> Any: ...

    @overload
    def __call__(
        self,
        **kwargs: str | OnConflict | OnExit,
    ) -> Any: ...

    def __call__(
        self,
        updates: dict[str, str] | None = None,
        *,
        on_conflict: OnConflict = OnConflict.ERROR,
        on_exit: OnExit = OnExit.RESET,
        **kwargs,
    ) -> Any:
        """
        Support both dict and kwargs syntax for the context manager:
        with env({"KEY": "value"}) and with env(KEY="value")

        Special kwargs when using kwargs syntax:
            _on_conflict: OnConflict = OnConflict.ERROR
            _on_exit: OnExit = OnExit.RESET
        """
        if updates is not None and kwargs:
            raise ValueError("Cannot specify both dictionary and keyword arguments")

        if updates is not None:
            return self._patch(updates, on_conflict=on_conflict, on_exit=on_exit)

        # Extract special kwargs
        _on_conflict = kwargs.pop('_on_conflict', on_conflict)
        _on_exit = kwargs.pop('_on_exit', on_exit)

        return self._patch(kwargs, on_conflict=_on_conflict, on_exit=_on_exit)


# Create singleton instance
env = Env()
