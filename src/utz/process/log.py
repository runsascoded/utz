from typing import Callable, Optional

Log = Optional[Callable[..., None]]


def silent(*_args) -> None:
    pass
