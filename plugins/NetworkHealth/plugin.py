# -*- coding: utf-8 -*-
#
# plugin.py
#
# Copyright (C) Marcos Pinto 2007 <markybob@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.

class plugin_NetworkHealth:
    def __init__(self, path, deluge_core, deluge_interface):
        print "Found NetworkHealth plugin..."
        self.parent = deluge_interface # Using this, you can access the Deluge client
        self.core = deluge_core
        self.location = path

        self.counter = 30
        self.maxCount = self.counter
    
    def update(self):
        session_info = self.core.get_state()
        if not session_info['has_incoming_connections'] and \
                 session_info['num_peers'] > 1:
            message = "[No incoming connections]"
            self.counter = self.counter - 1
            if self.counter < 0:
                # self.parent.addMessage("No incoming connections: you may be behind a firewall or router. Perhaps you need to forward the relevant ports.", "W")
                self.counter  = self.maxCount*2
                self.maxCount = self.counter
        else:
            message = _("[Health: OK]")
            self.counter = self.maxCount

        self.parent.statusbar_temp_msg = self.parent.statusbar_temp_msg + '   ' + message
