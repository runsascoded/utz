#!/usr/bin/env python
# coding: utf-8

# # `o()`: attr-access for `dict`s
# Wrap `dict`s (or kwarg lists) to allow direct `.`-accessing of items.
# 
# Before:
# ```python
# x={'a':1,'b':2}  # given some dict
# x['a'], x['b']   # access fields via "getitem" syntax
# ```
# After:
# ```python
# x=o({'a':1,'b':2})  # wrap dict in o()
# x.a, x.b            # access members via "getattr" syntax
# ```
# Or, instantiate directly with kwargs:
# ```python
# x=o(a=1,b=2)
# x.a, x.b
# ```
# 
# **Contents:**
# - [Implementation](#Implementation)
# - [Examples](#Examples)

# ## Implementation

# In[1]:


class o(dict):
    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            raise ValueError(f'≤1 positional args required, got {len(args)}')
        
        if args:
            (data,) = args
            if type(data) is not dict:
                raise ValueError(f'Single-arg o() ctor call needs dict arg, not {type(data)}: {data}')
            if kwargs:
                raise ValueError(f'Positional dict arg is exclusive with kwargs: {data}, {kwargs}')
        else:
            data = kwargs

        K = '_data'
        if K in data:
            raise ValueError(f"Reserved key '{K}' found in 'data' dict: {data}")

        super().__init__(**data)

        for k, v in data.items():
            if isinstance(v, dict) and not isinstance(v, o): v = o(v)
            super(o, self).__setattr__(k, v)

        super(o, self).__setattr__(K, data)

    @classmethod
    def merge(cls, *args, **kwargs):
        if args:
            (obj, *args) = args
            obj = dict(obj)
        else:
            obj = dict()
        for arg in args:
            obj.update(**arg)
        for k,v in kwargs.items():
            obj[k] = v
        return o(obj)

    def __dict__(self): return dict(self._data)
    
    def __setattr__(self, k, v):
        if isinstance(v, dict) and not isinstance(v, o): v = o(v)
        self._data[k] = v

    def __getattr__(self, k):
        try:
            v = self._data[k]
            if isinstance(v, dict) and not isinstance(v, o): v = o(v)
            return v
        except KeyError:
            raise AttributeError(f'Key {k}')

    def get(self, k, default=None):
        if k in self:
            return self[k]
        else:
            return default

    def __call__(self, *keys, default=None):
        obj = self
        keys = list(keys)
        while keys:
            key = keys.pop(0)
            if key in obj:
                obj = obj[key]
            else:
                return default

        return obj

    def __getitem__(self, k):
        v = self._data[k]
        if isinstance(v, dict) and not isinstance(v, o): v = o(v)
        return v
    def __setitem__(self, k, v): self._data[k] = v
    def __contains__(self, k): return k in self._data
    
    def __str__(self): return str(self._data)
    def __repr__(self): return repr(self._data)

    def __iter__(self): return iter(self._data)
    def items(self): return self._data.items()

    def __eq__(self, r):
        if isinstance(r, o):
            return self._data == r._data
        if isinstance(r, dict):
            return self._data == r
        return NotImplemented

    def __ne__(self, r):
        if isinstance(r, o):
            return self._data != r._data
        if isinstance(r, dict):
            return self._data != r
        return NotImplemented

    def __hash__(self): return hash(self._data)


# ## Examples

# In[2]:


o1 = o(a=1,b=2)


# In[3]:


o1.a, o1.b


# In[4]:


from .context import catch
with catch(AttributeError): o1.c


# In[5]:


x={'c':3,'d':4}
o2 = o(x)
o2.c, o2.d


# In[6]:


x['e']=5
o2.e


# In[7]:


o2.c = 'ccc'
x


# In[8]:


o2


# In[9]:


str(o2)


# In[10]:


'c' in o2


# In[11]:


x


# In[12]:


list(iter(x))


# In[13]:


'z' in o2


# In[14]:


oo = o(a={'b':1})
oo


# In[15]:


oo.get('b', 'yay')


# In[16]:


oo.a.b

