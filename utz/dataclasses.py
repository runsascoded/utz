import typing
from dataclasses import fields


def from_dict(cls, d):
    """See https://stackoverflow.com/a/54769644/544236."""
    try:
        fieldtypes = {f.name: f.type for f in fields(cls)}
        kwargs = {}
        for k, v in d.items():
            fieldtype = fieldtypes[k]
            if typing.get_origin(fieldtype) is list:
                [elem_cls] = typing.get_args(fieldtype)
                if type(v) is not list:
                    raise ValueError(f"Non-list class: {v} ({type(v)})")
                kwargs[k] = [
                    from_dict(elem_cls, _v)
                    for _v in v
                ]
            else:
                kwargs[k] = from_dict(fieldtype, v)
        return cls(**kwargs)
    except TypeError as e:
        return d  # Not a dataclass field
