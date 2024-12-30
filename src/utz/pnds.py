# # Pandas imports / aliases / helpers
from functools import partial
from os import environ, remove
from os.path import exists, isdir, splitext
from pathlib import Path
from shutil import rmtree

from utz.imports import _try

with _try:
    from dateutil.parser import parse
with _try:
    from numpy import nan, array, ndarray
    import pandas as pd
    from pandas import \
        concat, \
        DataFrame as DF, \
        Series, \
        isna, \
        read_csv, read_excel, read_json, read_parquet, read_sql, read_sql_query, read_sql_table, \
        date_range, to_datetime as to_dt, Timedelta as Δ, NaT, \
        get_option, set_option

    # ## crosstab
    xtab = pd.crosstab
    xtabn = partial(pd.crosstab, dropna=False)

    def display(r=None, c=None):
        """Set the default number of rows and columns for Pandas to display"""
        if r:
            pd.options.display.max_rows = r
        if c:
            pd.options.display.max_columns = c

    display(
        int(environ.get("PANDAS_DEFAULT_DISPLAY_ROWS", "100")),
        int(environ.get("PANDAS_DEFAULT_DISPLAY_COLS", "100")),
    )


# ## value_counts
def vc(p, **kwargs):
    return p.value_counts(**kwargs)


def vcs(p, **kwargs):
    return p.value_counts(**kwargs).sort_index()


def vcn(p, **kwargs):
    return p.value_counts(dropna=False, **kwargs)


def vcns(p, **kwargs):
    return p.value_counts(dropna=False, **kwargs).sort_index()


def vcvc(p, **kwargs):
    return p.value_counts(**kwargs).value_counts()


def vcvcs(p, **kwargs):
    return p.value_counts(**kwargs).value_counts().sort_index()


# ## Concat / Creation

def sxs(*dfs, **kwargs):
    """Concat some DataFrames "side by side\""""
    return concat(dfs, axis=1, **kwargs)


# ## Counting

def series_counts(series, ascending = None):
    df_new = DF(series.value_counts())
    column_name = df_new.columns[0]
    df_new['index'] = df_new.index
    ascending = [False,True] if ascending is None else ascending
    return df_new.sort_values(by = [column_name,'index'], ascending = ascending)[column_name]


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

def file_dict(path: Path):
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

def expand_date(s):
    d = parse(s).date()
    return dict(date=d, year=d.year, month=d.month, day=d.day)


def to_parquet(df, out_path, verify_extension=True, *args, **kwargs):
    if verify_extension:
        _, extension = splitext(out_path)
        if extension != '.parquet':
            raise Exception(f"Refusing to write parquet dataset to non-parquet path {out_path}")

    if exists(out_path):
        if isdir(out_path):
            rmtree(out_path)
        else:
            remove(out_path)

    return df.to_parquet(out_path, *args, **kwargs)
