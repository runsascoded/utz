import re

CAPS_RGX = re.compile(r'(?<!^)(?=[A-Z])')


def dash_case(orig):
    if '_' in orig:
        return re.sub("_", "-", orig)
    else:
        return CAPS_RGX.sub('-', orig).lower()


def snake_case(orig):
    if '-' in orig:
        return re.sub("-", "_", orig)
    else:
        return CAPS_RGX.sub('_', orig).lower()


def camel_case(s):
    def upper_first(pc):
        return pc[0].upper() + pc[1:]
    return ''.join([ upper_first(pc) for pc in re.split('[-_:]', s) ])
