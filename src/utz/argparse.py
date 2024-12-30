
def parse_dict(args, attr, default_ok=True):
    """Parse an "nargs='*'" field from an ArgumentParser's parsed arguments

    Each argument value should be of the form <k>=<v>, and a dict() of those mappings will be returned

    At most one argument value can simply be of the form <v>, in which case it will be assigned to the None value in the returned dict
    """
    arg = getattr(args, attr)
    ret = {}
    if isinstance(arg, list):
        for entry in arg:
            pcs = entry.split('=', 1)
            if len(pcs) == 2:
                [ repository, arg ] = pcs
                ret[repository] = arg
            elif len(pcs) == 1 and default_ok:
                if None in ret:
                    raise ValueError(f'Invalid --{attr}: multiple default values ({ret[None]}, {pcs[0]})')
                ret[None] = arg
            else:
                raise ValueError(f'Invalid --{attr}: {arg}')
    return ret
