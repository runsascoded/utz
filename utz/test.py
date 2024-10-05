from contextlib import contextmanager
from dataclasses import asdict, fields
from inspect import getfullargspec
from typing import List, TypeVar, Tuple, Type, Optional, Union

Case = TypeVar('Case')  # Dataclass with an `id: str`


def parametrize(*cases: Case | List[Case] | Tuple[Case, ...]):
    """"Parametrize [sic]" a test with a list of test "Case" objects (instances of a dataclass).

    The cases are expected to have an ``id: str`` field, which is used as the test-case "ID".

    Adapted from https://github.com/single-cell-data/TileDB-SOMA/blob/1.14.2/apis/python/tests/parametrize_cases.py.
    """
    cases = [
        case
        for arg in cases
        for case in (arg if isinstance(arg, (list, tuple)) else [arg])
    ]
    cls = cases[0].__class__
    for case in cases:
        if case.__class__ is not cls:
            raise ValueError(
                f"Expected all cases to be of type {cls}, but found {case.__class__}"
            )

    def wrapper(fn):
        """Parameterize a test ``fn``, converting the ``cases`` above to pytest-style "ID"s and
        kwarg keys/values.

        The wrapped function's argument list can be any subset of the "Case" dataclass' fields;
        fields it doesn't "declare" are omitted.
        """
        # Test-case IDs
        ids = [ case.id for case in cases ]

        # Convert each case to a "values" array; also filter and reorder to match kwargs expected
        # by the wrapped "test_*" function.
        spec = getfullargspec(fn)
        field_names = [ f.name for f in fields(cls) ]
        names = [ arg for arg in spec.args if arg in field_names ]
        values = [
            { name: rt_dict[name] for name in names }.values()
            for rt_dict in [ asdict(case) for case in cases ]
        ]

        import pytest

        # Delegate to PyTest `parametrize`
        return pytest.mark.parametrize(
            names,  # kwarg names
            values,  # arg value lists
            ids=ids,  # test-case names
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
