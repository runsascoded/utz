
from contextlib import contextmanager
from ctypes import pythonapi, py_object, c_int
from inspect import stack
from sys import stderr

from .methods import Methods


@contextmanager
def use(o, local_conflict='ignore', **kwargs):
    stk = stack()
    frame_info = stk[2]
    frame = frame_info.frame
    glbls = frame.f_globals
    restore = {}
    if type(o) is dict:
        if kwargs:
            raise ValueError(f'kwargs not supported when passing dict object: {",".join(kwargs.keys())}')
        for k,v in o.items():
            if k in glbls:
                restore[k] = True, glbls[k]
            else:
                restore[k] = False, None
            if local_conflict != 'ignore':
                if k in frame.f_locals:
                    # TODO: can this be refined to distinguish function vs class vs module scope?
                    # locals can be reliably updated in module scope, afaict.
                    msg = f'var {k} found in local scope; setting global may not take effect'
                    if local_conflict == 'warn':
                        stderr.write('%s\n' % msg)
                    elif local_conflict in ['raise','err','error']:
                        raise RuntimeError(msg)
                    else:
                        raise ValueError(f'Unrecognized `local_conflict` value: {local_conflict}')
            glbls[k] = v
    else:
        # Parse kwargs
        if 'include' in kwargs:
            ivars = False
            methods = False
            cmethods = False
            smethods = False
            smembers = False
            properties = False
            cached_properties = False
            include = kwargs['include'].split(',')
            for k in include:
                if k == 'ivars': ivars = True
                if k == 'methods': methods = True
                if k == 'cmethods': cmethods = True
                if k == 'smethods': smethods = True
                if k == 'smembers': smembers = True
                if k == 'properties': properties = True
                if k == 'cached_properties': cached_properties = True
        else:
            ivars = True
            methods = True
            cmethods = True
            smethods = True
            smembers = True
            properties = True
            cached_properties = True
            if 'exclude' in kwargs:
                exclude = kwargs['exclude'].split(',')
                for k in exclude:
                    if k == 'ivars': ivars = False
                    if k == 'methods': methods = False
                    if k == 'cmethods': cmethods = False
                    if k == 'smethods': smethods = False
                    if k == 'smembers': smembers = False
                    if k == 'properties': properties = False
                    if k == 'cached_properties': cached_properties = False
            else:
                for k,v in kwargs.items():
                    if k == 'ivars': ivars = bool(v)
                    if k == 'methods': methods = bool(v)
                    if k == 'cmethods': cmethods = bool(v)
                    if k == 'smethods': smethods = bool(v)
                    if k == 'smembers': smembers = bool(v)
                    if k == 'properties':
                        if v == 'all':
                            pass
                        elif v == 'cached':
                            properties = False
                        elif v in ['none','no']:
                            properties = False
                            cached_properties = False
                        else:
                            raise ValueError(f'Unexpcted "properties" value: {properties}; choices: [all,cached,none/no]')

        m = Methods(o)

        assign = set()
        if ivars: assign.update(m.ivars)
        if  methods: assign.update(m. methods)
        if cmethods: assign.update(m.cmethods)
        if smethods: assign.update(m.smethods)
        if smembers: assign.update(m.smembers)
        if cached_properties: assign.update(m.cached_properties)
        if properties: assign.update(m.properties)

        for k in assign:
            if k in glbls:
                restore[k] = True, glbls[k]
            else:
                restore[k] = False, None
            glbls[k] = getattr(o, k)

    pythonapi.PyFrame_LocalsToFast(py_object(frame), c_int(1))
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
        pythonapi.PyFrame_LocalsToFast(py_object(frame), c_int(1))
        del frame


