#!/usr/bin/env python
# coding: utf-8

from pandas import Series

def singleton(elems, fn=None, empty_ok=False, name='elems', dedupe=True):
    if isinstance(elems, Series):
        elems = elems.unique().tolist()
    elif isinstance(elems, dict):
        elems = elems.items()
    if fn:
        elems = [ elem for elem in elems if fn(elem) ]
    else:
        if dedupe:
            elems = set(elems)
    if not elems:
        if empty_ok:
            return None
        raise ValueError(f'No {name} found')
    if len(elems) > 1:
        raise ValueError(f'{len(elems)} {name} found: {",".join([ str(elem) for elem in list(elems)[:10] ])}')
    [ elem ] = elems
    return elem


from math import exp, log
from numpy import nan
from sys import stderr

def coerce(value, choices, ε=1e-2, multi_ok=False, errors='raise',warn=True):
    assert errors in ['raise','coerce','ignore',]
    elems = sorted(
        [ 
            dict(
                ratio=abs(log(value / choice)),
                choice=choice
            )
            for choice in choices
        ],
        key=lambda r: r['ratio']
    )
    log_ε = log(1+ε)
    valids = [ elem for elem in elems if elem['ratio'] <= log_ε ]
    best = elems[0]
    choice = best['choice']
    if not valids:
        msg = f'Best choice {choice} for value {value} has error {exp(best["ratio"])-1} > {ε}'
        if errors == 'raise':
            raise ValueError(msg)
        if warn:
            stderr.write(msg + '\n')
        if errors == 'coerce':
            return nan
        else:
            return value
    if len(valids) > 1 and not multi_ok:
        raise ValueError(
            '%d choices passed ε<%f filter:\n\t%s' % (
                len(valids),
                ε,
                "\n\t".join([ str(r["choice"]) for r in valids ]),
            )
        )
    return best['choice']        

