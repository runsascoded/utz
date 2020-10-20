from utz.setup import setup

setup(
    install_requires=[
        "GitPython",
        "joblib",
        "pandas",
        "python-dateutil",
        "pyyaml",
    ],
    extras_require={
        'pdf': [
            'reportlab==3.5.42',
            'pyPDF2==1.26.0',
        ],
        'setup': [
            'lxml==4.6.1',
            'mistune==2.0.0a5',
        ]
    },
    scripts=['utz.sh',],
    url="https://github.com/runsascoded/utz",
)
