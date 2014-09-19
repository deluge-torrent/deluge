# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 John Garland <johnnybg+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

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
