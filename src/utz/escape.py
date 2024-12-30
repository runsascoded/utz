import re
from re import escape, finditer
from typing import Sequence


def split(s: str, ch: str, max: int = 0):
    """Split ``s`` on character ``ch``, un-escaping backslash-escaped instances of ``ch`` (and
    un-escaping double-backslashes to single backslashes).

    If ``max`` is passed, ``max`` groups will be extracted, and a final ``(max+1)``-th group will
    be appended to the returned list, containing the remainder of ``s`` (with no un-escaping
    performed).
    """
    idx = 0
    strs = []
    n = 0
    nxt = ''
    escaped_ch = escape(ch)
    rgx = r'(?:\\+%s?|%s)' % (escaped_ch, escaped_ch)
    for m in finditer(rgx, s):
        start, end = m.span()
        nxt += s[idx:start]
        idx = start
        span = s[start:end]
        while span.startswith(r'\\'):
            nxt += '\\'
            span = span[2:]
            idx += 2
        if span == '\\' + ch:
            nxt += ch
            idx += 2
        elif span == ch:
            strs.append(nxt)
            nxt = ''
            idx += 1
            n += 1
            if max == n:
                break
        elif span:
            raise RuntimeError(f'Unexpected end to span {s[start:end]}: {span}; {s=}, {idx=}, {m=}')
        assert idx == end
    nxt += s[idx:]
    strs.append(nxt)
    return strs


def join(strs: Sequence[str], ch: str, max: int = 0):
    """Escape and ``ch``-join a list of strings; inverse of ``split`` above.

    In the returned string:
    - backslashes are escaped (turned into double-backslashes)
    - instances of `ch` are escaped (preceded by a backslash)

    If ``max`` is passed and ``len(strs) == max + 1``, the final element of ``strs`` is taken to
    have been a raw group from a corresponding call to split(…, max=…), and is directly appended to
    the final string (skipping the escaping steps above).
    """
    escaped_ch = escape(ch)

    def esc(s):
        s = re.sub(r'\\', r'\\\\', s)
        s = re.sub(escaped_ch, '\\' + escaped_ch, s)
        return s

    if max and len(strs) > max:
        if len(strs) > max + 1:
            raise ValueError(f'{len(strs)} strs > {max}+1')
        return ch.join(esc(s) for s in strs[:max]) + ch + strs[max]
    else:
        return ch.join(esc(s) for s in strs)


def esc(s: str, ch: str):
    """Escape instances of character ``ch`` in string ``s`` by preceding them with a backslash."""
    return join([s], ch)
