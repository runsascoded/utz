from utz import parametrize
from dataclasses import dataclass


def fn(f: float, fmt: str) -> str:
    """Example function, to be tested with ``Case``s below."""
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
    """Example test, "paraametrized" by several ``Cases``s."""
    assert fn(f, fmt) == expected
