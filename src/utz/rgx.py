from __future__ import annotations

import re

from typing import Sequence

from re import Pattern

from abc import ABC


class Patterns(ABC):
    def __init__(
        self,
        pats: Sequence[str | Pattern] | None,
        flags: int = 0,
        *,
        search: bool = True,
    ):
        self.pats = None if pats is None else [
            re.compile(pat, flags=flags) if isinstance(pat, str) else
            re.compile(pat.pattern, flags=flags) if flags else
            pat
            for pat in pats
        ]
        self.search = search

    def __bool__(self) -> bool:
        return self.pats is not None

    def __call__(self, val: str) -> bool:
        pats = self.pats
        if not self:
            # `pats is None` ⟹ everything passes this filter
            return True
        else:
            return any(pat.search(val) if self.search else pat.fullmatch(val) for pat in pats)


class Includes(Patterns):
    pass


class Excludes(Patterns):
    def __call__(self, val: str) -> bool:
        if not self:
            return True
        else:
            return not super().__call__(val)
