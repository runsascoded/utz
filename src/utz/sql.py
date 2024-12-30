#!/usr/bin/env python

import dask.dataframe as dd
import pandas as pd
from os import cpu_count


def to_sql(
    table, name, db_path, force=False,
):
    if_exists = 'replace' if force else 'fail'
    table.to_sql(name, db_path, if_exists=if_exists)
    if isinstance(table, dd.DataFrame):
        divisions = pd.Series(table.divisions, name='divisions')
        divisions.to_sql(f'{name}/divisions', db_path, if_exists=if_exists)


def from_sql(
    name, db_path, index_col=None, dask=True,
):
    if index_col is None:
        index_col = 'index'

    if dask:
        divisions = pd.read_sql_table(f'{name}/divisions', db_path, index_col='index').divisions.tolist()
        table = dd.read_sql_table(name, db_path, index_col=index_col, divisions=divisions)
    else:
        table = pd.read_sql_table(name, db_path, index_col=index_col)

    return table


def table_to_sql(
    table_name,
    db_path,
    index_col=None,
    dask=True,
    npartitions=-1,
    table_path=None,
    force_db_refresh=False,
    **kwargs
):
    from sqlalchemy import create_engine
    engine = create_engine(db_path)

    if npartitions is not None:
        if npartitions <= 0:
            npartitions = cpu_count()

    if force_db_refresh or not engine.has_table(table_name):
        if not table_path:
            raise ValueError(f'table_path required in order to compute table {table_name}')
        print(f'Creating db table: {table_name}')
        if_exists = ('replace' if force_db_refresh else 'fail')
        if dask:
            csv = dd.read_csv(table_path, **kwargs)
            if npartitions is not None:
                csv = csv.repartition(npartitions=npartitions)
            if index_col is None:
                # Force Dask to get a cross-partition default integer autoinc index
                csv = csv.reset_index().set_index('index')
        else:
            csv = pd.read_csv(table_path, **kwargs)
        
        if index_col is not None:
            csv = csv.set_index(index_col)

        to_sql(csv, table_name, db_path, force=force_db_refresh)

    return from_sql(table_name, db_path, index_col=index_col, dask=dask)
