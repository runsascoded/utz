from __future__ import annotations

import dataclasses
from contextlib import contextmanager
from dataclasses import replace
from inspect import getfullargspec, getmembers, isfunction
from typing import Any, Callable, Iterable, TypeVar, Union

# Dataclass type
Case = TypeVar('Case')
# Input field value, output string repr (for test-case "ID"s; ``None`` ⟹ omit)
IdFmtField = Callable[[Any], Union[str, None]]
# Format function for each dataclass field.
IdFmts = dict[str, IdFmtField]
# Unprocessed version of ``IdFmts``, supports key-tuple shorthand for assigning a format-fn value
# to multiple keys.
IdFmtsInput = dict[Union[str, tuple[str]], IdFmtField]


def default_field_fmt(val: Any) -> str:
    """Default field-formatting function for ``Case`` IDs."""
    return f"{val}"


def normalize(id_fmts: IdFmtsInput) -> IdFmts:
    return {
        key: fn
        for keys, fn in id_fmts.items()
        for key in (keys if isinstance(keys, tuple) else [keys])
    }


def parametrize(
    *cases: Case | Iterable[Case],
    delim: str = "-",
    id_fmts: dict[str | tuple[str], IdFmtField] | None = None,
    **sweeps,
):
    """"Parametrize" [sic] a test function with a list of test-"case"s (instances of a dataclass).

    Fields, `@property``s, and methods of each ``case`` may be passed as keyword arguments to the
    test function, if it declares arguments with matching names. Test functions can also declare an
     argument named ``case`` to receive the full ``Case`` object.

    Test-case "ID"s (used by pytest for display and lookup purposes, for each test case) are taken
    from each ``Case``'s ```id`` attribute, if present. Otherwise, an ID is generated from the
    dataclass-fields whose values differ among ``cases``.

    ``**sweeps`` supports parameter sweeps, where ``cases`` is "Cartesian product"-ed against a
     series of ``(str, list[Any])`` pairs (where the "key" is a dataclass-field name).

    Adapted/Extended from https://github.com/single-cell-data/TileDB-SOMA/blob/1.14.2/apis/python/tests/parametrize_cases.py.
    """
    # Flatten the ``cases`` varargs. Sometimes it's convenient to pass a Generator as a single arg
    # to ``parametrize`` (e.g. to construct parameter sweeps with a loop), or otherwise build one
    # or more ``Sequence``s of ``Case``s to pass to ``parametrize``.
    if len(cases) == 1 and isinstance(cases[0], list):
        # Special-case, to save ``O(N)`` redundant traversals when N ``sweeps`` are provided (see
        # recursive ``sweeps`` unroll block below)
        cases = cases[0]
    else:
        cases = [
            case
            for arg in cases
            for case in (arg if isinstance(arg, Iterable) else [arg])
        ]

    if sweeps:
        # Pop first ``(key,vals)`` pair
        key = next(iter(sweeps.keys()))
        vals = sweeps.pop(key)
        # Sweep over ``vals``, recurse until no ``sweeps`` remain
        return parametrize(
            [
                replace(case, **{ key: val })
                for case in cases
                for val in vals
            ],
            delim=delim,
            id_fmts=id_fmts,
            **sweeps,
        )

    # Verify and extract a single ``class`` type from ``cases``.
    cls = cases[0].__class__
    for case in cases:
        if case.__class__ is not cls:
            raise ValueError(
                f"Expected all cases to be of type {cls}, but found {case.__class__}"
            )

    # Dicts of ``@property``s, methods, and ``@dataclass`` fields.
    props = {
        name: prop
        for name, prop
        in getmembers(cls, lambda o: isinstance(o, property))
    }
    methods = {
        name: method
        for name, method
        in getmembers(cls, isfunction)
        if not name.startswith('_')
    }
    fields = { f.name: f for f in dataclasses.fields(cls) }

    # Find fields that differ among the ``cases``; used for auto-generating test-case IDs
    differing_fields = {}
    if cases:
        case0, *rest = cases
        for name, field in fields.items():
            val0 = getattr(case0, name)
            for case in rest:
                val = getattr(case, name)
                if val != val0:
                    differing_fields[name] = field
                    break

    id_fmts = normalize(id_fmts) if id_fmts else {}
    _id_fmts = normalize(getattr(cls, '_id_fmts', {}))
    id_fmts = {
        name: id_fmts.get(name, _id_fmts.get(name, default_field_fmt))
        for name in differing_fields.keys()
    }

    def wrapper(fn):
        """Parameterize a test ``fn``, converting the ``cases`` above to "ID"s, key,
        and value lists that Pytest expects.

        The wrapped function's argument list can be any subset of the "Case" dataclass' fields,
        ``@property``s, and methods. Fields not "declared" by the test function are not passed.
        """
        def get_case_id(case: Case) -> str:
            """Generate a test-case ID from a "Case" object.

            Hyphen-delimited string reprs of all fields that differ among ``cases``."""
            case_id = getattr(case, 'id', None)
            if case_id:
                return case_id
            id_vals = []
            for name, field in differing_fields.items():
                val = getattr(case, name)
                fmt_fn = id_fmts[name]
                val_str = fmt_fn(val) if fmt_fn else None
                if val_str is not None:
                    id_vals.append(val_str)
            return delim.join(id_vals)

        # Test-case IDs, used by Pytest for display and lookup purposes
        ids = [ get_case_id(case) for case in cases ]

        # Full list of fields that can be passed to the test function
        # "case" is the dataclass instance itself
        cls_names: list[str] = [
            *fields.keys(),
            *props.keys(),
            *methods.keys(),
            'case',
        ]

        # Intersect the test function's argument names with the eligible field names above
        spec = getfullargspec(fn)
        fn_arg_names: list[str] = [
            arg
            for arg in spec.args
            if arg in cls_names
        ]

        # Dicts of keys and values, one per ``case``, for the keys (kwargs) expected by ``fn``
        # cases_kvs: list[dict[str, Any]] = []
        values_lists: list[list[Any]] = []
        for case in cases:
            values = []
            for name in fn_arg_names:
                if name == 'case':
                    values.append(case)
                elif name in fields:
                    values.append(getattr(case, name))
                elif name in props:
                    values.append(props[name].fget(case))
                elif name in methods:
                    values.append(getattr(case, name))
            values_lists.append(values)

        import pytest

        # Delegate to PyTest `parametrize`
        return pytest.mark.parametrize(
            fn_arg_names,  # List of kwarg ("key") names that match eligible ``Case`` class members
            values_lists,  # List of arg-value lists, one per test ``case``
            ids=ids,       # List of test-case names
        )(fn)

    return wrapper


@contextmanager
def raises(
    exc_type: type[Exception],
    match: str | list[str] | None = None,
    exact: bool | None = None,
    *args,
    **kwargs,
):
    """``pytest.raises`` wrapper, 2nd arg can be ``match`` regex or ``list`` of exact-match candidates."""
    import pytest
    if exact:
        if isinstance(match, str):
            match = [match]
    if isinstance(match, list):
        msgs = match
        with pytest.raises(exc_type) as exc:
            yield
        expected = str(exc.value)
        assert expected in msgs, f'Expected "{expected}" to be in {msgs}'
    else:
        with pytest.raises(exc_type, *args, match=match, **kwargs):
            yield
