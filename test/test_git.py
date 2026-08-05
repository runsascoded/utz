import pytest

from utz import git
from utz.git.remote import parse_ls_remote_lines


def test_parse_ls_remote_lines():
    sha = 'e0add3d2805fc8999dab650697a22f1939fd5396'
    hailstone_lines = [
        f'{sha}	HEAD',
        f'{sha}	refs/heads/master',
    ]
    assert parse_ls_remote_lines(hailstone_lines) == dict(head=sha, heads={'master': sha})
    assert parse_ls_remote_lines(hailstone_lines, sha=sha) == dict(head=sha, heads={'master': sha})
    assert parse_ls_remote_lines(hailstone_lines, head='master') == sha

    utz_lines = [
        '12bbfa076261df4ed8069bb91044971bd47892a8	HEAD',
        '3aded57969e3e71d2f28c47ed328529fb84fe963	refs/heads/master',
        'aec6bf6cb37f02d9e0c0fe9f136973f2adc221e3	refs/heads/nb',
        '12bbfa076261df4ed8069bb91044971bd47892a8	refs/heads/py',
        'a5dfc290398236c11ecc6afe576e70027793eb1a	refs/tags/v0.1.3',
        '5313cee06bc686c90bb5dd6a2e2c3c8ad2d27a4a	refs/tags/v0.2.0',
        'a67870037d4c3006d515244ce9e9c51a6345e175	refs/tags/v0.2.1',
        '12bbfa076261df4ed8069bb91044971bd47892a8	refs/tags/v0.2.2',
    ]
    head = '12bbfa076261df4ed8069bb91044971bd47892a8'
    heads = {
        'master': '3aded57969e3e71d2f28c47ed328529fb84fe963',
        'nb': 'aec6bf6cb37f02d9e0c0fe9f136973f2adc221e3',
        'py': '12bbfa076261df4ed8069bb91044971bd47892a8',
    }
    tags = {
        'v0.1.3': 'a5dfc290398236c11ecc6afe576e70027793eb1a',
        'v0.2.0': '5313cee06bc686c90bb5dd6a2e2c3c8ad2d27a4a',
        'v0.2.1': 'a67870037d4c3006d515244ce9e9c51a6345e175',
        'v0.2.2': '12bbfa076261df4ed8069bb91044971bd47892a8',
    }
    assert parse_ls_remote_lines(utz_lines) == dict(head=head, heads=heads, tags=tags, )
    assert parse_ls_remote_lines(utz_lines, sha=head) == dict(head=head, heads={'py': head}, tags={'v0.2.2': head}, )
    assert parse_ls_remote_lines(utz_lines, head='py') == head
    assert parse_ls_remote_lines(utz_lines, head='nope') is None
    assert parse_ls_remote_lines(utz_lines, tag='v0.2.2') == head
    assert parse_ls_remote_lines(utz_lines, tag='nope') is None
    assert parse_ls_remote_lines(utz_lines, heads=True) == heads
    assert parse_ls_remote_lines(utz_lines, tags=True) == tags
    assert parse_ls_remote_lines(utz_lines, heads=True, tags=True) == dict(heads=heads, tags=tags)
    assert parse_ls_remote_lines(utz_lines, sha=head, heads=True) == {'py': head}
    assert parse_ls_remote_lines(utz_lines, sha=head, tags=True) == {'v0.2.2': head}
    assert parse_ls_remote_lines(utz_lines, sha=head, heads=True, tags=True) == dict(heads={'py': head},
                                                                                     tags={'v0.2.2': head})


@pytest.mark.live
def test_ls_remote():
    head = '12bbfa076261df4ed8069bb91044971bd47892a8'
    assert git.ls_remote('https://gitlab.com/runsascoded/utz.git', tag='v0.2.2') == head
