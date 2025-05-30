from __future__ import annotations

from contextlib import nullcontext, contextmanager
from dataclasses import dataclass
from os import makedirs
from os.path import dirname, exists, relpath
from shutil import rmtree
from tempfile import NamedTemporaryFile
from typing import Any

from utz import parametrize


def fn(f: float, fmt: str) -> str:
    """Example function, to be tested with ``case``s below."""
    return f"{f:{fmt}}"


@dataclass
class case:
    """Container for a test-case; float, format, and expected output."""
    f: float
    fmt: str
    expected: str

    @property
    def id(self):
        return f"fmt-{self.f}-{self.fmt}"


@parametrize(
    case(1.23, "0.1f", "1.2"),
    case(123.456, "0.1e", "1.2e+02"),
    case(-123.456, ".0f", "-123"),
)
def test_fn(f, fmt, expected):
    """Example test, "parametrized" by several ``Cases``s."""
    assert fn(f, fmt) == expected


@parametrize(
    case(1.23, "0.1f", "1.2"),
)
def test_case_id(case, request):
    """Test that the ``id`` property of a ``Case`` is used as the test's ID.

    Also, an argument named ``case`` is populated with the full ``Case`` object.

    ``request`` is a special arg-name that Pytest populates with metadata about the current test case.
    """
    assert case.f == 1.23
    assert case.fmt == "0.1f"
    assert case.id == "fmt-1.23-0.1f"
    assert request.node.name == 'test_case_id[fmt-1.23-0.1f]'


def pow2(n: int) -> int:
    """Example function to be tested by ``case2``s below."""
    return n ** 2


@dataclass
class case2:
    n: int
    # Example field with a default value, omitted from test IDs unless set to a non-default value
    extra: str = "extra str"

    @property
    def sq(self):
        return self.n * self.n


@parametrize(
    case2(11),
    case2(22, extra="extra str"),
)
def test_case2_id(case, request):
    """Test that an ``id`` is autogenerated for "case" classes that don't define one.

    Fields are included iff their value doesn't match the default value (or there is no default value).
    """
    assert request.node.name == f'test_case2_id[{case.n}]'


@parametrize(
    case2(11, extra="AAAA"),
)
def test_case2_id_extra(request):
    """Test that autogenerated ``id``s incorporate non-default field values."""
    assert request.node.name == 'test_case2_id_extra[]'


@parametrize(
    case2(n)
    for n in range(10)
)
def test_pow2(n, sq):
    """Example unpacking a `@property` field (``sq``) from a "case" class."""
    assert pow2(n) == sq


def json_dump(obj: Any, path: str):
    """Example function to be tested by ``case3``s below."""
    import json
    with open(path, 'w') as f:
        json.dump(obj, f)


def json_load(path: str) -> Any:
    """Example function to be tested by ``case3``s below."""
    import json
    with open(path, 'r') as f:
        return json.load(f)


@dataclass
class case3:
    obj: Any  # Object to JSON-serde
    dir: str | None = None  # Perform JSON-serde roundtrip in this directory
    suffix: str | None = None  # Suffix for the temporary file

    @property
    @contextmanager
    def dir_ctx(self):
        if not self.dir:
            with nullcontext():
                yield
        else:
            rm_dir = False
            if not exists(self.dir):
                makedirs(self.dir)
                rm_dir = True
            try:
                yield self.dir
            finally:
                if rm_dir:
                    rmtree(self.dir)

    def roundtrip(self) -> Any:
        """JSON serialization round-trip."""
        with self.dir_ctx:
            with NamedTemporaryFile(dir=self.dir, suffix=self.suffix) as f:
                path = f.name
                if self.dir:
                    assert dirname(relpath(path)) == self.dir
                json_dump(self.obj, path)
                return json_load(path)


@parametrize(
    case3({'a': 1}),
    case3([ 11, 22, 33 ]),
    dir=[ None, 'tmp/test_json_roundtrip', ],
    suffix=[ None, ".json", ],
    # Custom field-formatters for pytest "ID" strings; see ``ids``
    id_fmts={
        'obj': lambda obj: (
            ','.join(f'{k}={v}' for k, v in obj.items())
            if isinstance(obj, dict)
            else str(obj).replace(' ', '')
        ),
        ('dir', 'suffix'): lambda s: str(s) if s else None,  # None ⟹ omit from ID
    },
)
def test_json_roundtrip_sweeps(obj, roundtrip, request):
    """Example testing a function that writes and reads a JSON file.

    Also reflects over the "swept" (kwargs) arguments above, verifying that 8 test cases are
    generated, having the expected IDs."""
    assert obj == roundtrip()

    # Swept test-case IDs
    ids = [
        item.name
        for item in request.session.items
        if item.originalname == 'test_json_roundtrip_sweeps'
    ]
    # Current test-case ID
    cur = request.node.name
    assert cur in ids
    assert ids == [
        'test_json_roundtrip_sweeps[a=1]',
        'test_json_roundtrip_sweeps[a=1-.json]',
        'test_json_roundtrip_sweeps[a=1-tmp/test_json_roundtrip]',
        'test_json_roundtrip_sweeps[a=1-tmp/test_json_roundtrip-.json]',
        'test_json_roundtrip_sweeps[[11,22,33]]',
        'test_json_roundtrip_sweeps[[11,22,33]-.json]',
        'test_json_roundtrip_sweeps[[11,22,33]-tmp/test_json_roundtrip]',
        'test_json_roundtrip_sweeps[[11,22,33]-tmp/test_json_roundtrip-.json]',
    ]


@parametrize(
    case3('aaa', dir='tmp/test_json_roundtrip'),
)
def test_contextmanager(case, dir_ctx):
    """Example testing a context manager."""
    assert not exists(case.dir)
    with dir_ctx as tmpdir:
        assert exists(case.dir)
        assert case.dir == tmpdir
    assert not exists(case.dir)
