# setup.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
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


"""
Label plugin.

Offers filters on state,tracker and keyword.
adds a tracker column.

future: Real labels.

"""

from setuptools import setup

__author__ = "Martijn Voncken <mvoncken@gmail.com>"

setup(
    name="Label",
    version="0.1",
    description=__doc__,
    author=__author__,
    packages=["label"],
    package_data = {"label": ["template/*"]},
    entry_points="""
    [deluge.plugin.core]
    Label = label:CorePlugin
    [deluge.plugin.webui]
    Label = label:WebUIPlugin
    [deluge.plugin.gtkui]
    Label = label:GtkUIPlugin
    """
)
