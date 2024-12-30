from functools import partial

from utz.escape import split, join, esc


def test_split_join():
    def check(s, strs, ch, **kwargs):
        assert split(s, ch, **kwargs) == strs
        assert join(strs, ch, **kwargs) == s

    chk = partial(check, ch=':')

    chk('', [''])
    chk('a', ['a'])
    chk('aaa', ['aaa'])
    chk('a:b', ['a', 'b'])
    chk('aaa:bbb', ['aaa', 'bbb'])

    # Escaped sep char is not a sep char
    chk(r'a\:b', ['a:b'])
    chk(r'aaa\:bbb', ['aaa:bbb'])
    chk(r'a\:b:c', ['a:b', 'c'])
    chk(r'aaa\:bbb:c', ['aaa:bbb', 'c'])

    # Empty initial/final elements
    chk(r':a\:b:c:', ['', 'a:b', 'c', ''])
    chk(r'::a\:b:c::', ['', '', 'a:b', 'c', '', ''])

    # Escaped backslashes, `max` arg
    chk(r'a:b\:c:d\\t\\\\f', ['a', 'b:c', r'd\t\\f'], )
    chk(r'a:b\:c:d\\t\\\\f', ['a', r'b\:c:d\\t\\\\f'], max=1)
    chk(r'a:b\:c:d\\t\\\\f', ['a', 'b:c', r'd\\t\\\\f'], max=2)
    chk(r'a:b\:c:d\\t\\\\f', ['a', 'b:c', r'd\t\\f'], max=3)
    chk(r'a:b\:c:d\\t\\\\f', ['a', 'b:c', r'd\t\\f'], max=4)

    chk(r':a:b\:c:d\\t\\\\f:', ['', 'a', 'b:c', r'd\t\\f', ''], )
    chk(r':a:b\:c:d\\t\\\\f:', ['', r'a:b\:c:d\\t\\\\f:'], max=1)
    chk(r':a:b\:c:d\\t\\\\f:', ['', 'a', r'b\:c:d\\t\\\\f:'], max=2)
    chk(r':a:b\:c:d\\t\\\\f:', ['', 'a', 'b:c', r'd\\t\\\\f:'], max=3)
    chk(r':a:b\:c:d\\t\\\\f:', ['', 'a', 'b:c', r'd\t\\f', ''], max=4)
    chk(r':a:b\:c:d\\t\\\\f:', ['', 'a', 'b:c', r'd\t\\f', ''], max=5)

    chk(r'a:b\:\:\:c:d\\\:\\\\\:eee:\\', ['a', 'b:::c', r'd\:\\:eee', '\\'], )
    chk(r'a:b\:\:\:c:d\\\:\\\\\:eee:\\', ['a', r'b\:\:\:c:d\\\:\\\\\:eee:\\'], max=1)
    chk(r'a:b\:\:\:c:d\\\:\\\\\:eee:\\', ['a', 'b:::c', r'd\\\:\\\\\:eee:\\'], max=2)
    chk(r'a:b\:\:\:c:d\\\:\\\\\:eee:\\', ['a', 'b:::c', r'd\:\\:eee', r'\\'], max=3)
    chk(r'a:b\:\:\:c:d\\\:\\\\\:eee:\\', ['a', 'b:::c', r'd\:\\:eee', '\\'], max=4)

    # sep char requires regex escaping
    check(r'a|b\|c|d\\t\\\\f', ['a', 'b|c', r'd\t\\f'], '|', )
    check(r'a|b\|c|d\\t\\\\f', ['a', r'b\|c|d\\t\\\\f'], '|', max=1)
    check(r'a|b\|c|d\\t\\\\f', ['a', 'b|c', r'd\\t\\\\f'], '|', max=2)
    check(r'a|b\|c|d\\t\\\\f', ['a', 'b|c', r'd\t\\f'], '|', max=3)

    check(r'|a|b\|c|d\\t\\\\f|', ['', 'a', 'b|c', r'd\t\\f', ''], '|')
    check(r'a|b\|\|\|c|d\\\|\\\\\|eee|\\', ['a', 'b|||c', r'd\|\\|eee', '\\'], '|', )

    check(':' * 3, [''] * 4, ':')
    check('|' * 3, [''] * 4, '|')
    check('', [''], '|')
    check('\\' * 10, ['\\' * 5], ':')
    check('\\' * 10, ['\\' * 5], '|')


def test_escape():
    assert esc('"s"', '"') == r'\"s\"'
