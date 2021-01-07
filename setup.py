from utz.setup import setup

setup(
    install_requires=[
        "GitPython",
        "joblib",
        "pandas",
        "python-dateutil==2.8.1",
        "pytz",
        "pyyaml==5.3.1",
    ],
    extras_require={
        'pdf': [
            'reportlab==3.5.42',
            'pyPDF2==1.26.0',
        ],
        'setup': [
            'lxml==4.6.1',
            'mistune>=0.8.1,<2',  # match nbconvert
        ],
        'test': [
            'pytest==6.0.1',
            'pytest-mock==3.3.1',
        ],
    },
    url="https://github.com/runsascoded/utz",
)
