from dataclasses import dataclass
from re import fullmatch


@dataclass
class RGB:
    r: float
    g: float
    b: float

    @staticmethod
    def from_css(css):
        if css[0] == '#':
            css = css[1:]

        m = fullmatch(r'(?P<r>[\da-f]{2})(?P<g>[\da-f]{2})(?P<b>[\da-f]{2})', css)
        if m:
            pcs = [ m['r'], m['g'], m['b'] ]
        else:
            m = fullmatch(r'(?P<r>[\da-f])(?P<g>[\da-f])(?P<b>[\da-f])', css)
            assert m
            pcs = [ m['r'] * 2, m['g'] * 2, m['b'] * 2 ]

        r, g, b = [ int(s, 16) for s in pcs ]
        return RGB(r, g, b)

    def __add__(l, r):
        return RGB(l.r + r.r, l.g + r.g, l.b + r.b)

    def __sub__(l, r):
        return RGB(l.r - r.r, l.g - r.g, l.b - r.b)

    def __mul__(self, f):
        return RGB(self.r * f, self.g * f, self.b * f)

    def __truediv__(self, f):
        return RGB(self.r / f, self.g / f, self.b / f)

    @property
    def css(self):
        return '#%s' % ''.join([ '%02x' % int(f) for f in [ self.r, self.g, self.b ]])


def color_interp(l_idx, l_n, r_colors):
    r_n = len(r_colors) - 1
    r_pos = l_idx / l_n * r_n
    r_idx = int(r_pos)
    r_rem = r_pos - r_idx
    r_colors = [ RGB.from_css(r_color) for r_color in r_colors ]
    cur = r_colors[r_idx]
    if r_rem == 0:
        return cur.css
    nxt = r_colors[r_idx + 1]
    color = cur + (nxt - cur) * r_rem
    return color.css


def colors_lengthen(colors, n):
    return [ color_interp(i, n - 1, colors) for i in range(n) ]


def swatches(colors, sep=' ', width=6):
    """Adapted from https://gist.github.com/wmayner/9b099a0e4a5f8e94f0c6ab2f570187a5"""
    from IPython.display import Markdown, display
    display(Markdown(sep.join(
        f'<span style="font-family: monospace">{color} <span style="color: {color}">{chr(9608)*width}</span></span>'
        for color in colors
    )))
