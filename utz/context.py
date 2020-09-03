#!/usr/bin/env python
# coding: utf-8

# # Context Manager utilities

# General/Common imports:

# In[ ]:


from contextlib import AbstractContextManager, contextmanager, suppress


# ## `nullcontext`
# Define `nullcontext` in a cross-version way:

# In[ ]:


try:
    # Python ≥3.7
    from contextlib import nullcontext
except ImportError:
    # Python <3.7
    class nullcontext(object):
        def __enter__(self): pass
        def __exit__(self, *args): pass


# Verify it works:

# In[2]:


with nullcontext(): pass


# ## `catch`: context manager for catching+verifying `Exception`s

# In[ ]:


class catch(AbstractContextManager):
    def __init__(self, *excs):
        self.excs = excs

    def __exit__(self, exc_type, exc_value, traceback):
        if not exc_type:
            if len(self.excs) == 1:
                raise AssertionError(f'No {self.excs[0].__name__} was thrown')
            else:
                raise AssertionError(f'None of {",".join([e.__name__ for e in self.excs])} were thrown')
        
        if not [ isinstance(exc_value, exc) for exc in self.excs ]:
            raise exc_value

        return True


# ## `no`: context manager for verifying `NameError`s (undefined variable names)

# In[1]:


no = catch(NameError)

