import pytest

from .paths import GSMO, HAILSTONE
from utz import basename, CalledProcessError, cd, env, exists, getcwd, git, lines, realpath, run, line, \
    now, b62


def test_current_branch():
    branch = 'tmp'
    sha = 'e0add3d'
    with git.clone.tmp(HAILSTONE, branch=branch, ref=sha):
        assert git.branch.current() == branch
        assert git.sha() == sha
        run('git', 'checkout', sha)  # detach HEAD
        with pytest.raises(CalledProcessError):
            assert git.branch.current() == branch  # by default, no branch ⟹ error
        assert git.branch.current(sha_ok=True) == sha  # can return SHA instead
        assert git.branch.current(sha_ok=None) is None  # or None


def check(cwd=None, name=None, status=True, branch=None, paths=None, shas=None, files=None, rm=None, ):
    if cwd:
        # Check that we're actually in the directory returned by the ctx mgr above:
        dir = realpath(getcwd())
        assert dir == realpath(cwd)

    if name:
        # check basename
        assert basename(getcwd()) == name

    if status:
        if status is True:
            # verify clone is clean
            assert not lines('git', 'status', '--short')
        else:
            # verify status lines
            assert lines('git', 'status', '--short') == status

    # verify current branch
    if branch:
        assert git.branch.current() == branch

    # verify submodules have been cloned
    if paths:
        if isinstance(paths, str): paths = [paths]
        for path in paths:
            assert exists(path), f"{path} doesn't exist"

    # verify various shas
    for sha, refs in shas.items():
        if isinstance(refs, (list, tuple)):
            for ref in refs:
                if ref is None:
                    assert git.sha() == sha
                else:
                    assert git.sha(ref) == sha

    if files:
        for path, lns in files.items():
            assert lines('cat', path) == lns

    if rm:
        assert not exists(rm)


def commit_file(path, lines, parent_sha=None, mode='w', fmt='%h', commit=True):
    new_file = not exists(path)
    with open(path, mode) as f:
        if isinstance(lines, str): lines = [lines]
        f.writelines('%s\n' % ln for ln in lines)
    run('git', 'add', path)
    if new_file:
        msg = f'add {path}: {lines}'
    else:
        msg = f'update {path}: {lines}'
    if commit:
        run('git', 'commit', '-m', msg)
        if parent_sha:
            assert git.sha('HEAD^') == parent_sha
        return git.fmt(fmt)


def test_tmp_clone_remote_push_changes():
    # set this HAILSTONE_SSH_URL to a different fork or repo if developing without access to this one
    url = env.get('HAILSTONE_SSH_URL', 'git@gitlab.com:gsmo/examples/hailstone.git')
    nonce = b62(now().ms)
    branch = f'tmp-{nonce}'
    sha0 = 'e0add3d'
    with git.clone.tmp(url, branch=branch, ref=sha0, push=True) as cwd:
        tmpdir = cwd
        check(cwd=cwd, name='hailstone', shas={sha0: (None, branch)})
        sha1 = commit_file('test1.txt', ['111', '222'], sha0, fmt='%H')

    try:
        assert not exists(tmpdir)
        assert git.ls_remote(url, head=branch) == sha1
    finally:
        run('git', 'push', '--delete', url, branch)


