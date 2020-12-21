
import utz
from utz import basename, cd, dirname, exists, getcwd, git, join, lines, realpath, run


def test_tmp_clone_remote():
    with git.clone.tmp('https://gitlab.com/gsmo/examples/factors.git') as cwd:
        # Check that we're actually in the directory returned by the ctx mgr above:
        tmpdir = realpath(getcwd())
        assert tmpdir == realpath(cwd)
        assert basename(getcwd()) == 'factors'
        # It's a clean clone
        assert not lines('git','status','--short')

    # verify the tmpdir is gone
    assert not exists(tmpdir)

def test_tmp_clone_local():
    branch = 'tmp'
    tag = 'v0.0.1'
    base_repo = join(dirname(utz.__file__), 'tests/data/gsmo')
    sha0 = '68a257a'

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

    # bind some `check` params
    def verify(wd, sha):
        check(
            cwd=wd,
            name='gsmo',
            paths='example/hailstone/run.ipynb',
            branch=branch,
            shas={sha: (None, branch)},
        )

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

        conflict_branch = f'conflict-{git.fmt("%h", sha3_2)}'
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
