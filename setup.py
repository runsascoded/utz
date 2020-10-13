from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

from utz import *
rgx = r'v?(?P<version>\d+\.\d+\.\d+)'
tag = line('git','describe','HEAD')
version = match(rgx, tag)['version']

setup(
    name="utz",
    version=version,
    author="Ryan Williams",
    author_email="ryan@runsascoded.com",
    description="Misc stdlib, pandas, subprocess, and other utilities, exposed for easy importing + boilerplate-reduction",
    install_requires=[
        "GitPython",
        "joblib",
        "pandas",
        "pyyaml",
    ],
    extras_require={
        'pdf': [
            'reportlab==3.5.42',
            'pyPDF2==1.26.0',
        ],
    },
    scripts=['utz.sh',],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/runsascoded/utz",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
