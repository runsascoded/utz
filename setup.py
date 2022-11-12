from utz.setup import setup

setup(
    install_requires=[
        "GitPython",
        "joblib",
        "pandas",
        "python-dateutil",
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
            'mistune',  # match nbconvert
        ],
        'test': [
            'pytest',
            'pytest-mock',
        ],
    },
    url="https://github.com/runsascoded/utz",
)
