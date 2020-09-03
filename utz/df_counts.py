#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from dask import compute
import dask.dataframe as dd
import pandas as pd

def df_counts(df):
    '''Get notnull and unique counts for each column in a DataFrame'''
    dask = isinstance(df, dd.DataFrame)
    if dask:
        nuniques = compute(*[ df[k].nunique() for k in df ])
        col_counts = pd.DataFrame(
            [
                { 'col':col, 'nunique':nunique }
                for col, nunique
                in zip(df.columns, nuniques)
            ]
        ) \
        .set_index('col')

        notnulls = df.notnull().sum().compute().rename('notnull')

        return pd.concat([notnulls, col_counts], axis=1)
    else:
        col_counts = pd.DataFrame(
            [
                { 'col':k, 'nunique':df[k].nunique() }
                for k in df
            ]
        ) \
        .astype({'nunique':int}) \
        .set_index('col')

        notnulls = df.notnull().sum().rename('notnull')

        return pd.concat([notnulls, col_counts], axis=1)


# In[ ]:


def col_counts(df, *cols):
    counts = df.groupby(list(cols)).size()
    counts = counts[counts > 1]
    return counts.compute().sort_values()

