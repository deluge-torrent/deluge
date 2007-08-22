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
        
        # Connect to the 'torrent_queue_changed' signal
        self.core.connect_to_signal("torrent_queue_changed", 
                                        self.torrent_queue_changed_signal)
        
        # Get the torrentview component from the plugin manager
        self.torrentview = self.plugin.get_torrentview()
        # Add the '#' column at the first position
        self.torrentview.add_text_column("#", 
                                        col_type=int,
                                        position=0, 
                                        status_field=["queue"])
        # Add a toolbar buttons
        self.plugin.get_toolbar().add_separator()
        self.plugin.get_toolbar().add_toolbutton(stock="gtk-go-up", 
                                    label="Queue Up", 
                                    tooltip="Queue selected torrents up",
                                    callback=self.on_queueup_toolbutton_clicked)

        self.plugin.get_toolbar().add_toolbutton(stock="gtk-go-down", 
                                label="Queue Down", 
                                tooltip="Queue selected torrents down",
                                callback=self.on_queuedown_toolbutton_clicked)

    def on_queuedown_toolbutton_clicked(self, widget):
        log.debug("Queue down toolbutton clicked.")
        # Get the selected torrents
        torrent_ids = self.plugin.get_selected_torrents()
        for torrent_id in torrent_ids:
            self.core.queue_down(torrent_id)
        return
        
    def on_queueup_toolbutton_clicked(self, widget):
        log.debug("Queue Up toolbutton clicked.")    
        # Get the selected torrents
        torrent_ids = self.plugin.get_selected_torrents()
        for torrent_id in torrent_ids:
            self.core.queue_up(torrent_id)
        return
    
    def torrent_queue_changed_signal(self):
        """This function is called whenever we receive a 'torrent_queue_changed'
        signal from the core plugin.
        """
        log.debug("torrent_queue_changed signal received..")
        # We only need to update the queue column
        self.torrentview.update(["#"])
        return

