from utz import contextmanager, git, line, o, run


@contextmanager
def txn(start=None, msg=None, add=None,):
    '''Contextmanager that creates a synthetic merge with __enter__- and __exit__-time HEADs as parents, and tree (and
    message, by default) of the latter.

    The yielded value is an o() dict-wrapper whose `msg` and `add` attrs will be used to configure a final commit
    '''
    start = start or git.sha()
    ctx = o()
    if add:
        ctx.add = add
    if msg:
        ctx.msg = msg
    yield ctx

    if ctx('exit'):
        return

    end = git.sha()

    add = ctx('add')
    msg = ctx('msg') or f'merge txn: {start}, {end}'

    if add:
        run('git','add', add)

    if git.diff.exists(untracked=False, unstaged=False):
        run('git','commit','-m',msg)
    elif ctx('empty'):
        run('git','commit','--allow-empty','-m',msg)

    if start != end:
        repo = git.Repo()
        tree = repo.tree().hexsha
        head = line('git','commit-tree',tree,'-p',start,'-p',end,'-m',msg)
        run('git','reset',head)
