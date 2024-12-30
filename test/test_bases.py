from utz.bases import b64


def test_ints_strs():
    cases = {
        0: '',
        1: '+',
        2: '/',
        63: 'y',
        64: 'z',
        65: '++',
        66: '+/',
        128: '+z',
        129: '/+',
        0x103f: 'zy',
        0x1040: 'zz',
        0x1041: '+++',
    }
    for i, s in cases.items():
        assert b64(i) == s
        assert b64(s) == i


def test_bytes():
    assert b64(bytes([])) == ''
    assert b64(bytes([ 1 ])) == '+'
    assert b64(bytes([ 1, 2 ])) == '1/'
    assert b64(bytes([ 1, 2, 3 ])) == 'D50'
