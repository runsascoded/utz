
def i2s(v, chars):
    N = len(chars)
    base = 1
    bases = []
    ceiling = 1
    while ceiling <= v:
        bases.append(base)
        base *= N
        ceiling += base

    chrs = ''
    n = v - ceiling
    for base in reversed(bases):
        i = n // base
        n -= i*base
        ch = chars[i]
        chrs += ch

    return chrs


def s2i(s, ints):
    sz = len(s)
    N = len(ints)
    n = (N**sz-1)//(N-1)
    base = 1
    for ch in reversed(s):
        i = ints[ch]
        n += i*base
        base *= N
    return n


def b2s(b, chars):
    n = 0
    for byte in b:
        n *= 256
        n += byte
    return i2s(n, chars)


class Converter:
    '''Base-class for converters between non-negative integers and strings comprised of a given alphabet

    See "base" 62, 64, and 90 versions below, but note that they work differently than e.g. standard base64; these
    encodings are isomorphisms between all natural numbers and all strings:
    - 0 ⟺ ''
    - [1,N) ⟺ <1-char strings>
    - [N, N²+N) ⟺ <2-char strings>
    - [N²+N, N³+N²+N) ⟺ <3-char strings>
    - etc.
    '''
    I2S = None

    def __init__(self):
        self.S2I = {ch:i for i, ch in enumerate(self.I2S)}

    def __call__(self, v):
        if isinstance(v, str):
            return s2i(v, self.S2I)
        elif isinstance(v, int):
            return i2s(v, self.I2S)
        elif isinstance(v, bytes):
            return b2s(v, self.I2S)
        else:
            raise ValueError(f'Unrecognized type ({type(v)}): {v}')


class B62(Converter): I2S = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
b62 = B62()


class B64(Converter): I2S = '+/0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
b64 = B64()


class B90(Converter): I2S = '!"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz'
b90 = B90()
