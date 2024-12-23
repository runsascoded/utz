from utz.setup import setup

extras_require = {
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
        'python-dateutil==2.9.0'  # Verified (as an example) in `test_setup.py`
    ],
}
extras_require['all'] = sum(extras_require.values(), [ 'pyyaml', ])

setup(
    name="utz",
    version="0.12.0",
    install_requires=["stdlb"],
    extras_require=extras_require,
    url="https://github.com/runsascoded/utz",
    python_requires=">=3.9",
)
