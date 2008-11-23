#
# coreclient.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
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
# 	Boston, MA    02110-1301, USA.
#



import deluge.component as component

class CoreClient(object):
    """
    provides the uiclient interface to core plugins
    see http://dev.deluge-torrent.org/wiki/Development/UiClient
    """
    def __init__(self):
        self.core = component.get("Core")

    def __getattr__(self, func_name):
        return self.core.funcs[func_name]

client = CoreClient()

