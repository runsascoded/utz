from utz.setup import setup

extras_require = {
    'dt': [
        'click',
        'python-dateutil==2.8.2',
        'pytz',
    ],
    'git': [
        'click',
        'GitPython',
        'PyGithub',
    ],
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
    'setup': [
        'setuptools',
    ],
    'test': [
        'pytest',
        'pytest-mock',
    ],
}
extras_require['all'] = sum(extras_require.values(), [ 'pyyaml', ])

setup(
    name="utz",
    version="0.8.1",
    extras_require=extras_require,
    url="https://github.com/runsascoded/utz",
    python_requires=">=3.10",
)
