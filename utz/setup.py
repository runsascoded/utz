import setuptools
from setuptools import find_packages

from utz import *


class Compute:
    '''Container for computing fallback values to pass to setup()'''

    def long_description(self):
        '''Read in README.md as the `long_description`'''
        if exists('README.md'):
            with open('README.md', "r") as fh:
                return fh.read()

    def long_description_content_type(self):
        '''Default to markdown format for `long_description`'''
        return "text/markdown"

    VERSION_TAG_REGEX = r'v?(?P<version>\d+\.\d+\.\d+(?:-(?P<commits_ahead>\d+)-g(?P<sha>[0-9a-f]{6,}))?)'
    def version(self):
        '''Infer version from git tag of the form "v_._._" (which must be present)'''
        try:
            tag = line('git','describe','--tags','HEAD')
            m = match(self.VERSION_TAG_REGEX, tag)
            if not m:
                raise ValueError('Unrecognized tag: %s' % tag)
            version = m['version']
        except CalledProcessError:
            version = line('git','log','--format=%h','-n1')

        return version

    def name(self):
        '''`name` defaults to the name of the containing directory'''
        return basename(getcwd())

    def author(self):
        '''Infer author name from most recent commit'''
        return line('git','log','-n1','--format=%an')

    def author_email(self):
        '''Infer author email from most recent commit'''
        return line('git','log','-n1','--format=%ae')

    def description(self):
        '''Set `description` to the contents of a <p> first-child of an initial <h1>'''
        from md2py import md2py
        md = md2py(self.long_description())
        h1 = md.h1
        desc = h1.descendants[0]
        if desc.name != 'p':
            raise ValueError('Parsing description failed due to first child of initial <h1> not being type <p>: %s' % str(desc))
        return desc.string

    def packages(self):
        return find_packages()

    def classifiers(self):
        return [
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ]

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
        'license',
        'author',
        'author_email',
        'packages',
        'classifiers',
        'python_requires',
    )

    setuptools.setup(**kwargs)
