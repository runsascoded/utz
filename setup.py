from utz.setup import setup

setup(
    name="utz",
    version="0.4.0",
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
    entry_points={
        'console_scripts': [
            'git-update-submodules=utz.git.git_update_submodules:main',
            'git-meta-branch-update=utz.git.git_meta_branch_update:main',
        ],
    },
)
