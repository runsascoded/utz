from ..proc import line


def sha(*args,**kwargs):
    return line('git','log','-n1','--format=%h',*args,**kwargs)


def fmt(fmt, *args, **kwargs):
    return line('git','log','-n1',f'--format={fmt}',*args,**kwargs)


def subject(*args,**kwargs):
    return line('git','log','-n1','--format=%s',*args,**kwargs)
