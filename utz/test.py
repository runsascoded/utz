import dataclasses
from contextlib import contextmanager
from dataclasses import asdict, replace
from inspect import getfullargspec, getmembers
from typing import TypeVar, Type, Optional, Union, Iterable, Any

Case = TypeVar('Case')  # Dataclass type


def parametrize(*cases: Case | Iterable[Case], **sweeps):
    """"Parametrize" [sic] a test function with a list of test-"case"s (instances of a dataclass).

    Fields and `@property``s of each case are passed as keyword arguments to the test function, but
    any that don't match the test function's argument names are ignored. Test functions can also
    declare an argument named ``case`` to receive the full ``Case`` object.

    ``id``s (used by pytest for display purposes, for each test case) are taken from each
    ``Case``'s ```id`` attribute, if present. Otherwise, an ID is generated from the non-default
    dataclass field values.

    Adapted/Extended from https://github.com/single-cell-data/TileDB-SOMA/blob/1.14.2/apis/python/tests/parametrize_cases.py.
    """
    # Flatten the ``cases`` varargs. Sometimes it's convenient to pass a Generator as a single arg
    # to ``parametrize`` (e.g. to construct parameter sweeps with a loop), or otherwise build one
    # or more ``Sequence``s of ``Case``s to pass to ``parametrize``.
    if len(cases) == 1 and isinstance(cases[0], list):
        # Special-case, to save many redundant traversals when ``sweeps`` are provided (see
        # recursive ``sweeps`` unroll block below)
        cases = cases[0]
    else:
        cases = [
            case
            for arg in cases
            for case in (arg if isinstance(arg, Iterable) else [arg])
        ]

    if sweeps:
        k = next(iter(sweeps.keys()))
        vs = sweeps.pop(k)
        return parametrize(
            [
                replace(case, **{k: v})
                for case in cases
                for v in vs
            ],
            **sweeps,
        )

    # Verify and extract a single ``class`` type from ``cases``.
    cls = cases[0].__class__
    for case in cases:
        if case.__class__ is not cls:
            raise ValueError(
                f"Expected all cases to be of type {cls}, but found {case.__class__}"
            )

    def wrapper(fn):
        """Parameterize a test ``fn``, converting the ``cases`` above to pytest-style "ID"s and
        kwarg keys/values.

        The wrapped function's argument list can be any subset of the "Case" dataclass' fields and
        ``@property``s; fields not "declared" by the test function are not passed.
        """
        # Dicts of ``@property`` and ``@dataclass`` fields
        props = {
            name: prop
            for name, prop
            in getmembers(cls, lambda o: isinstance(o, property))
        }
        fields = { f.name: f for f in dataclasses.fields(cls) }

        def get_case_id(case) -> str:
            """Generate a test-case ID from a "Case" object.

            Concatenate string reprs of all non-default field values, separated by hyphens."""
            case_id = getattr(case, 'id', None)
            if case_id:
                return case_id
            non_default_vals = []
            case_kvs = asdict(case)
            for name, field in fields.items():
                val = case_kvs[name]
                if val == field.default:
                    # Skip fields that match the default value
                    # (Fields with no default are always included / never skipped)
                    continue
                non_default_vals.append(f"{val}")
            return '-'.join(non_default_vals)

        # Test-case IDs
        ids = [ get_case_id(case) for case in cases ]

        # Full list of fields that can be passed to the test function
        # "case" is the dataclass instance itself
        cls_names: list[str] = list(fields.keys()) + list(props.keys()) + ['case']
        # Intersect the test function's argument names with the eligible field names above
        spec = getfullargspec(fn)
        fn_arg_names: list[str] = [ arg for arg in spec.args if arg in cls_names ]
        # Dicts of all eligible field keys and values, one per case
        cases_kvs: list[dict[str, Any]] = [
            dict(
                **asdict(case),
                **{
                    name: prop.fget(case)
                    for name, prop
                    in props.items()
                },
                case=case,
            )
            for case in cases
        ]
        # Filter case dicts to just the values corresponding to keys that the test function accepts
        values: list[list[Any]] = [
            [ case_kvs[name] for name in fn_arg_names ]
            for case_kvs in cases_kvs
        ]

        import pytest

        # Delegate to PyTest `parametrize`
        return pytest.mark.parametrize(
            fn_arg_names,  # list of kwarg ("key") names
            values,        # list of arg-value lists
            ids=ids,       # list of test-case names
        )(fn)

    return wrapper


@contextmanager
def raises(
    exc_type: Type[Exception],
    match: Union[str, list[str], None] = None,
    exact: Optional[bool] = None,
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
        assert str(exc.value) in msgs
    else:
        with pytest.raises(exc_type, *args, match=match, **kwargs):
            yield
