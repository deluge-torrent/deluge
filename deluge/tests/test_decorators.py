#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


from deluge.decorators import proxy


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
