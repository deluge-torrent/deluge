#
# gtkui.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.

import logging

try:
    import dbus, dbus.service
    dbus_version = getattr(dbus, "version", (0,0,0))
    if dbus_version >= (0,41,0) and dbus_version < (0,80,0):
        import dbus.glib
    elif dbus_version >= (0,80,0):
        from dbus.mainloop.glib import DBusGMainLoop
        DBusGMainLoop(set_as_default=True)
    else:
        pass
except: dbus_imported = False
else: dbus_imported = True

# Get the logger
log = logging.getLogger("deluge")

class GtkUI:
    def __init__(self, plugin_manager):
        log.debug("Queue GtkUI plugin initalized..")
        self.plugin = plugin_manager
        # Get a reference to the core portion of the plugin
        bus = dbus.SessionBus()
        proxy = bus.get_object("org.deluge_torrent.Deluge", 
                               "/org/deluge_torrent/Plugin/Queue")
        self.core = dbus.Interface(proxy, "org.deluge_torrent.Deluge.Queue")
        # Get the torrentview component from the plugin manager
        self.torrentview = self.plugin.get_torrentview()
        # Add the '#' column at the first position
        self.torrentview.add_text_column("#", 
                                        col_type=int,
                                        position=0, 
                                        get_function=self.column_get_function)
    
    def column_get_function(self, torrent_id):
        """Returns the queue position for torrent_id"""
        # Return the value + 1 because we want the queue list to start at 1
        # for the user display.
        return self.core.get_position(torrent_id) + 1
