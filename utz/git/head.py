#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import ur
from ..process import line
def sha(): return line('git','log','-n1','--format=%h')
def subject(): return line('git','log','-n1','--format=%s')

