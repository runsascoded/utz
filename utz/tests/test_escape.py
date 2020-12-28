
from utz.escape import split, join


def test_split():
    def check(s, strs, ch):
        assert split(s, ch) == strs
        assert join(strs, ch) == s

    check(r'a:b\:c:d\\t\\\\f', ['a','b:c',r'd\t\\f'], ':',)
    check(r':a:b\:c:d\\t\\\\f:', ['','a','b:c',r'd\t\\f',''], ':',)
    check(r'a:b\:\:\:c:d\\\:\\\\\:eee:\\', ['a','b:::c',r'd\:\\:eee','\\'], ':',)

    # sep char requires regex escaping
    check(r'a|b\|c|d\\t\\\\f', ['a','b|c',r'd\t\\f'], '|',)
    check(r'|a|b\|c|d\\t\\\\f|', ['','a','b|c',r'd\t\\f',''], '|')
    check(r'a|b\|\|\|c|d\\\|\\\\\|eee|\\', ['a','b|||c',r'd\|\\|eee','\\'], '|',)

    check(':'*3, ['']*4, ':')
    check('|'*3, ['']*4, '|')
    check('', [''], '|')
    check('\\'*10, ['\\'*5], ':')
    check('\\'*10, ['\\'*5], '|')
