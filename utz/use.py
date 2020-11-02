
from contextlib import contextmanager
from ctypes import pythonapi, py_object, c_int
from functools import cached_property
from inspect import getmembers, stack

@contextmanager
def use(o, ivars=True, methods=True, properties='all'):
    stk = stack()
    frame_info = stk[2]
    frame = frame_info.frame
    glbls = frame.f_globals
    restore = {}
    if type(o) is dict:
        for k,v in o.items():
            if k in glbls:
                restore[k] = True, glbls[k]
            else:
                restore[k] = False, None
            glbls[k] = v
    else:
        cls = { k:v for k,v in getmembers(type(o)) if not k.startswith('_') }
        props = { k:v for k,v in cls.items() if isinstance(v, property) }
        cached_props = { k:v for k,v in cls.items() if isinstance(v, cached_property) }
        keys = set(k for k in dir(o) if not k.startswith('_'))
        _ivars = keys.difference(cls.keys())
        imethods = set(cls.keys()).difference(props.keys()).difference(cached_props.keys()).intersection(keys)
        cmethods = { k:v for k,v in cls.items() if isinstance(v, classmethod) }
        # obj = { k:v for k,v in getmembers(o) if not k.startswith('_') }
        # methods = cls.keys()
        # ivars = set(obj.keys()).difference(methods)

        assign = _ivars if ivars else set()
        if methods:
            assign.update(imethods)
        if properties == 'cached':
            assign.update(cached_props.keys())
        elif properties == 'all':
            assign.update(cached_props.keys())
            assign.update(props.keys())
        elif properties not in ['none','no']:
            raise ValueError(f'Unexpcted "properties" value: {properties}; choices: [all,cached,none/no]')

        for k in assign:
            if k in glbls:
                restore[k] = True, glbls[k]
            else:
                restore[k] = False, None
            glbls[k] = getattr(o, k)

    pythonapi.PyFrame_LocalsToFast(py_object(frame), c_int(0))
    del frame
    yield
    if restore:
        frame = frame_info.frame
        glbls = frame.f_globals
        for k, (existed, v) in restore.items():
            if existed:
                glbls[k] = v
            else:
                del glbls[k]
        pythonapi.PyFrame_LocalsToFast(py_object(frame), c_int(0))
        del frame


