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
    },
    scripts=['utz.sh',],
    url="https://github.com/runsascoded/utz",
)
