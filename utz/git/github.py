import re
from sys import stderr
from typing import Optional, Literal

GITHUB_HTTPS_URL_RGX = r'https://github.com/(?P<nameWithOwner>[^/]+/[^/]+?)(?:\.git)?'
GITHUB_SSH_URL_RGX = r'git@github.com:(?P<nameWithOwner>[^/]+/[^/]+?)(?:\.git)?'


def parse_url(url: str, err: Literal['raise', 'stderr', 'none'] = 'raise') -> Optional[str]:
    m = re.fullmatch(GITHUB_HTTPS_URL_RGX, url)
    if m:
        return m.group('nameWithOwner')
    m = re.fullmatch(GITHUB_SSH_URL_RGX, url)
    if m:
        return m.group('nameWithOwner')
    if err == 'raise':
        raise ValueError(f'Could not parse GitHub url: {url}')
    elif err == 'stderr':
        print(f'Could not parse GitHub url: {url}', file=stderr)
    return None
