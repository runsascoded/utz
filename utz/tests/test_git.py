
import utz
from utz import basename, cd, dirname, env, exists, getcwd, git, join, line, lines, realpath, run


def check(cwd=None, name=None, status=True, branch=None, paths=None, shas=None, files=None, rm=None,):
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
            assert not lines('git','status','--short')
        else:
            # verify status lines
            assert lines('git','status','--short') == status

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
        if isinstance(refs, (list,tuple)):
            for ref in refs:
                if ref is None:
                    assert git.sha() == sha
                else:
                    assert git.sha(ref) == sha

    if files:
        for path, lns in files.items():
            assert lines('cat',path) == lns

    if rm:
        assert not exists(rm)


def commit_file(path, lines, parent_sha, mode='w'):
    new_file = not exists(path)
    with open(path, mode) as f:
        if isinstance(lines, str): lines = [lines]
        f.writelines('%s\n' % ln for ln in lines)
    run('git','add',path)
    if new_file:
        msg = f'add {path}: {lines}'
    else:
        msg = f'update {path}: {lines}'
    run('git','commit','-m',msg)
    assert git.sha('HEAD^') == parent_sha
    return git.sha()


def test_tmp_clone_remote_push_changes():
    # set this HAILSTONE_SSH_URL to a different fork or repo if developing without access to this one
    url = env.get('HAILSTONE_SSH_URL', 'git@gitlab.com:gsmo/examples/hailstone.git')
    branch = 'tmp'
    sha0 = 'f09bd0a'
    with git.clone.tmp(url, branch=branch, init=sha0, push=True) as cwd:
        tmpdir = cwd
        check(cwd=cwd, name='hailstone', shas={ sha0: (None, branch) })
        sha1 = commit_file('test1.txt',['111','222'], sha0)

    try:
        # verify the tmpdir is gone
        assert not exists(tmpdir)

        ref_str = f'refs/heads/{branch}'
        remote_line = line('git','ls-remote','--heads',url,ref_str)
        run('git','fetch',url,f'{branch}:{branch}')
        full_sha = git.fmt('%H', sha1)
        assert remote_line == '%s\t%s' % (full_sha, ref_str)
    finally:
        run('git','push','--delete',url,branch)


def test_tmp_clone_local_pull_changes():
    branch = 'tmp'
    tag = 'v0.0.1'
    base_repo = join(dirname(utz.__file__), 'tests/data/gsmo')
    sha0 = '68a257a'

    # bind some `check` params
    def verify(wd, sha):
        check(
            cwd=wd,
            name='gsmo',
            paths='example/hailstone/run.ipynb',
            branch=branch,
            shas={sha: (None, branch)},
        )

    with git.clone.tmp(base_repo, branch=branch, init=tag) as origin:
        verify(origin, sha0)

        # simulate an additional clone + pulling changes back in
        with git.clone.tmp(origin, branch=branch, pull=True) as wd:
            tmpdir = wd
            verify(wd, sha0)
            sha1 = commit_file('test1.txt', ['123','456'], sha0)

        check(
            shas={ sha1: (None, branch) },
            branch=branch,
            files={ 'test1.txt': ['123','456'] },
            rm=tmpdir,  # verify the tmpdir is gone
        )

        # simulate an additional clone + merging changes back in with concurrent upstream changes
        with git.clone.tmp(origin, branch=branch, pull=True) as wd:
            tmpdir = wd
            verify(wd, sha1)
            sha2_2 = commit_file('test2.txt', ['abc','def'], sha1)

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
                'test1.txt': ['123','456','789',],
                'test2.txt': ['abc','def',],
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
                'test1.txt': ['123','456','789',],
                'test2.txt': ['abc','def','yyy',],
            },
            rm=tmpdir,
        )

    # verify the tmpdir is gone
    assert not exists(origin)


def test_ls_remote_lines():
    from utz.git.remote import parse_ls_remote_lines
    sha = 'e0add3d2805fc8999dab650697a22f1939fd5396'
    hailstone_lines = [
        f'{sha}	HEAD',
        f'{sha}	refs/heads/master',
    ]
    assert parse_ls_remote_lines(hailstone_lines) == dict(head=sha, heads={'master':sha})
    assert parse_ls_remote_lines(hailstone_lines, sha=sha) == dict(head=sha,heads={'master':sha})
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
    assert parse_ls_remote_lines(utz_lines) == dict(head=head, heads=heads, tags=tags,)
    assert parse_ls_remote_lines(utz_lines, sha=head) == dict(head=head, heads={'py':head}, tags={'v0.2.2':head},)
    assert parse_ls_remote_lines(utz_lines, head='py') == head
    assert parse_ls_remote_lines(utz_lines, head='nope') is None
    assert parse_ls_remote_lines(utz_lines, tag='v0.2.2') == head
    assert parse_ls_remote_lines(utz_lines, tag='nope') is None
    assert parse_ls_remote_lines(utz_lines, heads=True) == heads
    assert parse_ls_remote_lines(utz_lines, tags=True) == tags
    assert parse_ls_remote_lines(utz_lines, heads=True, tags=True) == dict(heads=heads, tags=tags)
    assert parse_ls_remote_lines(utz_lines, sha=head, heads=True) == {'py':head}
    assert parse_ls_remote_lines(utz_lines, sha=head, tags=True) == {'v0.2.2':head}
    assert parse_ls_remote_lines(utz_lines, sha=head, heads=True, tags=True) == dict(heads={'py':head}, tags={'v0.2.2':head})

    assert git.ls_remote('https://gitlab.com/runsascoded/utz.git', tag='v0.2.2') == head
