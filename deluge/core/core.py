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
import os.path

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

import gobject
import deluge.libtorrent as lt

from deluge.config import Config
import deluge.common
from deluge.core.torrentmanager import TorrentManager

# Get the logger
log = logging.getLogger("deluge")

DEFAULT_PREFS = {
    "compact_allocation": True,
    "download_location": deluge.common.get_default_download_dir(),
    "listen_ports": [6881, 6891],
    "torrentfiles_location": deluge.common.get_default_torrent_dir()
}

class Core(dbus.service.Object):
    def __init__(self, path="/org/deluge_torrent/Core"):
        log.debug("Core init..")

        # Start the TorrentManager
        self.torrents = TorrentManager()
        
        # Setup DBUS
        bus_name = dbus.service.BusName("org.deluge_torrent.Deluge", 
                                                        bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, path)

        # Get config
        self.config = Config("core.conf", DEFAULT_PREFS)

        # Setup the libtorrent session and listen on the configured ports
        log.debug("Starting libtorrent session..")
        self.session = lt.session()
        log.debug("Listening on %i-%i", self.config.get("listen_ports")[0],
                                        self.config.get("listen_ports")[1])
        self.session.listen_on(self.config.get("listen_ports")[0],
                               self.config.get("listen_ports")[1])

        log.debug("Starting main loop..")
        self.loop = gobject.MainLoop()
        self.loop.run()

    # Exported Methods
    @dbus.service.method("org.deluge_torrent.Deluge")
    def shutdown(self):
        """Shutdown the core"""
        log.info("Shutting down core..")
        self.loop.quit()

    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge", 
                                    in_signature="say", out_signature="")
    def add_torrent_file(self, filename, filedump):
        """Adds a torrent file to the libtorrent session
            This requires the torrents filename and a dump of it's content
        """
        log.info("Adding torrent: %s", filename)

        # Convert the filedump data array into a string of bytes
        filedump = "".join(chr(b) for b in filedump)
        
        # Bdecode the filedata sent from the UI
        torrent_filedump = lt.bdecode(filedump)
        handle = None
        try:
            handle = self.session.add_torrent(lt.torrent_info(torrent_filedump), 
                                    self.config["download_location"],
                                    self.config["compact_allocation"])
        except RuntimeError:
            log.warning("Error adding torrent") 
            
        if not handle or not handle.is_valid():
            # The torrent was not added to the session
            # Emit the torrent_add_failed signal
            self.torrent_add_failed()
            return
        
        # Write the .torrent file to the torrent directory
        log.debug("Attemping to save torrent file: %s", filename)
        try:
            f = open(os.path.join(self.config["torrentfiles_location"], 
                    filename),
                    "wb")
            f.write(filedump)
            f.close()
        except IOError:
            log.warning("Unable to save torrent file: %s", filename)
        
        # Add the torrent to the torrentmanager
        torrent_id = self.torrents.add(handle)
        
        # Emit the torrent_added signal
        self.torrent_added(torrent_id)

    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
                                    in_signature="s", out_signature="(six)")
    def get_torrent_info(self, torrent_id):
        # Get the info tuple from the torrent and return it
        return self.torrents[torrent_id].get_info()

    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
                                    in_signature="s", 
                                    out_signature="(ibdixxddiixii)")
    def get_torrent_status(self, torrent_id):
        # Get the status tuple from the torrent and return it
        return self.torrents[torrent_id].get_status()
        
    ## Queueing functions ######
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge", 
                                    in_signature="s", out_signature="")
    def queue_top(self, torrent_id):
        # If the queue method returns True, then we should emit a signal
        if self.queue.top(torrent_id):
            self.torrent_queue_top()
            # Store the new torrent position in the torrent object
#            self.torrents[torrent_id].set_position(self.queue[torrent_id])

    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge", 
                                    in_signature="s", out_signature="")
    def queue_up(self, torrent_id):
        # If the queue method returns True, then we should emit a signal
        if self.queue.up(torrent_id):
            self.torrent_queue_up()

    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge", 
                                    in_signature="s", out_signature="")
    def queue_down(self, torrent_id):
        # If the queue method returns True, then we should emit a signal
        if self.queue.down(torrent_id):
            self.torrent_queue_down()

    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge", 
                                    in_signature="s", out_signature="")
    def queue_bottom(self, torrent_id):
        # If the queue method returns True, then we should emit a signal
        if self.queue.bottom(torrent_id):
            self.torrent_queue_bottom()
        
    # Signals
    @dbus.service.signal(dbus_interface="org.deluge_torrent.Deluge",
                                             signature="s")
    def torrent_added(self, torrent_id):
        """Emitted when a new torrent is added to the core"""
        log.debug("torrent_added signal emitted")

    @dbus.service.signal(dbus_interface="org.deluge_torrent.Deluge",
                                             signature="")
    def torrent_add_failed(self):
        """Emitted when a new torrent fails addition to the session"""
        log.debug("torrent_add_failed signal emitted")

    @dbus.service.signal(dbus_interface="org.deluge_torrent.Deluge",
                                             signature="s")
    def torrent_queue_top(self, torrent_id):
        """Emitted when a torrent is queued to the top"""
        log.debug("torrent_queue_top signal emitted")

    @dbus.service.signal(dbus_interface="org.deluge_torrent.Deluge",
                                             signature="s")    
    def torrent_queue_up(self, torrent_id):
        """Emitted when a torrent is queued up"""
        log.debug("torrent_queue_up signal emitted")

    @dbus.service.signal(dbus_interface="org.deluge_torrent.Deluge",
                                             signature="s")    
    def torrent_queue_down(self, torrent_id):
        """Emitted when a torrent is queued down"""
        log.debug("torrent_queue_down signal emitted")

    @dbus.service.signal(dbus_interface="org.deluge_torrent.Deluge",
                                             signature="s")    
    def torrent_queue_bottom(self, torrent_id):
        """Emitted when a torrent is queued to the bottom"""
        log.debug("torrent_queue_bottom signal emitted")
