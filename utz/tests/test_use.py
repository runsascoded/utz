
from functools import cached_property
import pytest
from utz.use import use


def test_dict():
    x={'a':11,'b':22}
    with use(x):
        assert a == 11
        assert b == 22
    with pytest.raises(NameError): print(a)
    with pytest.raises(NameError): print(b)


def test_locals_override():
    a = 'aaa'
    x={'a':11,'b':22}
    with use(x):
        # NOTE: existing local is not overridden; this is a limitation of locals() in function scope that I couldn't find a way around
        assert a == 'aaa'
        assert b == 22

    assert a == 'aaa'
    with pytest.raises(NameError): print(b)

    with pytest.raises(RuntimeError):
        with use(x, local_conflict='err'):
            pass


TEST_GLOBAL = 'TEST GLOBAL'
def test_global_override_restore():
    a = 'aaa'
    x={'a':11,'b':22, TEST_GLOBAL: 'overridden global'}
    with use(x):
        # NOTE: existing local is not overridden; this is a limitation of locals() in function scope that I couldn't find a way around
        assert a == 'aaa'
        assert b == 22
        assert TEST_GLOBAL == 'overriden'

    assert a == 'aaa'
    with pytest.raises(NameError): print(b)
    assert TEST_GLOBAL == 'TEST_GLOBAL'


class Foo:
    def __init__(self, name):
        self.name = name

    STATIC_MEMBER = "111"

    @classmethod
    def cm(cls): return 'class method'

    @staticmethod
    def sm(): return 'static method'

    def method1(self, n): return n * 2
    def method2(self): return 'method 2'

    @property
    def name_reversed(self): return ''.join(reversed(self.name))

    @cached_property
    def name_2x(self): return self.name + self.name

    def __str__(self): return f'Foo({self.name})'


def test_method():
    from utz.methods import Methods
    m = Methods(Foo('abc'))
    assert m.ivars == {'name'}
    assert m.methods == {'method1', 'method2'}
    assert m.cmethods == {'cm'}
    assert m.smethods == {'sm'}
    assert m.smembers == {'STATIC_MEMBER'}
    assert m.properties == {'name_reversed'}
    assert m.cached_properties == {'name_2x'}


def test_cls_all():
    foo = Foo('abc')
    with use(foo):
        assert method1(3) == 6
        assert method2() == 'method 2'
        assert name == 'abc'
        assert name_2x == 'abcabc'
        assert name_reversed == 'cba'
    with pytest.raises(NameError): print(method1)
    with pytest.raises(NameError): print(method2)
    with pytest.raises(NameError): print(name_2x)
    with pytest.raises(NameError): print(name_reversed)
    with pytest.raises(NameError): print(name)


def test_cls_ivars_only():
    foo = Foo('abc')
    with use(foo, properties='no', methods=False):
        assert name == 'abc'
        with pytest.raises(NameError): print(method1)
        with pytest.raises(NameError): print(method2)
        with pytest.raises(NameError): print(name_2x)
        with pytest.raises(NameError): print(name_reversed)
    with pytest.raises(NameError): print(name)
