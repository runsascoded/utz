import re


def escape(*args):
    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, dict):
            return " ".join(escape(k, v) for k,v in arg.items())
        else:
            backslashes = re.sub(r'\\',r'\\\\',str(arg))
            return re.sub(r'(["\n])',r'\\\1',backslashes)
    elif len(args) == 2:
        k,v = args
        return f'"{escape(k)}"="{escape(v)}"'


