#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from ..process import *

def ls():
    return lines('git','submodule','foreach','--quiet','echo $name')

def exists(name): return name in ls()

def add(url, path=None):
    if exists(name): return
    cmd = ['git','submodule','add','url']
    if path: cmd.append(path)
    run(cmd)

