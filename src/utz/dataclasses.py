from __future__ import annotations

import dataclasses
from typing import get_args, get_origin, Union, get_type_hints

try:
    from types import UnionType
    UnionTypes = (Union, UnionType)
except ImportError:
    # Python < 3.10
    UnionTypes = (Union,)


def from_dict(cls, v):
    """Parse a dataclass instance from a dictionary.

    Recursively parses instance-vars' types.
    """
    for typ in (int, float, str, bool, type(None)):
        if cls is typ or isinstance(cls, str) and cls == typ.__name__:
            if type(v) is not typ:
                raise ValueError(f"{v} ({type(v).__name__}) is not of expected type {typ.__name__}")
            return v

    if get_origin(cls) is list:
        [elem_cls] = get_args(cls)
        if type(v) is not list:
            raise ValueError(f"Non-list class: {v} ({type(v)})")
        return [
            from_dict(elem_cls, _v)
            for _v in v
        ]
    elif get_origin(cls) is dict:
        if not isinstance(v, dict):
            raise ValueError(f"Expected {cls}, got {v})")
        [key_cls, value_cls] = get_args(cls)
        return {
            from_dict(key_cls, k): from_dict(value_cls, _v)
            for k, _v in v.items()
        }
    elif get_origin(cls) in UnionTypes:
        args = get_args(cls)
        for arg in args:
            try:
                return from_dict(arg, v)
            except (TypeError, ValueError) as e:
                pass
        raise ValueError(f"Invalid value '{v}' (expected one of {[ c.__name__ for c in get_args(cls) ]})")

    try:
        fields = dataclasses.fields(cls)
        try:
            fieldtypes = get_type_hints(cls)
        except TypeError:
            fieldtypes = { f.name: f.type for f in fields }
    except TypeError:
        raise TypeError(f"`fields` must be called with a dataclass type or instance, not {getattr(cls, '__name__', cls)}")

    if not isinstance(v, dict):
        raise ValueError(f"Expected dict (representing a {cls.__name__}), got {v}")

    kwargs = {}
    for k, _v in v.items():
        fieldtype = fieldtypes[k]
        kwargs[k] = from_dict(fieldtype, _v)
    return cls(**kwargs)
