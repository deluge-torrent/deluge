# -*- coding: utf-8 -*-
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#               2007-2009 Andrew Resch <andrewresch@gmail.com>
#               2009 Damien Churchill <damoxc@gmail.com>
#               2010 Pedro Algarvio <pedro@algarvio.me>
#               2017 Calum Lind <calumlind+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import os.path
from functools import wraps
from sys import exc_info

import six
from pkg_resources import resource_filename


def get_resource(filename):
    return resource_filename(__package__, os.path.join('data', filename))


def raises_errors_as(error):
    """Factory class that returns a decorator which wraps the decorated
    function to raise all exceptions as the specified error type.

    """

    def decorator(func):
        """Returns a function which wraps the given func to raise all exceptions as error."""

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            """Wraps the function in a try..except block and calls it with the specified args.

            Raises:
                Any exceptions as error preserving the message and traceback.

            """
            try:
                return func(self, *args, **kwargs)
            except Exception:
                (value, tb) = exc_info()[1:]
                six.reraise(error, value, tb)

        return wrapper

    return decorator


def remove_zeros(ip):
    """Removes unneeded zeros from ip addresses.

    Args:
        ip (str): The ip address.

    Returns:
        str: The ip address without the unneeded zeros.

    Example:
        000.000.000.003 -> 0.0.0.3

    """
    return '.'.join([part.lstrip('0').zfill(1) for part in ip.split('.')])


class BadIP(Exception):
    _message = None

    def __init__(self, message):
        super(BadIP, self).__init__(message)

    def __set_message(self, message):
        self._message = message

    def __get_message(self):
        return self._message

    message = property(__get_message, __set_message)
    del __get_message, __set_message


class IP(object):
    __slots__ = ('q1', 'q2', 'q3', 'q4', '_long')

    def __init__(self, q1, q2, q3, q4):
        self.q1 = q1
        self.q2 = q2
        self.q3 = q3
        self.q4 = q4
        self._long = 0
        for q in self.quadrants():
            self._long = (self._long << 8) | int(q)

    @property
    def address(self):
        return '.'.join([str(q) for q in [self.q1, self.q2, self.q3, self.q4]])

    @property
    def long(self):
        return self._long

    @classmethod
    def parse(cls, ip):
        try:
            q1, q2, q3, q4 = [int(q) for q in ip.split('.')]
        except ValueError:
            raise BadIP(_('The IP address "%s" is badly formed' % ip))
        if q1 < 0 or q2 < 0 or q3 < 0 or q4 < 0:
            raise BadIP(_('The IP address "%s" is badly formed' % ip))
        elif q1 > 255 or q2 > 255 or q3 > 255 or q4 > 255:
            raise BadIP(_('The IP address "%s" is badly formed' % ip))
        return cls(q1, q2, q3, q4)

    def quadrants(self):
        return (self.q1, self.q2, self.q3, self.q4)

    #    def next_ip(self):
    #        (q1, q2, q3, q4) = self.quadrants()
    #        if q4 >= 255:
    #            if q3 >= 255:
    #                if q2 >= 255:
    #                    if q1 >= 255:
    #                        raise BadIP(_('There is not a next IP address'))
    #                    q1 += 1
    #                else:
    #                    q2 += 1
    #            else:
    #                q3 += 1
    #        else:
    #            q4 += 1
    #        return IP(q1, q2, q3, q4)
    #
    #    def previous_ip(self):
    #        (q1, q2, q3, q4) = self.quadrants()
    #        if q4 <= 1:
    #            if q3 <= 1:
    #                if q2 <= 1:
    #                    if q1 <= 1:
    #                        raise BadIP(_('There is not a previous IP address'))
    #                    q1 -= 1
    #                else:
    #                    q2 -= 1
    #            else:
    #                q3 -= 1
    #        else:
    #            q4 -= 1
    #        return IP(q1, q2, q3, q4)

    def __lt__(self, other):
        if isinstance(other, ''.__class__):
            other = IP.parse(other)
        return self.long < other.long

    def __gt__(self, other):
        if isinstance(other, ''.__class__):
            other = IP.parse(other)
        return self.long > other.long

    def __eq__(self, other):
        if isinstance(other, ''.__class__):
            other = IP.parse(other)
        return self.long == other.long

    def __repr__(self):
        return '<%s long=%s address="%s">' % (
            self.__class__.__name__,
            self.long,
            self.address,
        )
