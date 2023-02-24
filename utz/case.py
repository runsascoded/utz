CAPS_RGX = re.compile(r'(?<!^)(?=[A-Z])')


def dash_case(camel_case):
    return CAPS_RGX.sub('-', camel_case).lower()


def snake_case(camel_case):
    return CAPS_RGX.sub('_', camel_case).lower()


def camel_case(s):
    def upper_first(pc):
        return pc[0].upper() + pc[1:]
    return ''.join([ upper_first(pc) for pc in re.split('[-_:]', s) ])
