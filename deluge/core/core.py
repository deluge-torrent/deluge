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

import pickle
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import gobject

import deluge.libtorrent as lt
from deluge.config import Config
import deluge.common
from deluge.core.torrentmanager import TorrentManager
from deluge.core.pluginmanager import PluginManager
from deluge.log import LOG as log

DEFAULT_PREFS = {
    "compact_allocation": True,
    "download_location": deluge.common.get_default_download_dir(),
    "listen_ports": [6881, 6891],
    "torrentfiles_location": deluge.common.get_default_torrent_dir(),
    "plugins_location": deluge.common.get_default_plugin_dir()
}

class Core(dbus.service.Object):
    def __init__(self, path="/org/deluge_torrent/Core"):
        log.debug("Core init..")
        
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

        # Start the TorrentManager
        self.torrents = TorrentManager(self.session)
        
        # Load plugins
        self.plugins = PluginManager()
        
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
        torrent_id = self.torrents.add(filename, filedump)

        # Run the plugin hooks for 'post_torrent_add'
        self.plugins.run_post_torrent_add(torrent_id)

        if torrent_id is not None:
            # Emit the torrent_added signal
            self.torrent_added(torrent_id)
        else:
            self.torrent_add_failed()

    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
                                    in_signature="s", out_signature="")
    def remove_torrent(self, torrent_id):
        log.debug("Removing torrent %s from the core.", torrent_id)
        if self.torrents.remove(torrent_id):
            # Run the plugin hooks for 'post_torrent_remove'
            self.plugins.run_post_torrent_remove(torrent_id)
            # Emit the torrent_removed signal
            self.torrent_removed(torrent_id)
            
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
                                    in_signature="s", out_signature="")
    def pause_torrent(self, torrent_id):
        log.debug("Pausing torrent %s", torrent_id)
        if self.torrents.pause(torrent_id):
            self.torrent_paused(torrent_id)
            
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
                                    in_signature="s", out_signature="")
    def resume_torrent(self, torrent_id):
        log.debug("Resuming torrent %s", torrent_id)
        if self.torrents.resume(torrent_id):
            self.torrent_resumed(torrent_id)
    
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
                                    in_signature="sas", 
                                    out_signature="ay")
    def get_torrent_status(self, torrent_id, keys):
        # Convert the array of strings to a python list of strings
        nkeys = []
        for key in keys:
            nkeys.append(str(key))
        # Pickle the status dictionary from the torrent
        status = self.torrents[torrent_id].get_status(nkeys)
        # Get the leftover fields and ask the plugin manager to fill them
        leftover_fields = list(set(nkeys) - set(status.keys()))
        if len(leftover_fields) > 0:
            status.update(self.plugins.get_status(torrent_id, leftover_fields))
        status = pickle.dumps(status)
        return status
        
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
    def torrent_removed(self, torrent_id):
        """Emitted when a torrent has been removed from the core"""
        log.debug("torrent_remove signal emitted")
        
    @dbus.service.signal(dbus_interface="org.deluge_torrent.Deluge",
                                             signature="s")
    def torrent_paused(self, torrent_id):
        """Emitted when a torrent is paused"""
        log.debug("torrent_paused signal emitted")
    
    def torrent_resumed(self, torrent_id):
        """Emitted when a torrent is resumed"""
        log.debug("torrent_resumed signal emitted")
