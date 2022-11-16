import setuptools
from setuptools import find_packages

from utz import *


class Compute:
    """Container for computing fallback values to pass to setup()"""

    def long_description(self):
        """Read in README.md as the `long_description`"""
        if exists('README.md'):
            with open('README.md', "r") as fh:
                return fh.read()

    def long_description_content_type(self):
        """Default to markdown format for `long_description`"""
        return "text/markdown"

    def version(self):
        return git_version()

    def name(self):
        """`name` defaults to the name of the containing directory"""
        return basename(getcwd())

    def author(self):
        """Infer author name from most recent commit"""
        return line('git','log','-n1','--format=%an')

    def author_email(self):
        """Infer author email from most recent commit"""
        return line('git','log','-n1','--format=%ae')

    def description(self):
        """Set `description` to the contents of a <p> first-child of an initial <h1>"""
        try:
            import mistune
        except ImportError:
            import pip
            pip.main(['install', 'mistune'])
            import mistune

        html = mistune.html(self.long_description())

        try:
            import lxml
        except ImportError:
            import pip
            pip.main(['install','lxml'])
            import lxml

        from lxml.html import fragments_fromstring
        [ h1, p, *_ ] = fragments_fromstring(html)
        if h1.tag != 'h1' or p.tag != 'p':
            raise ValueError('Expected initial <h1> followed by <p> while parsing `description` from README.md')

        return p.text_content()

    def packages(self):
        return find_packages()

    def classifiers(self):
        classifiers = [
            "Programming Language :: Python :: 3",
            "Operating System :: OS Independent",
        ]

        license = self.license()
        if license:
            classifiers += [f"License :: OSI Approved :: {license} License"]

        return classifiers

    def python_requires(self): return '>=3.6'

    def license(self):
        if exists('LICENSE'):
            with open('LICENSE','r') as f:
                lines = f.readlines()
                first_lines = [ line.strip() for line in lines[:2] ]
                if first_lines == ['Apache License','Version 2.0, January 2004',]: return 'Apache v2'
                if first_lines == ['MIT License','',]: return 'MIT'


def setup(**kwargs):
    c = Compute()
    def compute(*keys):
        for k in keys:
            if k not in kwargs:
                fn = getattr(c, k)
                v = fn()
                s = str(v)
                s = s[:100] + '…' if len(s) > 100 else s
                print('Fallback value: %s = %s' % (k, s))
                kwargs[k] = v

    compute(
        'name',
        'version',
        'description',
        'long_description',
        'long_description_content_type',
        'license',
        'author',
        'author_email',
        'packages',
        'classifiers',
        'python_requires',
    )

    setuptools.setup(**kwargs)
