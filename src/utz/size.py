from __future__ import annotations

def iec(
    value: float | str,
    binary: bool = True,
    gnu: bool = False,
    format: str = "%.3g",
) -> str:
    from humanize import naturalsize
    return naturalsize(
        value=value,
        binary=binary,
        gnu=gnu,
        format=format,
    )
