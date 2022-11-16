from utz.setup import setup

setup(
    install_requires=[
        "GitPython",
        "joblib",
        "pandas",
        "python-dateutil==2.8.2",
        "pytz",
        "pyyaml",
    ],
    extras_require={
        'pdf': [
            'reportlab',
            'pyPDF2',
        ],
        'setup': [
            'lxml',
            'mistune',
        ],
        'test': [
            'pytest',
            'pytest-mock',
        ],
    },
    url="https://github.com/runsascoded/utz",
)
