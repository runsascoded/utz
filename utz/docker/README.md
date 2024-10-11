Utilities and a DSL for programmatically constructing Dockerfiles (and building images from them)

```python
from utz import *  # or: `from utz.docker.dsl import *`

def build_python_git_image(python_version, tag):
    """Build a Docker image with a specified Python version, and `git` installed."""
    with docker.File(tag=tag):
        FROM(f'python:{python_version}-slim')
        RUN(
            'apt-get update',
            'apt-get install -y git',
        )
        ENTRYPOINT('python','-V')

# build 3 images with various python versions
[
    build_python_git_image(pv, f'python-git:{pv}')
    for pv in ('3.7.9', '3.8.6', '3.9.1',)
]


run('docker','run','python-git:3.9.1')
# Python 3.9.1
```

See also [`utz/tests/test_docker.py`](../tests/test_docker.py).
