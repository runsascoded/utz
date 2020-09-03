# utz
Misc stdlib, pandas, subprocess, and other utilities, exposed for easy importing + boilerplate-reduction

## Install
```bash
pip install utz
```

## Use
Import the whole kitchen sink:
```python
from utz.imports import *
```

See [imports.py](utz/imports.py), which imports many of the modules below, as well as a bevy of handy stdlib methods and objects.

Some noteworthy modules:
- [pnds](utz/pnds.py): common [pandas](https://pandas.pydata.org/) imports
- [cd](utz/cd.py): "change directory" contextmanager
- [o](utz/o.py): object (dict) wrapper that exposes keys as attrs (e.g.: `o({'a':1}).a == 1`)
- [process](utz/process.py): subprocess wrappers for more easily shelling out commands
- [git](utz/git): git helpers / wrappers around [GitPython](https://gitpython.readthedocs.io/en/stable/)
- [collections](utz/collections.py): collection/list helpers
- [context](utz/context.py): contextlib helpers
