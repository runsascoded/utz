#!/usr/bin/env python

from collections.abc import MutableMapping


def rev(arg: dict) -> dict:
    return { v: k for k, v in arg.items() }


def merge(*args, **kwargs):
    if args:
        (obj, *args) = args
        obj = dict(obj)
    else:
        obj = dict()
    for arg in args:
        obj.update(**arg)
    for k,v in kwargs.items():
        obj[k] = v
    return o(obj)


class o(MutableMapping, dict):
    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            raise ValueError(f'≤1 positional args required, got {len(args)}')
        
        if args:
            (data,) = args
            if type(data) is not dict:
                raise ValueError(f'Single-arg o() ctor call needs dict arg, not {type(data)}: {data}')
            if kwargs:
                raise ValueError(f'Positional dict arg is exclusive with kwargs: {data}, {kwargs}')
        else:
            data = kwargs

        K = '_data'
        if K in data:
            raise ValueError(f"Reserved key '{K}' found in 'data' dict: {data}")

        super().__init__(**data)

        for k, v in data.items():
            if type(v) is dict and not isinstance(v, o): v = o(v)
            super(o, self).__setattr__(k, v)

        super(o, self).__setattr__(K, data)

    def merge(self, *args, **kwargs):
        return merge(self, *args, **kwargs)

    def update(self, *args, **kwargs):
        for arg in args:
            self.update(**arg)
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __items__(self):
        for k, v in self._data.items():
            yield k, v

    def __setattr__(self, k, v):
        if isinstance(v, dict) and not isinstance(v, o): v = o(v)
        self._data[k] = v

    def __getattr__(self, k):
        try:
            v = self._data[k]
            if isinstance(v, dict) and not isinstance(v, o): v = o(v)
            return v
        except KeyError:
            raise AttributeError(f'Key {k}')

    def __len__(self):
        return len(self._data)

    def __delitem__(self, k):
        del self._data[k]

    def get(self, k, default=None):
        if k in self:
            return self[k]
        else:
            return default

    def __call__(self, *keys, default=None):
        obj = self
        keys = list(keys)
        while keys:
            key = keys.pop(0)
            if key in obj:
                obj = obj[key]
            else:
                return default

        return obj

    def __getitem__(self, k):
        v = self._data[k]
        if type(v) is dict:
            v = o(v)
        return v

    def __setitem__(self, k, v):
        self._data[k] = v

    def __contains__(self, k):
        return k in self._data
    
    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return repr(self._data)

    def __iter__(self):
        return iter(self._data)

    def items(self):
        return self._data.items()

    def __eq__(self, r):
        if isinstance(r, o):
            return self._data == r._data
        if isinstance(r, dict):
            return self._data == r
        return NotImplemented

    def __ne__(self, r):
        if isinstance(r, o):
            return self._data != r._data
        if isinstance(r, dict):
            return self._data != r
        return NotImplemented

    def __hash__(self):
        return hash(self._data)
