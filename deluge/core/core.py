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

import gobject
import deluge.libtorrent as lt

from deluge.config import Config
import deluge.common
from deluge.core.torrent import Torrent

# Get the logger
log = logging.getLogger("deluge")

DEFAULT_PREFS = {
    "listen_ports": [6881, 6891],
    "download_location": deluge.common.get_default_download_dir(),
    "compact_allocation": True
}

class Core(dbus.service.Object):
    def __init__(self, path="/org/deluge_torrent/Core"):
        log.debug("Core init..")
        bus_name = dbus.service.BusName("org.deluge_torrent.Deluge", 
                                                        bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, path)
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
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge", 
                                    in_signature="s", out_signature="")
    def add_torrent_file(self, _filename):
        """Adds a torrent file to the libtorrent session
        """
        log.info("Adding torrent: %s", _filename)
        torrent = Torrent(filename=_filename)
        self.session.add_torrent(torrent.torrent_info, 
                                    self.config["download_location"], 
                                    self.config["compact_allocation"])
        # Emit the torrent_added signal
        self.torrent_added()

    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge", 
                                    in_signature="s", out_signature="")
    def add_torrent_url(self, _url):
        """Adds a torrent from url to the libtorrent session
        """
        log.info("Adding torrent: %s", _url)
        torrent = Torrent(url=_url)
        self.session.add_torrent(torrent.torrent_info, 
                                    self.config["download_location"], 
                                    self.config["compact_allocation"])

    
    @dbus.service.method("org.deluge_torrent.Deluge")
    def shutdown(self):
        log.info("Shutting down core..")
        self.loop.quit()
        
    # Signals
    @dbus.service.signal(dbus_interface="org.deluge_torrent.Deluge",
                                             signature="")
    def torrent_added(self):
        """Emitted when a new torrent is added to the core"""
        log.debug("torrent_added signal emitted")
