# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 John Garland <johnnybg+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import inspect
import re
import warnings
from functools import wraps


def proxy(proxy_func):
    """
    Factory class which returns a decorator that passes
    the decorated function to a proxy function

    :param proxy_func: the proxy function
    :type proxy_func: function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return proxy_func(func, *args, **kwargs)

        return wrapper

    return decorator


def overrides(*args):
    """
    Decorater function to specify when class methods override
    super class methods.

    When used as
    @overrides
    def funcname

    the argument will be the funcname function.

    When used as
    @overrides(BaseClass)
    def funcname

    the argument will be the BaseClass

    """
    stack = inspect.stack()
    if inspect.isfunction(args[0]):
        return _overrides(stack, args[0])
    else:
        # One or more classes are specified, so return a function that will be
        # called with the real function as argument
        def ret_func(func, **kwargs):
            return _overrides(stack, func, explicit_base_classes=args)

        return ret_func


def _overrides(stack, method, explicit_base_classes=None):
    # stack[0]=overrides, stack[1]=inside class def'n, stack[2]=outside class def'n
    classes = {}
    derived_class_locals = stack[2][0].f_locals

    # Find all super classes
    m = re.search(r'class\s(.+)\((.+)\)\s*\:', stack[2][4][0])
    class_name = m.group(1)
    base_classes = m.group(2)

    # Handle multiple inheritance
    base_classes = [s.strip() for s in base_classes.split(',')]
    check_classes = base_classes

    if not base_classes:
        raise ValueError(
            'overrides decorator: unable to determine base class of class "%s"'
            % class_name
        )

    def get_class(cls_name):
        if '.' not in cls_name:
            return derived_class_locals[cls_name]
        else:
            components = cls_name.split('.')
            # obj is either a module or a class
            obj = derived_class_locals[components[0]]
            for c in components[1:]:
                assert inspect.ismodule(obj) or inspect.isclass(obj)
                obj = getattr(obj, c)
            return obj

    if explicit_base_classes:
        # One or more base classes are explicitly given, check only those classes
        override_classes = re.search(r'\s*@overrides\((.+)\)\s*', stack[1][4][0]).group(
            1
        )
        override_classes = [c.strip() for c in override_classes.split(',')]
        check_classes = override_classes

    for c in base_classes + check_classes:
        classes[c] = get_class(c)

    # Verify that the explicit override class is one of base classes
    if explicit_base_classes:
        from itertools import product

        for bc, cc in product(base_classes, check_classes):
            if issubclass(classes[bc], classes[cc]):
                break
        else:
            raise Exception(
                'Excplicit override class "%s" is not a super class of: %s'
                % (explicit_base_classes, class_name)
            )
        if not all(hasattr(classes[cls], method.__name__) for cls in check_classes):
            for cls in check_classes:
                if not hasattr(classes[cls], method.__name__):
                    raise Exception(
                        'Function override "%s" not found in superclass: %s\n%s'
                        % (
                            method.__name__,
                            cls,
                            'File: %s:%s' % (stack[1][1], stack[1][2]),
                        )
                    )

    if not any(hasattr(classes[cls], method.__name__) for cls in check_classes):
        raise Exception(
            'Function override "%s" not found in any superclass: %s\n%s'
            % (
                method.__name__,
                check_classes,
                'File: %s:%s' % (stack[1][1], stack[1][2]),
            )
        )
    return method


def deprecated(func):
    """This is a decorator which can be used to mark function as deprecated.

    It will result in a warning being emitted when the function is used.

    """

    @wraps(func)
    def depr_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # Turn off filter
        warnings.warn(
            'Call to deprecated function {}.'.format(func.__name__),
            category=DeprecationWarning,
            stacklevel=2,
        )
        warnings.simplefilter('default', DeprecationWarning)  # Reset filter
        return func(*args, **kwargs)

    return depr_func
