# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

from twisted.trial import unittest

from deluge.decorators import proxy


class DecoratorsTestCase(unittest.TestCase):
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

        self.assertTrue(something(False))
        self.assertFalse(something(True))
        self.assertTrue(double_nothing(True))
        self.assertFalse(double_nothing(False))

    def test_proxy_with_class_method(self):
        def negate(func, *args, **kwargs):
            return -func(*args, **kwargs)

        class Test(object):
            def __init__(self, number):
                self.number = number

            @proxy(negate)
            def diff(self, number):
                return self.number - number

            @proxy(negate)
            def no_diff(self, number):
                return self.diff(number)

        t = Test(5)
        self.assertEqual(t.diff(1), -4)
        self.assertEqual(t.no_diff(1), 4)
