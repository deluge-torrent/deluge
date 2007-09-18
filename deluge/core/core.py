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
from deluge.configmanager import ConfigManager
import deluge.common
from deluge.core.torrentmanager import TorrentManager
from deluge.core.pluginmanager import PluginManager
from deluge.core.alertmanager import AlertManager
from deluge.log import LOG as log

DEFAULT_PREFS = {
    "compact_allocation": True,
    "download_location": deluge.common.get_default_download_dir(),
    "listen_ports": [6881, 6891],
    "torrentfiles_location": deluge.common.get_default_torrent_dir(),
    "plugins_location": deluge.common.get_default_plugin_dir(),
    "prioritize_first_last_pieces": False,
    "random_port": False,
    "dht": False,
    "upnp": False,
    "natpmp": False,
    "utpex": False,
    "enc_in_policy": 1,
    "enc_out_policy": 1,
    "enc_level": 1,
    "enc_prefer_rc4": True,
    "max_connections_global": -1,
    "max_upload_speed": -1.0,
    "max_download_speed": -1.0,
    "max_upload_slots_global": -1,
    "max_connections_per_torrent": -1,
    "max_upload_slots_per_torrent": -1
}

class Core(dbus.service.Object):
    def __init__(self, path="/org/deluge_torrent/Core"):
        log.debug("Core init..")
        
        # Setup DBUS
        bus_name = dbus.service.BusName("org.deluge_torrent.Deluge", 
                                                        bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, path)

        # Get config
        self.config = ConfigManager("core.conf", DEFAULT_PREFS)
        
        # Create the client fingerprint
        version = []
        for value in deluge.common.get_version().split("."):
            version.append(int(value))
        fingerprint = lt.fingerprint("DE", *version)
        
        # Start the libtorrent session
        log.debug("Starting libtorrent session..")
        self.session = lt.session(fingerprint)
        
        # Set the user agent
        self.settings = lt.session_settings()
        self.settings.user_agent = "Deluge %s" % deluge.common.get_version()
        self.session.set_settings(self.settings)
        
        # Set the listening ports
        if self.config["random_port"]:
            import random
            listen_ports = []
            randrange = lambda: random.randrange(49152, 65525)
            listen_ports.append(randrange())
            listen_ports.append(listen_ports[0]+10)
        else:
            listen_ports = self.config["listen_ports"]
        
        log.debug("Listening on ports %i-%i", listen_ports[0],
                                                listen_ports[1])
        self.session.listen_on(listen_ports[0],
                                listen_ports[1])

        # Load metadata extension
        self.session.add_extension(lt.create_metadata_plugin)

        # Load utorrent peer-exchange
        if self.config["utpex"]:
            self.session.add_extension(lt.create_ut_pex_plugin)

        # Start the TorrentManager
        self.torrents = TorrentManager(self.session)
        
        # Load plugins
        self.plugins = PluginManager()
        
        # Start the AlertManager
        self.alerts = AlertManager(self.session)
        
        log.debug("Starting main loop..")
        self.loop = gobject.MainLoop()
        self.loop.run()

    # Exported Methods
    @dbus.service.method("org.deluge_torrent.Deluge")
    def shutdown(self):
        """Shutdown the core"""
        log.info("Shutting down core..")
        self.loop.quit()
        del self.torrents
        self.plugins.shutdown()
        del self.plugins
        del self.config
        del deluge.configmanager
        del self.session

    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge", 
                                    in_signature="say", out_signature="b")
    def add_torrent_file(self, filename, filedump):
        """Adds a torrent file to the libtorrent session
            This requires the torrents filename and a dump of it's content
        """
        torrent_id = self.torrents.add(filename, filedump)

        # Run the plugin hooks for 'post_torrent_add'
        self.plugins.run_post_torrent_add(torrent_id)

        if torrent_id is not None:
            # Emit the torrent_added signal
            self.torrent_added(torrent_id)
            return True
        else:
            # Return False because the torrent was not added successfully
            return False

    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
                                    in_signature="s", out_signature="b")
    def add_torrent_url(self, url):
        log.info("Attempting to add url %s", url)
        
        # Get the actual filename of the torrent from the url provided.
        filename = url.split("/")[-1]
        
        # Get the .torrent file from the url
        torrent_file = deluge.common.fetch_url(url)
        if torrent_file is None:
            return False
        
        # Dump the torrents file contents to a string
        try:
            filedump = open(torrent_file, "rb").read()
        except IOError:
            log.warning("Unable to open %s for reading.", torrent_file)
            return False
            
        # Add the torrent to session
        return self.add_torrent_file(filename, filedump)
        
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
        try:
            status = self.torrents[torrent_id].get_status(nkeys)
        except KeyError:
            # The torrent_id is not found in the torrentmanager, so return None
            status = None
            status.pickle.dumps(status)
            return status
        
        # Get the leftover fields and ask the plugin manager to fill them
        leftover_fields = list(set(nkeys) - set(status.keys()))
        if len(leftover_fields) > 0:
            status.update(self.plugins.get_status(torrent_id, leftover_fields))
        status = pickle.dumps(status)
        return status
    
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
                                in_signature="",
                                out_signature="ay")
    def get_session_state(self):
        """Returns a list of torrent_ids in the session."""
        # Get the torrent list from the TorrentManager
        torrent_list = self.torrents.get_torrent_list()
        # Pickle the list and send it
        session_state = pickle.dumps(torrent_list)
        return session_state
    
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge")
    def save_state(self):
        """Save the current session state to file."""
        # Have the TorrentManager save it's state
        self.torrents.save_state()
    
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
                                in_signature="",
                                out_signature="ay")    
    def get_config(self):
        """Get all the preferences as a dictionary"""
        config = self.config.get_config()
        config = pickle.dumps(config)
        return config
        
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
        in_signature="ay")
    def set_config(self, config):
        """Set the config with values from dictionary"""
        # Convert the byte array into the dictionary
        config = "".join(chr(b) for b in config)
        config = pickle.loads(config)
        # Load all the values into the configuration
        for key in config.keys():
            self.config[key] = config[key]
    
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
        out_signature="i")
    def get_listen_port(self):
        """Returns the active listen port"""
        return self.session.listen_port()
        
    # Signals
    @dbus.service.signal(dbus_interface="org.deluge_torrent.Deluge",
                                             signature="s")
    def torrent_added(self, torrent_id):
        """Emitted when a new torrent is added to the core"""
        log.debug("torrent_added signal emitted")

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
