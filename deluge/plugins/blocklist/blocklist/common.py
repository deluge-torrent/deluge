#
# common.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#


import pkg_resources
import os.path
from functools import wraps
from sys import exc_info

def get_resource(filename):
    return pkg_resources.resource_filename("blocklist", os.path.join("data", filename))

def raisesErrorsAs(error):
    """
    Factory class that returns a decorator which wraps
    the decorated function to raise all exceptions as
    the specified error type
    """
    def decorator(func):
        """
        Returns a function which wraps the given func
        to raise all exceptions as error
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            """
            Wraps the function in a try..except block
            and calls it with the specified args

            Raises any exceptions as error preserving the
            message and traceback
            """
            try:
                return func(self, *args, **kwargs)
            except:
                (value, tb) = exc_info()[1:]
                raise error, value, tb
        return wrapper
    return decorator

def remove_zeros(ip):
    """
    Removes unneeded zeros from ip addresses.
    
    Example: 000.000.000.003 -> 0.0.0.3
    
    :param ip: the ip address
    :type ip: string
    
    :returns: the ip address without the unneeded zeros
    :rtype: string
    
    """
    return ".".join([part.lstrip("0").zfill(1) for part in ip.split(".")])
