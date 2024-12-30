
from functools import cached_property
import pytest
from utz import use


# convenient way to verify that a name is undefined
nope = pytest.raises(NameError)


def test_dict():
    x={'a':11,'b':22}
    with use(x):
        assert a == 11
        assert b == 22
    with nope: a
    with nope: b


def test_locals_override():
    a = 'aaa'
    x={'a':11,'b':22}
    with use(x):
        # NOTE: existing local is not overridden; this is a limitation of locals() in function scope that I couldn't find a way around
        assert a == 'aaa'
        assert b == 22

    assert a == 'aaa'
    with nope: b

    with pytest.raises(RuntimeError):
        with use(x, local_conflict='err'):
            pass


TEST_GLOBAL = 'TEST GLOBAL'
def test_global_override_restore():
    a = 'aaa'
    x = { 'a':11, 'b':22, 'TEST_GLOBAL': 'overridden global' }
    with use(x):
        # NOTE: existing local is not overridden; this is a limitation of locals() in function scope that I couldn't find a way around
        assert a == 'aaa'
        assert b == 22
        assert TEST_GLOBAL == 'overridden global'

    assert a == 'aaa'
    with nope: b
    assert TEST_GLOBAL == 'TEST GLOBAL'


class Foo:
    def __init__(self, name):
        self.name = name

    STATIC_MEMBER = "STATIC MEMBER"

    @classmethod
    def cm1(cls): return f'class method 1'
    @classmethod
    def cm2(cls, n): return f'class method 2: {n}'

    @staticmethod
    def sm1(): return 'static method 1'
    @staticmethod
    def sm2(n): return f'static method 2: {n}'

    def method1(self): return 'method 1'
    def method2(self, n): return f'method 2: {n}'

    @property
    def name_reversed(self): return ''.join(reversed(self.name))

    @cached_property
    def name_2x(self): return self.name + self.name

    def __str__(self): return f'Foo({self.name})'


def test_method():
    from utz.methods import Methods
    m = Methods(Foo('abc'))
    assert m.ivars == {'name'}
    assert m.methods == {'method1','method2'}
    assert m.cmethods == {'cm1','cm2'}
    assert m.smethods == {'sm1','sm2'}
    assert m.smembers == {'STATIC_MEMBER'}
    assert m.properties == {'name_reversed'}
    assert m.cached_properties == {'name_2x'}


def test_cls_all():
    foo = Foo('abc')

    with use(foo):
        # everything from `foo` is in scope!
        assert method1() == 'method 1'
        assert method2(111) == 'method 2: 111'
        assert cm1() == 'class method 1'
        assert cm2(222) == 'class method 2: 222'
        assert sm1() == 'static method 1'
        assert sm2(222) == 'static method 2: 222'
        assert STATIC_MEMBER == 'STATIC MEMBER'
        assert name == 'abc'
        assert name_2x == 'abcabc'
        assert name_reversed == 'cba'

    # nothing from `foo` is in scope
    with nope: method1
    with nope: method2
    with nope: cm1
    with nope: cm2
    with nope: sm1
    with nope: sm2
    with nope: STATIC_MEMBER
    with nope: name
    with nope: name_2x
    with nope: name_reversed


def test_cls_ivars_only():
    foo = Foo('abc')

    with use(foo, include='ivars'):
        # only the instance var `name` has been brought into scope
        assert name == 'abc'
        with nope: method1
        with nope: method2
        with nope: cm1
        with nope: cm2
        with nope: sm1
        with nope: sm2
        with nope: STATIC_MEMBER
        with nope: name_2x
        with nope: name_reversed

    # out here it's gone
    with nope: name


def test_exclude_multiple_types():
    foo = Foo('abc')

    # choose one or more classes via `include`/`exclude`
    with use(foo, exclude=['cmethods','smethods']):
        # everything from `foo` is in scope!
        assert method1() == 'method 1'
        assert method2(111) == 'method 2: 111'
        assert STATIC_MEMBER == 'STATIC MEMBER'
        assert name == 'abc'
        assert name_2x == 'abcabc'
        assert name_reversed == 'cba'

        with nope: cm1
        with nope: cm2
        with nope: sm1
        with nope: sm2

    # nothing from `foo` is in scope
    with nope: method1
    with nope: method2
    with nope: STATIC_MEMBER
    with nope: name
    with nope: name_2x
    with nope: name_reversed
