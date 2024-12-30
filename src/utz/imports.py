# Helper for optional imports:
from contextlib import suppress


_try = suppress(ImportError, ModuleNotFoundError, NameError)
