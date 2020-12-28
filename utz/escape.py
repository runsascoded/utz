
import re
from re import escape, finditer


def split(s, ch):
    idx = 0
    strs = []
    nxt = ''
    escaped_ch = escape(ch)
    rgx = r'(?:\\+%s?|%s)' % (escaped_ch, escaped_ch)
    matches = list(finditer(rgx, s))
    for m in matches:
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
        elif span:
            raise RuntimeError(f'Unexpected end to span {s[start:end]}: {span}; {s=}, {idx=}, {m=}')
        assert idx == end
    nxt += s[idx:]
    strs.append(nxt)
    return strs


def join(strs, ch):
    escaped_ch = escape(ch)
    def esc(s):
        s = re.sub(r'\\', r'\\\\', s)
        s = re.sub(escaped_ch, '\\' + escaped_ch, s)
        return s

    return ch.join(esc(s) for s in strs)
