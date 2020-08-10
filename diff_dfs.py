#!/usr/bin/env python
# coding: utf-8

# # Diff DFs
# Compute various diffs between two Pandas DataFrames
# 
# See [examples](#examples) / [usage](#diff) below.

# In[1]:


from IPython.display import HTML
from numpy import nan
from pandas import concat, Index, IndexSlice as idx, isna, MultiIndex
from re import sub

def neq(l, r): return l!=r and not (isna(l) and isna(r))

def blank_row(row, fill=''):
    l,r = row.iloc[:]
    if neq(l,r):
        return row
    else:
        row.loc[:] = (fill,fill)
        return row

def blank_eqs(df, fill=''):
    return df.apply(blank_row, axis=1, fill=fill)

class Diff:
    def __init__(self, l, r, **join_kwargs):
        self.l = l
        self.r = r

        l_col_set = self.l_col_set = set(l.columns)
        r_col_set = self.r_col_set = set(r.columns)
        l_only_col_names = self.l_only_col_names = [ c for c in l.columns if c not in r_col_set ]
        r_only_col_names = self.r_only_col_names = [ c for c in r.columns if c not in l_col_set ]
        lr_col_names = self.lr_col_names = Index([ c for c in l.columns if c in r_col_set ])

        l_only_cols = self.l_only_cols = l[l_only_col_names]
        r_only_cols = self.r_only_cols = r[r_only_col_names]

        l_row_set = self.l_row_set = set(l.index)
        r_row_set = self.r_row_set = set(r.index)
        l_only_row_names = self.l_only_row_names = [ c for c in l.index if c not in r_row_set ]
        r_only_row_names = self.r_only_row_names = [ c for c in r.index if c not in l_row_set ]
        lr_index = self.lr_index = Index([ c for c in l.index if c in r_row_set ])

        l_only_rows = self.l_only_rows = l.loc[l_only_row_names]
        r_only_rows = self.r_only_rows = r.loc[r_only_row_names]        

        l_shared = self.l_shared = l.loc[lr_index, lr_col_names]
        r_shared = self.r_shared = r.loc[lr_index, lr_col_names]

        groups = self.groups = {
            c: concat([l_shared[c].rename('l'),r_shared[c].rename('r')], axis=1)
            for c in lr_col_names
        }

        l_suffix, r_suffix = join_kwargs.get('suffixes', ('_x','_y'))
        suffixes_regex = f'(?:{l_suffix}|{r_suffix})$'
        merged = self.merged = l.merge(r, left_index=True, right_index=True, **join_kwargs)
        grouped = self.grouped = merged.groupby(lambda c: sub(suffixes_regex,'',c), axis=1)

        cols = self.cols = lr_col_names
        midx = MultiIndex.from_tuples([ (c, side) for c in cols for side in ['l','r'] ])

        # Build DF with top-level columns and {l,r} sub-columns with both sides' values
        df = self.df = concat(
            [ 
                (l_shared[c] if sfx == 'l' else r_shared[c]) \
                .rename((c, sfx))
                for c, sfx in midx
            ],
            axis=1,
        )
        df.columns.names = ['col','side']
        midx = self.midx = df.columns

        neqs = self.neqs = ((l_shared != r_shared) & (l_shared.notnull() | r_shared.notnull()))

        row_counts = self.row_counts = neqs.sum(axis=1)
        rows_changed = self.rows_changed = self.rows_changed = row_counts>0
        changed_rows = self.changed_rows = lr_index[rows_changed]        

        col_counts = self.col_counts = neqs.sum()
        cols_changed = self.cols_changed = col_counts>0
        changed_cols = self.changed_cols = lr_col_names[cols_changed]

        changed = self.changed = df.loc[changed_rows, idx[changed_cols,:]]

        clean = self.clean =             self             .changed             .groupby(level=0,axis=1)             .apply(blank_eqs, fill='')
    
    def _repr_html_(self): return self.clean._repr_html_()
    
    def __getattr__(self, k):
        if hasattr(self.changed, k):
            return getattr(self.changed, k)
        raise AttributeError(k)

    def __getitem__(self, k):
        if k in self.changed:
            return self.changed[k]
        raise AttributeError(k)


# ## Examples <a id="examples"></a>
# Build a synthetic DataFrame to test with:

# In[27]:


from hashlib import sha256
from pandas import DataFrame as DF, Series, Index
from numpy.random import choice, random, seed

# Seed PRNG
seed(123)

# Rows in the test DF
R = 20

# Use single letters for index elements
index = Index([ chr(i+ord('a')) for i in range(R) ])

# Generate some pseudorandom floats and bools
floats = Series(random(R), name='floats')
bools = Series(choice([False,True], R), name='bools')

# Generate some strings with many repeated values by hashing the smallest divisor
# of each index (this will be "2" ½ the time, "3" ⅙ of the time, etc.)
strings = Series(
    [ 
        sha256(
            str(
                # Find the smallest integer divisor of i
                next(
                    j
                    for j in range(2,i+2)
                    if i%j == 0
                )
            ) \
            .encode()
        ) \
        .hexdigest() \
        [:5]
        for i in range(2, R+2)
    ],
    name='strings',
)

# Assemble these columns into a DataFrame:
l = concat([floats, bools, strings], axis=1).set_index(index)
l


# Make a second test DataFrame, with a few changes:

# In[23]:


from numpy import nan
r = l.copy()
r.loc['c','bools'] = True
r = r[r.index!='k']
r.loc['o','strings'] = nan
r.loc['o','floats'] = 0
r.loc['p','strings'] = ''
r


# ### Build a `Diff` object: <a id="diff"></a>

# In[24]:


d = Diff(l, r)
d


# The default display is the `d.clean` DataFrame, which renders only rows and columns where at least one change occurred, but with pairs of empty strings (for both `l` and `r`) at coordinates where nothing changed.
# 
# This allows detecting values that went from non-`NaN` to `NaN` (see (`o`,`strings`)), non-empty to empty (see (`p`,`strings`)), etc.

# The `changed` member shows all values for rows and cols where anything changed:

# In[25]:


d.changed


# This is similar to the `clean` DataFrame, except that coordinates where nothing changed display the (identical) values in both `l` and `r` sub-columns (as opposed to in `clean`, where they are replaced with the empty string).

# The full, joined DataFrame (with `l`/`r` sub-columns for each column) is in the `df` member:

# In[26]:


d.df

