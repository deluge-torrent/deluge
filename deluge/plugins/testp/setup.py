# setup.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
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

"""
Test plugin
"""

from setuptools import setup

__author__ = "Andrew Resch"

setup(
    name="Test Plugin",
    version="1.0",
    description=__doc__,
    author=__author__,
    packages=["testp"],
    package_data = {"testp": ["glade/*.glade"]},
    entry_points="""
    [deluge.plugin.core]
    Testp = testp:CorePlugin
    [deluge.plugin.gtkui]
    Testp = testp:GtkUIPlugin
    """
)
