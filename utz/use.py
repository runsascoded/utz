
from contextlib import contextmanager
from ctypes import pythonapi, py_object, c_int
from inspect import stack
from sys import stderr

from .methods import Methods

IVAR_KWARG_NAME = 'ivars'
METHOD_KWARG_NAME = 'methods'
CMETHOD_KWARG_NAMES = ['cmethods','classmethods']
SMETHOD_KWARG_NAMES = ['smethods','staticmethods']
SMEMBER_KWARG_NAMES = ['smembers', 'staticmembers']
PROP_KWARG_NAMES = ['props','properties']
CACHED_PROP_KWARG_NAMES = ['cached_props','cached_properties']


@contextmanager
def use(o, local_conflict='ignore', **kwargs):
    stk = stack()
    frame_info = stk[2]
    frame = frame_info.frame
    glbls = frame.f_globals
    restore = {}
    if type(o) is dict:
        include = exclude = None
        if kwargs:
            if 'include' in kwargs:
                include = kwargs.pop('include')
                if isinstance(include, str): include = [include]
            if 'exclude' in kwargs:
                exclude = kwargs.pop('exclude')
                if isinstance(exclude, str): exclude = [exclude]
            if kwargs:
                raise ValueError(f'Unexpected kwargs for use(dict): {",".join(kwargs)}')
            if include and exclude:
                raise ValueError('Specify at most one of [include,exclude]')

        for k,v in o.items():
            if include and k not in include: continue
            if exclude and k in exclude: continue
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
            include = kwargs['include']
            if isinstance(include, str): include = [include]
            for k in include:
                if k == IVAR_KWARG_NAME: ivars = True
                if k == METHOD_KWARG_NAME: methods = True
                if k in CMETHOD_KWARG_NAMES: cmethods = True
                if k in SMETHOD_KWARG_NAMES: smethods = True
                if k in SMEMBER_KWARG_NAMES: smembers = True
                if k in PROP_KWARG_NAMES: properties = True
                if k in CACHED_PROP_KWARG_NAMES: cached_properties = True
        else:
            ivars = True
            methods = True
            cmethods = True
            smethods = True
            smembers = True
            properties = True
            cached_properties = True
            if 'exclude' in kwargs:
                exclude = kwargs['exclude']
                if isinstance(exclude, str): exclude = [exclude]
                for k in exclude:
                    if k == IVAR_KWARG_NAME: ivars = False
                    if k == METHOD_KWARG_NAME: methods = False
                    if k in CMETHOD_KWARG_NAMES: cmethods = False
                    if k in SMETHOD_KWARG_NAMES: smethods = False
                    if k in SMEMBER_KWARG_NAMES: smembers = False
                    if k in PROP_KWARG_NAMES: properties = False
                    if k in CACHED_PROP_KWARG_NAMES: cached_properties = False
            else:
                for k,v in kwargs.items():
                    if k == IVAR_KWARG_NAME: ivars = bool(v)
                    if k == METHOD_KWARG_NAME: methods = bool(v)
                    if k in CMETHOD_KWARG_NAMES: cmethods = bool(v)
                    if k in SMETHOD_KWARG_NAMES: smethods = bool(v)
                    if k in SMEMBER_KWARG_NAMES: smembers = bool(v)
                    if k in PROP_KWARG_NAMES:
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
        if             ivars: assign.update(m.            ivars)
        if           methods: assign.update(m.          methods)
        if          cmethods: assign.update(m.         cmethods)
        if          smethods: assign.update(m.         smethods)
        if          smembers: assign.update(m.         smembers)
        if cached_properties: assign.update(m.cached_properties)
        if        properties: assign.update(m.       properties)

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


