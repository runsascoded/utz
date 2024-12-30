from functools import cached_property
from inspect import isfunction


class Methods:
    def __init__(self, o):
        klz = type(o)
        klzm = klz.__dict__
        self.methods = set()
        self.cmethods = set()
        self.smethods = set()
        self.smembers = set()
        self.properties = set()
        self.cached_properties = set()

        for k,v in klzm.items():
            if k.startswith('_'): continue
            if isfunction(v):
                self.methods.add(k)
            elif isinstance(v, classmethod):
                self.cmethods.add(k)
            elif isinstance(v, staticmethod):
                self.smethods.add(k)
            elif isinstance(v, property):
                self.properties.add(k)
            elif isinstance(v, cached_property):
                self.cached_properties.add(k)
            else:
                self.smembers.add(k)

        self.ivars = set(k for k in dir(o) if not k.startswith('_')).difference(klzm.keys())
