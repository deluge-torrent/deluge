#
# core.py
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

from torrentqueue import TorrentQueue

# Get the logger
log = logging.getLogger("deluge")

class Core(dbus.service.Object):
    def __init__(self, plugin, path="/org/deluge_torrent/Plugin/Queue"):
        # Get the pluginmanager reference
        self.plugin = plugin

        # Setup DBUS
        bus_name = dbus.service.BusName("org.deluge_torrent.Deluge", 
                                                        bus=dbus.SessionBus())

        dbus.service.Object.__init__(self, bus_name, path)
       
        # Instantiate the TorrentQueue object        
        self.queue = TorrentQueue()
        
        # Register core hooks
        self.plugin.register_hook("post_torrent_add", self.post_torrent_add)
        self.plugin.register_hook("post_torrent_remove", 
                                                    self.post_torrent_remove)
        self.plugin.register_status_field("queue", self.status_field_queue)
        
        log.info("Queue Core plugin initialized..")
    
    ## Hooks for core ##
    def post_torrent_add(self, torrent_id):
        if torrent_id is not None:
            self.queue.append(torrent_id)
    
    def post_torrent_remove(self, torrent_id):
        if torrent_id is not None:
            self.queue.remove(torrent_id)
    
    ## Status field function ##
    def status_field_queue(self, torrent_id):
        return self.queue[torrent_id]+1
        
    ## Queueing functions ##
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge.Queue", 
                                    in_signature="s", out_signature="")
    def queue_top(self, torrent_id):
        log.debug("Attempting to queue %s to top", torrent_id)
        try:
            # If the queue method returns True, then we should emit a signal
            if self.queue.top(torrent_id):
                self.torrent_queue_changed()
        except KeyError:
            log.warning("torrent_id: %s does not exist in the queue", 
                                                                    torrent_id)

    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge.Queue", 
                                    in_signature="s", out_signature="")
    def queue_up(self, torrent_id):
        log.debug("Attempting to queue %s to up", torrent_id)
        try:
            # If the queue method returns True, then we should emit a signal
            if self.queue.up(torrent_id):
                self.torrent_queue_changed()
        except KeyError:
            log.warning("torrent_id: %s does not exist in the queue", 
                                                                    torrent_id)
           
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge.Queue", 
                                    in_signature="s", out_signature="")
    def queue_down(self, torrent_id):
        log.debug("Attempting to queue %s to down", torrent_id)
        try:
            # If the queue method returns True, then we should emit a signal
            if self.queue.down(torrent_id):
                self.torrent_queue_changed()
        except KeyError:
            log.warning("torrent_id: %s does not exist in the queue", 
                                                                    torrent_id)

    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge.Queue", 
                                    in_signature="s", out_signature="")
    def queue_bottom(self, torrent_id):
        log.debug("Attempting to queue %s to bottom", torrent_id)
        try:
            # If the queue method returns True, then we should emit a signal
            if self.queue.bottom(torrent_id):
                self.torrent_queue_changed()
        except KeyError:
            log.warning("torrent_id: %s does not exist in the queue", 
                                                                    torrent_id)
    
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge.Queue",
                                    in_signature="", out_signature="as")
    def get_queue_list(self):
        """Returns the queue list.
        """
        log.debug("Getting queue list")
        return self.queue.queue
    
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge.Queue",
                                    in_signature="s", out_signature="i")
    def get_position(self, torrent_id):
        """Returns the queue position of torrent_id"""
        log.debug("Getting queue position for %s", torrent_id)
        return self.queue[torrent_id]
       
    ## Signals ##
    @dbus.service.signal(dbus_interface="org.deluge_torrent.Deluge.Queue",
                                             signature="")
    def torrent_queue_changed(self):
        """Emitted when a torrent queue position is changed"""
        log.debug("torrent_queue_changed signal emitted")
