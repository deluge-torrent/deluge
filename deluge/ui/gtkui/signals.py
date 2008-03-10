#
# signals.py
#
# Copyright (C) 2007, 2008 Andrew Resch ('andar') <andrewresch@gmail.com>
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

import deluge.component as component
from deluge.ui.client import aclient as client
from deluge.ui.signalreceiver import SignalReceiver
from deluge.log import LOG as log

class Signals(component.Component):
    def __init__(self):
        component.Component.__init__(self, "Signals")
        self.receiver = SignalReceiver()

    def start(self):
        if not client.is_localhost():
            self.receiver.set_remote(True)

        self.receiver.run()
        self.receiver.connect_to_signal("torrent_added", 
            self.torrent_added_signal)
        self.receiver.connect_to_signal("torrent_removed", 
            self.torrent_removed_signal)
        self.receiver.connect_to_signal("torrent_paused", self.torrent_paused)
        self.receiver.connect_to_signal("torrent_resumed", 
            self.torrent_resumed)
        self.receiver.connect_to_signal("torrent_all_paused", 
            self.torrent_all_paused)
        self.receiver.connect_to_signal("torrent_all_resumed", 
            self.torrent_all_resumed)
        self.receiver.connect_to_signal("config_value_changed",
            self.config_value_changed)
        self.receiver.connect_to_signal("torrent_queue_changed",
            self.torrent_queue_changed)
    
    def stop(self):
        try:
            self.receiver.shutdown()
        except:
            pass
    
    def connect_to_signal(self, signal, callback):
        """Connects a callback to a signal"""
        self.receiver.connect_to_signal(signal, callback)
            
    def torrent_added_signal(self, torrent_id):
        log.debug("torrent_added signal received..")
        log.debug("torrent id: %s", torrent_id)
        # Add the torrent to the treeview
        component.get("TorrentView").add_row(torrent_id)

    def torrent_removed_signal(self, torrent_id):
        log.debug("torrent_remove signal received..")
        log.debug("torrent id: %s", torrent_id)
        # Remove the torrent from the treeview
        component.get("TorrentView").remove_row(torrent_id)
        component.get("TorrentDetails").clear()
        component.get("ToolBar").update_buttons()

    def torrent_paused(self, torrent_id):
        log.debug("torrent_paused signal received..")
        component.get("TorrentView").update()
        component.get("ToolBar").update_buttons("paused", torrent_id)
    
    def torrent_resumed(self, torrent_id):
        log.debug("torrent_resumed signal received..")
        component.get("TorrentView").update()
        component.get("ToolBar").update_buttons("resumed", torrent_id)
    
    def torrent_all_paused(self):
        log.debug("torrent_all_paused signal received..")
        component.get("TorrentView").update()
        component.get("ToolBar").update_buttons("paused")

    def torrent_all_resumed(self):
        log.debug("torrent_all_resumed signal received..")
        component.get("TorrentView").update()
        component.get("ToolBar").update_buttons("resumed")

    def config_value_changed(self, key, value):
        log.debug("config_value_changed signal received..")
        component.get("StatusBar").config_value_changed(key, value)
        component.get("SystemTray").config_value_changed(key, value)
    
    def torrent_queue_changed(self):
        log.debug("torrent_queue_changed signal received..")
        component.get("TorrentView").update()
        
