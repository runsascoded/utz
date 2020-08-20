#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import ur
from ..process import *
from . import branch as _branch

def ls(): return lines('git','remote')

def exists(name): return name in ls()

def url(name, *args, **kwargs):
    if not exists(name):
        if len(args) == 1:
            default = args[0]
        elif 'default' in kwargs:
            default = kwargs.pop('default')
        else:
            raise ValueError(f"Remote {name} doesn't exist")

        return default
    
    return line('git','remote','get-url',name)
_url = url

def init(name, url, branch=None, remote_branch=None, fetch=True, checkout=True):
    if exists(name):
        existing_url = _url(name)
        if existing_url != url:
            run('git','remote','set-url',name,url)
    else:
        run('git','remote','add',name,url)
    
    if fetch:
        run('git','fetch',name)
    
    if branch:
        remote_branch = remote_branch or 'master'
        upstream = f'{name}/{remote_branch}'
        run('git','branch','-u',upstream,branch)
        if checkout:
            run('git','checkout',branch)

def push(name=None, local=None, remote=None):
    refspec = None
    if local:
        if remote:
            refspec = f'{local}:{remote}'
        else:
            refspec = f'{local}:{local}'
    
    run('git','push',name,refspec)

