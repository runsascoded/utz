#!/usr/bin/env python
# coding: utf-8

# # Pandas imports / aliases / helpers

# In[ ]:


from dateutil.parser import parse
from pathlib import Path

from numpy import nan, array, ndarray

import pandas as pd
from pandas import     concat, DataFrame as DF, Series,     isna,     read_csv, read_excel, read_json, read_parquet, read_sql, read_sql_query, read_sql_table,     date_range, to_datetime as to_dt, Timedelta as Δ, NaT


# ## Config

# In[ ]:


def display(r=None, c=None):
    '''Set the default number of rows and columns for Pandas to display'''
    if r:
        pd.options.display.max_rows = r
    if c:
        pd.options.display.max_columns = c

display(100, 100)


# ## Concat / Creation

# In[ ]:


def sxs(*dfs, **kwargs):
    '''Concat some DataFrames "side by side"'''
    return concat(dfs, axis=1, **kwargs)


# ## Counting

# In[ ]:


def series_counts(series, ascending = None):
    df_new = DF(series.value_counts())
    column_name = df_new.columns[0]
    df_new['index'] = df_new.index
    ascending = [False,True] if ascending is None else ascending
    return df_new.sort_values(by = [column_name,'index'], ascending = ascending)[column_name]


# In[ ]:


def sort_by_series(df, series):
    tmp_col_name = series.name or '_'
    while tmp_col_name in df:
        tmp_col_name=f'_{tmp_col_name}'

    if isinstance(series, str):
        series = df[series]

    df2 = df.copy()
    df2[tmp_col_name] = series
    return         df2         .sort_values(tmp_col_name)         .drop(columns=tmp_col_name)


# ## File paths

# In[ ]:


def file_dict(path):
    name = path.name
    pieces = name.rsplit('.', 1)
    if len(pieces) == 2:
        base, xtn = pieces
    else:
        [ base ] = pieces
        xtn = nan
    
    return dict(parent=path.parent, name=name, base=base, xtn=xtn, exists=path.exists())


def annotate_files(files):
    if files.empty:
        dtypes = {
            'parent': object,
            'name': str,
            'base': str,
            'xtn': str,
            'exists': bool,
        }
        return DF([], index=files, columns=dtypes.keys()).astype(dtypes)
    else:
        extra = files.apply(file_dict).apply(Series)
        files = sxs(files, extra).set_index(files.name)
        return files


def load_files(files, glob=None, name=None):
    if isinstance(files, Path):
        name = name or 'path'
        files = Series(files.glob(glob), name=name, dtype=object)
    else:
        name = name or files.name
    files = annotate_files(files)
    return files


# ## Dates

# In[ ]:


def expand_date(s):
    d = parse(s).date()
    return dict(date=d, year=d.year, month=d.month, day=d.day)
