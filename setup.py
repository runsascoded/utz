from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="utz",
    version="0.0.8",
    author="Ryan Williams",
    author_email="ryan@runsascoded.com",
    description="Misc stdlib, pandas, subprocess, and other utilities, exposed for easy importing + boilerplate-reduction",
    install_requires=[
        "GitPython",
        "joblib",
        "pandas",
        "pyyaml",
    ],
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
