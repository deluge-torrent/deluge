# setup.py
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2008 Mark Stahler ('kramed') <markstahler@gmail.com>

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
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA    02110-1301, USA.
#


"""
Download and import IP Blocklists
"""

from setuptools import setup

__author__ = "Andrew Resch"

setup(
    name="Blocklist",
    version="1.0",
    description=__doc__,
    author=__author__,
    packages=["blocklist"],
    package_data = {"blocklist": ["data/*"]},
    entry_points="""
    [deluge.plugin.core]
    Blocklist = blocklist:CorePlugin
    [deluge.plugin.gtkui]
    Blocklist = blocklist:GtkUIPlugin
    [deluge.plugin.webui]
    Blocklist = blocklist:WebUIPlugin
    """
)
