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
    "enc_level": 2,
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
        
        # Load metadata extension
        self.session.add_extension(lt.create_metadata_plugin)

        # Start the TorrentManager
        self.torrents = TorrentManager(self.session)
        
        # Load plugins
        self.plugins = PluginManager()
        
        # Start the AlertManager
        self.alerts = AlertManager(self.session)
        
        # Register alert functions
        self.alerts.register_handler("torrent_finished_alert", 
            self.on_alert_torrent_finished)
        self.alerts.register_handler("torrent_paused_alert",
            self.on_alert_torrent_paused)
            
        # Register set functions in the Config
        self.config.register_set_function("listen_ports", 
            self.on_set_listen_ports)
        self.config.register_set_function("random_port",
            self.on_set_random_port)
        self.config.register_set_function("dht", self.on_set_dht)
        self.config.register_set_function("upnp", self.on_set_upnp)
        self.config.register_set_function("natpmp", self.on_set_natpmp)
        self.config.register_set_function("utpex", self.on_set_utpex)
        self.config.register_set_function("enc_in_policy",
            self.on_set_encryption)
        self.config.register_set_function("enc_out_policy",
            self.on_set_encryption)
        self.config.register_set_function("enc_level",
            self.on_set_encryption)
        self.config.register_set_function("enc_prefer_rc4",
            self.on_set_encryption)
        self.config.register_set_function("max_connections_global",
            self.on_set_max_connections_global)
        self.config.register_set_function("max_upload_speed",
            self.on_set_max_upload_speed)
        self.config.register_set_function("max_download_speed",
            self.on_set_max_download_speed)
        self.config.register_set_function("max_upload_slots_global",
            self.on_set_max_upload_slots_global)
        self.config.register_set_function("max_connections_per_torrent",
            self.on_set_max_connections_per_torrent)
        self.config.register_set_function("max_upload_slots_per_torrent",
            self.on_set_max_upload_slots_per_torrent)
            
        # Run all the set functions now to set the config for the session
        self.config.apply_all()
        
        log.debug("Starting main loop..")
        self.loop = gobject.MainLoop()
        self.loop.run()

    def _shutdown(self):
        """This is called by a thread from shutdown()"""
        log.info("Shutting down core..")
        self.loop.quit()
        del self.torrents
        self.plugins.shutdown()
        del self.plugins
        # Make sure the config file has been saved
        self.config.save()
        del self.config
        del deluge.configmanager
        del self.session
        
    # Exported Methods
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
                                    in_signature="", out_signature="")
    def shutdown(self):
        """Shutdown the core"""
        # Make shutdown an async call
        gobject.idle_add(self._shutdown)

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
    def force_reannounce(self, torrent_id):
        log.debug("Forcing reannouncment to trackers of torrent %s", torrent_id)
        self.torrents.force_reannounce(torrent_id)

    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
                                    in_signature="s", out_signature="")
    def pause_torrent(self, torrent_id):
        log.debug("Pausing torrent %s", torrent_id)
        if not self.torrents.pause(torrent_id):
            log.warning("Error pausing torrent %s", torrent_id)
    
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge")   
    def pause_all_torrents(self):
        """Pause all torrents in the session"""
        if not self.torrents.pause_all():
            log.warning("Error pausing all torrents..")
            
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge")   
    def resume_all_torrents(self):
        """Resume all torrents in the session"""
        if self.torrents.resume_all():
            # Emit the 'torrent_all_resumed' signal
            self.torrent_all_resumed()
        
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
                                in_signature="s",
                                out_signature="ay")     
    def get_config_value(self, key):
        """Get the config value for key"""
        try:
            value = self.config[key]
        except KeyError:
            return None
        
        value = pickle.dumps(value)
        return value
        
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
    
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
        out_signature="i")
    def get_num_connections(self):
        """Returns the current number of connections"""
        return self.session.num_connections()
    
    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
        out_signature="d")
    def get_download_rate(self):
        """Returns the payload download rate"""
        return self.session.status().payload_download_rate


    @dbus.service.method(dbus_interface="org.deluge_torrent.Deluge",
        out_signature="d")
    def get_upload_rate(self):
        """Returns the payload upload rate"""
        return self.session.status().payload_upload_rate
            
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

    @dbus.service.signal(dbus_interface="org.deluge_torrent.Deluge",
                                             signature="s")    
    def torrent_resumed(self, torrent_id):
        """Emitted when a torrent is resumed"""
        log.debug("torrent_resumed signal emitted")

    @dbus.service.signal(dbus_interface="org.deluge_torrent.Deluge")
    def torrent_all_paused(self):
        """Emitted when all torrents have been paused"""
        log.debug("torrent_all_paused signal emitted")

    @dbus.service.signal(dbus_interface="org.deluge_torrent.Deluge")
    def torrent_all_resumed(self):
        """Emitted when all torrents have been resumed"""
        log.debug("torrent_all_resumed signal emitted")
        
    # Config set functions
    def on_set_listen_ports(self, key, value):
        # Only set the listen ports if random_port is not true
        if self.config["random_port"] is not True:
            log.debug("listen port range set to %s-%s", value[0], value[1])
            self.session.listen_on(value[0], value[1])
        
    def on_set_random_port(self, key, value):
        log.debug("random port value set to %s", value)
        # We need to check if the value has been changed to true and false
        # and then handle accordingly.
        if value:
            import random
            listen_ports = []
            randrange = lambda: random.randrange(49152, 65525)
            listen_ports.append(randrange())
            listen_ports.append(listen_ports[0]+10)
        else:
            listen_ports = self.config["listen_ports"]
        
        # Set the listen ports
        log.debug("listen port range set to %s-%s", listen_ports[0], 
            listen_ports[1])
        self.session.listen_on(listen_ports[0], listen_ports[1])
    
    def on_set_dht(self, key, value):
        log.debug("dht value set to %s", value)
        if value:
            self.session.start_dht(None)
        else:
            self.session.stop_dht()
    
    def on_set_upnp(self, key, value):
        log.debug("upnp value set to %s", value)
        if value:
            self.session.start_upnp()
        else:
            self.session.stop_upnp()
    
    def on_set_natpmp(self, key, value):
        log.debug("natpmp value set to %s", value)
        if value:
            self.session.start_natpmp()
        else:
            self.session.stop_natpmp()
    
    def on_set_utpex(self, key, value):
        log.debug("utpex value set to %s", value)
        if value:
            self.session.add_extension(lt.create_ut_pex_plugin)

    def on_set_encryption(self, key, value):
        log.debug("encryption value %s set to %s..", key, value)
        pe_settings = lt.pe_settings()
        pe_settings.out_enc_policy = \
            lt.enc_policy(self.config["enc_out_policy"])
        pe_settings.in_enc_policy = lt.enc_policy(self.config["enc_in_policy"])
        pe_settings.allowed_enc_level = lt.enc_level(self.config["enc_level"])
        pe_settings.prefer_rc4 = self.config["enc_prefer_rc4"]
        self.session.set_pe_settings(pe_settings)
        set = self.session.get_pe_settings()
        log.debug("encryption settings:\n\t\t\tout_policy: %s\n\t\t\
        in_policy: %s\n\t\t\tlevel: %s\n\t\t\tprefer_rc4: %s", 
            set.out_enc_policy,
            set.in_enc_policy,
            set.allowed_enc_level,
            set.prefer_rc4)

    def on_set_max_connections_global(self, key, value):
        log.debug("max_connections_global set to %s..", value)
        self.session.set_max_connections(value)
        
    def on_set_max_upload_speed(self, key, value):
        log.debug("max_upload_speed set to %s..", value)
        # We need to convert Kb/s to B/s
        self.session.set_upload_rate_limit(int(value * 1024))

    def on_set_max_download_speed(self, key, value):
        log.debug("max_download_speed set to %s..", value)
        # We need to convert Kb/s to B/s
        self.session.set_download_rate_limit(int(value * 1024))
        
    def on_set_max_upload_slots_global(self, key, value):
        log.debug("max_upload_slots_global set to %s..", value)
        self.session.set_max_uploads(value)
        
    def on_set_max_connections_per_torrent(self, key, value):
        log.debug("max_connections_per_torrent set to %s..", value)
        self.torrents.set_max_connections(value)
        
    def on_set_max_upload_slots_per_torrent(self, key, value):
        log.debug("max_upload_slots_per_torrent set to %s..", value)
        self.torrents.set_max_uploads(value)
        
    ## Alert handlers ##
    def on_alert_torrent_finished(self, alert):
        log.debug("on_alert_torrent_finished")
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        log.debug("%s is finished..", torrent_id)
        # Write the fastresume file
        self.torrents.write_fastresume(torrent_id)
        
    def on_alert_torrent_paused(self, alert):
        log.debug("on_alert_torrent_paused")
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        # Write the fastresume file
        self.torrents.write_fastresume(torrent_id)
        # Emit torrent_paused signal
        self.torrent_paused(torrent_id)
