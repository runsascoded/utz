
from utz import exists, getcwd, git, lines, realpath


def test_tmp_clone():
    tmpdir = None
    with git.clone.tmp('https://gitlab.com/gsmo/examples/factors.git') as cwd:
        # Check that we're actually in the directory returned by the ctx mgr above:
        tmpdir = realpath(getcwd())
        assert tmpdir == realpath(cwd)
        # It's a clean clone
        assert not lines('git','status','--short')
    assert not exists(tmpdir)
