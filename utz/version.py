from pkg_resources import DistributionNotFound
from re import fullmatch
from subprocess import CalledProcessError

from .process import line


VERSION_TAG_REGEX = r'v?(?P<version>(?P<base>\d+\.\d+\.\d+)(?P<rc>(?:r|c|rc|a|b)\d+)?(?:-(?P<commits_ahead>\d+)-g(?P<sha>[0-9a-f]{6,}))?)'


def git_version():
    '''Infer version from git tag of the form "v_._._"; otherwise, return current Git commit SHA'''
    try:
        tag = line('git','describe','--tags','HEAD')
        m = fullmatch(VERSION_TAG_REGEX, tag)
        if not m:
            raise ValueError('Unrecognized tag: %s' % tag)
        version = m['version']
    except CalledProcessError:
        version = line('git','log','--format=%h','-n1')

    return version


def pkg_version(name=None):
    from pkg_resources import get_distribution
    try:
        pkg = get_distribution(name)
        return pkg.version
    except DistributionNotFound:
        return git_version()