def test_tmp_clone_local_pull_changes():
    branch = 'tmp'
    tag = 'v0.1.1rc2'
    sha0 = 'de6da9d'

    # bind some `check` params
    def verify(wd, sha):
        check(
            cwd=wd,
            name='gsmo',
            paths='example/hailstone/run.ipynb',
            branch=branch,
            shas={sha: (None, branch)},
        )

    with git.clone.tmp(GSMO, branch=branch, ref=tag) as origin:
        verify(origin, sha0)

        # simulate an additional clone + pulling changes back in
        with git.clone.tmp(origin, branch=branch, pull=True) as wd:
            tmpdir = wd
            verify(wd, sha0)
            sha1 = commit_file('test1.txt', ['123', '456'], sha0)

        check(
            shas={sha1: (None, branch)},
            branch=branch,
            files={'test1.txt': ['123', '456']},
            rm=tmpdir,  # verify the tmpdir is gone
        )

        # simulate an additional clone + merging changes back in with concurrent upstream changes
        with git.clone.tmp(origin, branch=branch, pull=True) as wd:
            tmpdir = wd
            verify(wd, sha1)
            sha2_2 = commit_file('test2.txt', ['abc', 'def'], sha1)

            # meanwhile, make another change in origin (which will have to be merged w/ sha2)
            with cd(origin):
                sha2_1 = commit_file('test1.txt', '789', sha1, mode='a')

            # on ctx mgr exit, merge is performed…

        sha2 = git.sha()
        check(
            shas={
                sha2: branch,
                sha2_1: 'HEAD^',
                sha2_2: 'HEAD^2',
            },
            branch=branch,
            files={
                'test1.txt': ['123', '456', '789', ],
                'test2.txt': ['abc', 'def', ],
            },
            rm=tmpdir,
        )

        # simulate an additional clone + failing to merge changes in vs concurrent upstream changes, but leaving a ref
        # for safe-keeping
        with git.clone.tmp(origin, branch=branch, pull=True) as wd:
            tmpdir = wd
            verify(wd, sha2)
            sha3_2 = commit_file('test2.txt', 'zzz', sha2, mode='a')

            # meanwhile, make another change in origin (which will have to be merged w/ sha2)
            with cd(origin):
                sha3_1 = commit_file('test2.txt', 'yyy', sha2, mode='a')

            # on ctx mgr exit, merge is performed, but a merge conflict arises, and a new branch `conflict-<sha>` points
            # at the unmerged temporary/remote changes

        conflict_branch = f'conflict-{sha3_2}'
        check(
            shas={
                sha3_1: (None, branch),
                sha3_2: conflict_branch,
                sha2: 'HEAD^',
            },
            branch=branch,
            files={
                'test1.txt': ['123', '456', '789', ],
                'test2.txt': ['abc', 'def', 'yyy', ],
            },
            rm=tmpdir,
        )

    # verify the tmpdir is gone
    assert not exists(origin)


def test_bare_tmp_clone():
    branch = 'tmp'
    sha0 = 'e0add3d'
    with git.clone.tmp(HAILSTONE, bare=True, branch=branch, ref=sha0) as origin:
        check(cwd=origin, status=False, branch=branch, shas={sha0: (None, branch)})
        with git.clone.tmp(origin, branch=branch) as wd:
            check(cwd=wd, name='hailstone', shas={sha0: (None, branch)})
            sha1 = commit_file('test1.txt', ['aaa', 'bbb'], sha0)
            remote = line('git', 'remote')
            run('git', 'push', remote)
            check(
                branch=branch,
                shas={
                    sha1: (None, branch, f'{remote}/{branch}'),
                    sha0: 'HEAD^',
                },
                files={'test1.txt': ['aaa', 'bbb']},
            )
        check(
            branch=branch,
            status=False,  # bare clone!
            shas={
                sha1: (None, branch),
                sha0: 'HEAD^',
            },
        )


def test_ls_remote_lines():
    from utz.git.remote import parse_ls_remote_lines
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

    assert git.ls_remote('https://gitlab.com/runsascoded/utz.git', tag='v0.2.2') == head


def test_atom():
    branch = 'tmp'
    sha0 = 'e0add3d'
    with git.clone.tmp(HAILSTONE, branch=branch, ref=sha0):
        with git.txn():
            pass
        check(shas={
            sha0: (None, branch),
        })

        with git.txn(add='value') as txn:
            commit_file('value', ['6'], commit=False)
            msg = 'set value=6'
            txn.msg = msg
        sha1 = git.sha()
        assert git.msg() == msg
        check(
            shas={
                sha1: (None, branch),
                sha0: f'{branch}^',
            },
            files={'value': ['6']},
        )

        # no additional commit is created with `add` param configured
        with git.txn():
            sha2 = commit_file('value', ['3'])
        sha3 = git.sha()
        assert git.msg() == f'merge txn: {sha1}, {sha2}'
        check(
            shas={
                sha3: (None, branch),
                sha2: f'{branch}^2',
                sha1: f'{branch}^',
            },
            files={'value': ['3']}
        )

        msg = 'two more updates'
        with git.txn(msg=msg):
            sha4 = commit_file('value', ['10'])
            sha5 = commit_file('value', ['5'])
        sha6 = git.sha()
        assert git.msg() == msg
        check(shas={
            sha6: (None, branch),
            sha5: f'{branch}^2',
            sha4: f'{branch}^2^',
            sha2: f'{branch}^',
        })

        msg = 'set value=8'
        with git.txn(add='value') as txn:
            sha7 = commit_file('value', ['16'])
            commit_file('value', ['8'], commit=False)
            txn.msg = msg
        sha8 = git.sha()
        assert git.msg() == msg
        check(
            shas={
                sha8: (None, branch),
                sha7: f'{branch}^2',
                sha6: (f'{branch}^2^', f'{branch}^',),
            },
            files={'value': ['8']},
        )
