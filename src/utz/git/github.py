from __future__ import annotations

import re
from functools import wraps
from os import environ
from typing import Literal

import utz
from utz import proc

GITHUB_HTTPS_URL_RGX = r'https://github.com/(?P<nameWithOwner>[^/]+/[^/]+?)(?:\.git)?'
GITHUB_SSH_URL_RGX = r'git@github.com:(?P<nameWithOwner>[^/]+/[^/]+?)(?:\.git)?'


def parse_url(url: str, err: Literal['raise', 'stderr', 'none'] = 'raise') -> str | None:
    m = re.fullmatch(GITHUB_HTTPS_URL_RGX, url)
    if m:
        return m.group('nameWithOwner')
    m = re.fullmatch(GITHUB_SSH_URL_RGX, url)
    if m:
        return m.group('nameWithOwner')
    if err == 'raise':
        raise ValueError(f'Could not parse GitHub url: {url}')
    elif err == 'stderr':
        utz.err(f'Could not parse GitHub url: {url}')
    return None


GITHUB_REPOSITORY = 'GITHUB_REPOSITORY'


def repository_option(
    *flag_args,
    env=GITHUB_REPOSITORY,
    help='Repository name (with owner, e.g. "owner/repo"), defaults to $GITHUB_REPOSITORY then `gh repo view --json nameWithOwner`', **flag_kwargs,
):
    if not flag_args:
        flag_args = ('-R', '--repository')

    def option(fn):
        from click import option

        @option(*flag_args, help=help, **flag_kwargs)
        @wraps(fn)
        def _fn(*args, repository=None, **kwargs):
            if not repository:
                repository = environ.get(env)
                if not repository:
                    verbose = kwargs.get('verbose', 0)
                    repository = proc.json('gh', 'repo', 'view', '--json', 'nameWithOwner', log=None if verbose else False)['nameWithOwner']
            return fn(*args, repository=repository, **kwargs)

        return _fn

    return option
