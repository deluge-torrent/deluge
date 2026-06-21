#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


import pytest

from deluge.decorators import overrides, proxy


class TestDecorators:
    def test_proxy_with_simple_functions(self):
        def negate(func, *args, **kwargs):
            return not func(*args, **kwargs)

        @proxy(negate)
        def something(_bool):
            return _bool

        @proxy(negate)
        @proxy(negate)
        def double_nothing(_bool):
            return _bool

        assert something(False)
        assert not something(True)
        assert double_nothing(True)
        assert not double_nothing(False)

    def test_proxy_with_class_method(self):
        def negate(func, *args, **kwargs):
            return -func(*args, **kwargs)

        class Test:
            def __init__(self, number):
                self.number = number

            @proxy(negate)
            def diff(self, number):
                return self.number - number

            @proxy(negate)
            def no_diff(self, number):
                return self.diff(number)

        t = Test(5)
        assert t.diff(1) == -4
        assert t.no_diff(1) == 4


class TestOverrides:
    def test_basic(self):
        class Base:
            def method(self):
                pass

        class Child(Base):
            @overrides
            def method(self):
                pass

    def test_explicit_base_class(self):
        class Base:
            def method(self):
                pass

        class Child(Base):
            @overrides(Base)
            def method(self):
                pass

    def test_multiple_inheritance(self):
        class A:
            def method(self):
                pass

        class B(A):
            pass

        class C(B):
            @overrides(A)
            def method(self):
                pass

    def test_missing_method_raises(self):
        class Base:
            def method(self):
                pass

        with pytest.raises(Exception, match='not found'):
            class Child(Base):
                @overrides
                def nonexistent(self):
                    pass

    def test_explicit_base_not_superclass_raises(self):
        class Base:
            def method(self):
                pass

        class Unrelated:
            def method(self):
                pass

        with pytest.raises(Exception):
            class Child(Base):
                @overrides(Unrelated)
                def method(self):
                    pass
