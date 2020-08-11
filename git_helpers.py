#!/usr/bin/env python
# coding: utf-8

# In[1]:


#import ur
from .process import run, line, check


def branch_exists(branch):
    return check('git','show-ref','--verify','--quiet',f'refs/heads/{branch}')


def current_branch():
    return line('git','symbolic-ref','-q','--short','HEAD')


def ensure_remote(remote, url):
    if remote_exists(remote):
        remote_url = line('git','remote','get-url',remote)
        if remote_url != url:
            print(f'Updating URL for remote {remote}: {remote_url} → {url}')
            run('git','remote','set-url',remote,url)
    else:
        run('git','remote','add',remote,url)

    run('git','fetch',remote)


def remote_and_branch(remote, url, branch, remote_branch='master'):
    ensure_remote(remote, url)
    upstream = f'{remote}/{remote_branch}'
    if branch_exists(branch):
        run('git','branch','-u',upstream,branch)
        run('git','checkout',branch)
    else:
        run('git','checkout','-b',branch,'-t',upstream)

