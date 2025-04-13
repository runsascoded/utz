from __future__ import annotations

from dataclasses import dataclass

from typing import Callable, Sequence, TypeVar

T = TypeVar("T")


class Unset:
    def __bool__(self):
        return False


@dataclass
class DefaultDict(dict[str, T]):
    """`defaultdict` replacement where `in` reflects the presence of a fallback/default value.

    Can be initialized from a list[str], where each element is either a `k=v` pair or a fallback value (with no `=`).
    """

    configs: dict[str, T]
    default: T = Unset

    @staticmethod
    def parse_configs(
        configs: Sequence[str],
        name2value: Callable[[str], T] | None = None,
        fallback: T | None = Unset,
    ) -> (T, dict[str, T]):
        default = fallback
        default_set = False
        kwargs: dict[str, T] = {}
        for write_config in configs:
            kv = write_config.split("=", 1)
            if len(kv) == 2:
                k, name = kv
                value = name2value(name) if name2value else name
                kwargs[k] = value
            elif len(kv) == 1:
                [name] = kv
                if default_set:
                    raise ValueError(f"Multiple defaults found: {default}, {name}")
                default = name2value(name) if name2value else name
                default_set = True
            else:
                raise ValueError(f"Unrecognized defaultdict config arg: {kv}")
        return default, kwargs

    @staticmethod
    def load(
        args: Sequence[str],
        name2value: Callable | None = None,
        fallback: T | None = None,
    ) -> "DefaultDict":
        default, kwargs = DefaultDict.parse_configs(
            args, name2value=name2value, fallback=fallback
        )
        return DefaultDict(configs=kwargs, default=default)

    def get_first(self, keys, fallback=None):
        for key in keys:
            if key in self.configs:
                return self.configs[key]
        if self.default is not Unset:
            return self.default
        return fallback

    def __contains__(self, item):
        return item in self.configs or self.default is not Unset

    def __getitem__(self, item) -> T:
        if item not in self.configs and self.default is not Unset:
            return self.default
        else:
            return self.configs[item]

    def __bool__(self):
        return bool(self.configs) or self.default is not Unset
