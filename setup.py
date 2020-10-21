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
            'mistune>=0.8.1,<2',  # match nbconvert
        ]
    },
    scripts=['utz.sh',],
    url="https://github.com/runsascoded/utz",
)
