#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from ..process import *

def exists(untracked=True, unstaged=True):
    files = lines('git','status','--porcelain')
    if not untracked:
        files = [ file for file in files if not file.startswith('??') ]
    if not unstaged:
        files = [ file for file in files if not file.startswith(' ') ]
    return bool(files)

