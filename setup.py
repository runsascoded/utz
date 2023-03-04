from utz.setup import setup

setup(
    name="utz",
    version="0.3.24",
    install_requires=open('requirements.txt', 'r').read(),
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
