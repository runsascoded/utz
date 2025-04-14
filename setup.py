from setuptools import find_packages

from utz.setup import setup

extras_require = {
    'cli': [ 'click' ],
    'dt': [
        'click',
        'python-dateutil',
        'pytz',
    ],
    'git': [
        'click',
        'GitPython',
        'PyGithub',
    ],
    'mem': [ 'memray' ],
    'pd': [
        'numpy',
        'pandas',
    ],
    'pdf': [
        'reportlab',
        'pyPDF2',
    ],
    'plot': [
        'jupyter',
        'kaleido',
        'plotly',
    ],
    's3': [ 'boto3', 'botocore', ],
    'setup': [ 'setuptools' ],
    'size': [ 'humanize' ],
    'test': [
        'pytest',
        'pytest-mock',
        'python-dateutil==2.9.0'  # Verified (as an example) in `test_setup.py`
    ],
}
extras_require['all'] = sum(extras_require.values(), [ 'pyyaml', ])

setup(
    name="utz",
    version="0.19.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=["stdlb"],
    extras_require=extras_require,
    url="https://github.com/runsascoded/utz",
    python_requires=">=3.9",
)
