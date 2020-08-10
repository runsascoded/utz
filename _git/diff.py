#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import ur
from ..process import *

def exists(untracked=True):
    files = lines('git','status','--porcelain')
    if not untracked:
        files = [ file for file in files if not file.startswith('??') ]
    return bool(files)

