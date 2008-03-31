#
# core.py
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

import gettext
import locale
import pkg_resources
import sys
import shutil
import os
import signal
import deluge.SimpleXMLRPCServer as SimpleXMLRPCServer
from SocketServer import ThreadingMixIn
import deluge.xmlrpclib as xmlrpclib
import gobject
import threading

import deluge.libtorrent as lt
from deluge.configmanager import ConfigManager
import deluge.common
import deluge.component as component
from deluge.core.torrentmanager import TorrentManager
from deluge.core.pluginmanager import PluginManager
from deluge.core.alertmanager import AlertManager
from deluge.core.signalmanager import SignalManager
from deluge.core.autoadd import AutoAdd
from deluge.log import LOG as log
    
DEFAULT_PREFS = {
    "config_location": deluge.common.get_config_dir(),
    "daemon_port": 58846,
    "allow_remote": False,
    "compact_allocation": True,
    "download_location": deluge.common.get_default_download_dir(),
    "listen_ports": [6881, 6891],
    "torrentfiles_location": deluge.common.get_default_torrent_dir(),
    "plugins_location": deluge.common.get_default_plugin_dir(),
    "prioritize_first_last_pieces": False,
    "random_port": True,
    "dht": False,
    "upnp": False,
    "natpmp": False,
    "utpex": False,
    "lsd": False,
    "enc_in_policy": 1,
    "enc_out_policy": 1,
    "enc_level": 2,
    "enc_prefer_rc4": True,
    "max_connections_global": -1,
    "max_upload_speed": -1.0,
    "max_download_speed": -1.0,
    "max_upload_slots_global": -1,
    "max_connections_per_torrent": -1,
    "max_upload_slots_per_torrent": -1,
    "max_upload_speed_per_torrent": -1,
    "max_download_speed_per_torrent": -1,
    "enabled_plugins": [],
    "autoadd_location": "",
    "autoadd_enable": False,
    "add_paused": False,
    "default_private": False,
    "max_active_seeding": -1,
    "max_active_downloading": -1,
    "queue_new_to_top": False,
    "queue_finished_to_bottom": False,
    "stop_seed_at_ratio": False,
    "remove_seed_at_ratio": False,
    "stop_seed_ratio": 1.00
}
        
class Core(
        ThreadingMixIn, 
        SimpleXMLRPCServer.SimpleXMLRPCServer,
        component.Component):
    def __init__(self, port):
        log.debug("Core init..")
        component.Component.__init__(self, "Core")
        self.client_address = None
        
        # Get config
        self.config = ConfigManager("core.conf", DEFAULT_PREFS)

        if port == None:
            port = self.config["daemon_port"]
            
        if self.config["allow_remote"]:
            hostname = ""
        else:
            hostname = "localhost"
            
        # Setup the xmlrpc server
        try:
            log.info("Starting XMLRPC server on port %s", port)
            SimpleXMLRPCServer.SimpleXMLRPCServer.__init__(
                self, (hostname, port), logRequests=False, allow_none=True)
        except:
            log.info("Daemon already running or port not available..")
            sys.exit(0)

        self.register_multicall_functions()
        
        # Register all export_* functions
        for func in dir(self):
            if func.startswith("export_"):
                self.register_function(getattr(self, "%s" % func), func[7:])

        self.register_introspection_functions()
                
        # Initialize gettext
        locale.setlocale(locale.LC_MESSAGES, '')
        locale.bindtextdomain("deluge", 
                    pkg_resources.resource_filename(
                                            "deluge", "i18n"))
        locale.textdomain("deluge")
        gettext.bindtextdomain("deluge",
                    pkg_resources.resource_filename(
                                            "deluge", "i18n"))
        gettext.textdomain("deluge")
        gettext.install("deluge",
                    pkg_resources.resource_filename(
                                            "deluge", "i18n"))
        # Setup signals
        try:
            import gnome.ui
            self.gnome_client = gnome.ui.Client()
            self.gnome_client.connect("die", self._shutdown)
        except:
            pass

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
        if not deluge.common.windows_check(): 
            signal.signal(signal.SIGHUP, self._shutdown)
        else:
            from win32api import SetConsoleCtrlHandler
            from win32con import CTRL_CLOSE_EVENT
            result = 0
            def win_handler(self, ctrl_type):
                if ctrl_type == CTRL_CLOSE_EVENT:
                    self._shutdown()
                    result = 1
                    return result
            SetConsoleCtrlHandler(win_handler)
            
    def get_request(self):
        """Get the request and client address from the socket.
            We override this so that we can get the ip address of the client.
        """
        request, client_address = self.socket.accept()
        self.client_address = client_address[0]
        return (request, client_address)
        
    def run(self):
        """Starts the core"""

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
        
        # Set lazy bitfield
        self.settings.lazy_bitfields = 1
        self.session.set_settings(self.settings)
        
        # Load metadata extension
        self.session.add_extension(lt.create_metadata_plugin)

        # Register set functions in the Config
        self.config.register_set_function("torrentfiles_location",
            self._on_set_torrentfiles_location)
        self.config.register_set_function("listen_ports", 
            self._on_set_listen_ports)
        self.config.register_set_function("random_port",
            self._on_set_random_port)
        self.config.register_set_function("dht", self._on_set_dht)
        self.config.register_set_function("upnp", self._on_set_upnp)
        self.config.register_set_function("natpmp", self._on_set_natpmp)
        self.config.register_set_function("utpex", self._on_set_utpex)
        self.config.register_set_function("lsd", self._on_set_lsd)
        self.config.register_set_function("enc_in_policy",
            self._on_set_encryption)
        self.config.register_set_function("enc_out_policy",
            self._on_set_encryption)
        self.config.register_set_function("enc_level",
            self._on_set_encryption)
        self.config.register_set_function("enc_prefer_rc4",
            self._on_set_encryption)
        self.config.register_set_function("max_connections_global",
            self._on_set_max_connections_global)
        self.config.register_set_function("max_upload_speed",
            self._on_set_max_upload_speed)
        self.config.register_set_function("max_download_speed",
            self._on_set_max_download_speed)
        self.config.register_set_function("max_upload_slots_global",
            self._on_set_max_upload_slots_global)

        self.config.register_change_callback(self._on_config_value_change)
        # Start the AlertManager
        self.alerts = AlertManager(self.session)
        
        # Start the SignalManager
        self.signals = SignalManager()                    

        # Load plugins
        self.plugins = PluginManager(self)
                
        # Start the TorrentManager
        self.torrents = TorrentManager(self.session, self.alerts)
        
        # Create the AutoAdd component
        self.autoadd = AutoAdd()        

        component.start()
        
        t = threading.Thread(target=self.serve_forever)
        t.setDaemon(True)
        t.start()
        gobject.threads_init()

        self.loop = gobject.MainLoop()
        try:
            self.loop.run()
        except KeyboardInterrupt:
            self._shutdown()
    
    def _shutdown(self, data=None):
        """This is called by a thread from shutdown()"""
        log.info("Shutting down core..")
        component.shutdown()
        # Make sure the config file has been saved
        self.config.save()
        del self.config
        del deluge.configmanager
        del self.session
        self.loop.quit()
        try:
            self.gnome_client.disconnect()
        except:
            pass
        
    # Exported Methods
    def export_ping(self):
        """A method to see if the core is running"""
        return True
        
    def export_shutdown(self):
        """Shutdown the core"""
        # Make shutdown an async call
        gobject.idle_add(self._shutdown)

    def export_register_client(self, port):
        """Registers a client with the signal manager so that signals are
            sent to it."""
        self.signals.register_client(self.client_address, port)
    
    def export_deregister_client(self):
        """De-registers a client with the signal manager."""
        self.signals.deregister_client(self.client_address)
        
    def export_add_torrent_file(self, filename, filedump, options):
        """Adds a torrent file to the libtorrent session
            This requires the torrents filename and a dump of it's content
        """
        # Make sure we are sending a string to add()
        if not isinstance(filedump, str):
            filedump = filedump.data

        torrent_id = self.torrents.add(filename, filedump=filedump, options=options)

        # Run the plugin hooks for 'post_torrent_add'
        self.plugins.run_post_torrent_add(torrent_id)

    def export_add_torrent_url(self, url, save_path, options):
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
        return self.export_add_torrent_file(
            filename, filedump, options)
        
    def export_remove_torrent(self, torrent_ids, remove_torrent, remove_data):
        log.debug("Removing torrent %s from the core.", torrent_ids)
        for torrent_id in torrent_ids:
            if self.torrents.remove(torrent_id, remove_torrent, remove_data):
                # Run the plugin hooks for 'post_torrent_remove'
                self.plugins.run_post_torrent_remove(torrent_id)
                # Emit the torrent_removed signal
                self.torrent_removed(torrent_id)
            
    def export_force_reannounce(self, torrent_ids):
        log.debug("Forcing reannouncment to: %s", torrent_ids)
        for torrent_id in torrent_ids:
            self.torrents[torrent_id].force_reannounce()

    def export_pause_torrent(self, torrent_ids):
        log.debug("Pausing: %s", torrent_ids)
        for torrent_id in torrent_ids:
            if not self.torrents[torrent_id].pause():
                log.warning("Error pausing torrent %s", torrent_id)
    
    def export_move_torrent(self, torrent_ids, dest):
        log.debug("Moving torrents %s to %s", torrent_id, dest)
        for torrent_id in torrent_ids:
            if not self.torrents[torrent_id].move_storage(dest):
                log.warning("Error moving torrent %s to %s", torrent_id, dest)
    
    def export_pause_all_torrents(self):
        """Pause all torrents in the session"""
        if not self.torrents.pause_all():
            log.warning("Error pausing all torrents..")
            
    def export_resume_all_torrents(self):
        """Resume all torrents in the session"""
        if self.torrents.resume_all():
            # Emit the 'torrent_all_resumed' signal
            self.torrent_all_resumed()
        
    def export_resume_torrent(self, torrent_ids):
        log.debug("Resuming: %s", torrent_ids)
        for torrent_id in torrent_ids:
            if self.torrents[torrent_id].resume():
                self.torrent_resumed(torrent_id)

    def export_get_torrent_status(self, torrent_id, keys):
        # Build the status dictionary
        try:
            status = self.torrents[torrent_id].get_status(keys)
        except KeyError:
            # The torrent_id is not found in the torrentmanager, so return None
            return None
        
        # Get the leftover fields and ask the plugin manager to fill them
        leftover_fields = list(set(keys) - set(status.keys()))
        if len(leftover_fields) > 0:
            status.update(self.plugins.get_status(torrent_id, leftover_fields))
        return status
    
    def export_get_torrents_status(self, torrent_ids, keys):
        status_dict = {}.fromkeys(torrent_ids)

        # Get the torrent status for each torrent_id
        for torrent_id in torrent_ids:
            try:
                status = self.torrents[torrent_id].get_status(keys)
            except KeyError:
                return None
            # Get the leftover fields and ask the plugin manager to fill them
            leftover_fields = list(set(keys) - set(status.keys()))
            if len(leftover_fields) > 0:
                status.update(
                    self.plugins.get_status(torrent_id, leftover_fields))
            
            status_dict[torrent_id] = status
        # Emit the torrent_status signal to the clients
        return status_dict
            
    def export_get_session_state(self):
        """Returns a list of torrent_ids in the session."""
        # Get the torrent list from the TorrentManager
        return self.torrents.get_torrent_list()
    
    def export_save_state(self):
        """Save the current session state to file."""
        # Have the TorrentManager save it's state
        self.torrents.save_state()
    
    def export_get_config(self):
        """Get all the preferences as a dictionary"""
        return self.config.get_config()
        
    def export_get_config_value(self, key):
        """Get the config value for key"""
        try:
            value = self.config[key]
        except KeyError:
            return None

        return value

    def export_set_config(self, config):
        """Set the config with values from dictionary"""
        config = deluge.common.pythonize(config)
        # Load all the values into the configuration
        for key in config.keys():
            self.config[key] = config[key]
        
    def export_get_listen_port(self):
        """Returns the active listen port"""
        return self.session.listen_port()
    
    def export_get_num_connections(self):
        """Returns the current number of connections"""
        return self.session.num_connections()
    
    def export_get_dht_nodes(self):
        """Returns the number of dht nodes"""
        return self.session.status().dht_nodes

    def export_get_download_rate(self):
        """Returns the payload download rate"""
        return self.session.status().payload_download_rate

    def export_get_upload_rate(self):
        """Returns the payload upload rate"""
        return self.session.status().payload_upload_rate
    
    def export_get_available_plugins(self):
        """Returns a list of plugins available in the core"""
        return self.plugins.get_available_plugins()

    def export_get_enabled_plugins(self):
        """Returns a list of enabled plugins in the core"""
        return self.plugins.get_enabled_plugins()

    def export_enable_plugin(self, plugin):
        self.plugins.enable_plugin(plugin)
        return None
        
    def export_disable_plugin(self, plugin):
        self.plugins.disable_plugin(plugin)
        return None
    
    def export_force_recheck(self, torrent_ids):
        """Forces a data recheck on torrent_ids"""
        for torrent_id in torrent_ids:
            gobject.idle_add(self.torrents.force_recheck, torrent_id)
    
    def export_set_torrent_trackers(self, torrent_id, trackers):
        """Sets a torrents tracker list.  trackers will be [{"url", "tier"}]"""
        return self.torrents[torrent_id].set_trackers(trackers)
    
    def export_set_torrent_max_connections(self, torrent_id, value):
        """Sets a torrents max number of connections"""
        return self.torrents[torrent_id].set_max_connections(value)
    
    def export_set_torrent_max_upload_slots(self, torrent_id, value):
        """Sets a torrents max number of upload slots"""
        return self.torrents[torrent_id].set_max_upload_slots(value)
        
    def export_set_torrent_max_upload_speed(self, torrent_id, value):
        """Sets a torrents max upload speed"""
        return self.torrents[torrent_id].set_max_upload_speed(value)
        
    def export_set_torrent_max_download_speed(self, torrent_id, value):
        """Sets a torrents max download speed"""
        return self.torrents[torrent_id].set_max_download_speed(value)
    
    def export_set_torrent_private_flag(self, torrent_id, value):
        """Sets a torrents private flag"""
        return self.torrents[torrent_id].set_private_flag(value)
    
    def export_set_torrent_file_priorities(self, torrent_id, priorities):
        """Sets a torrents file priorities"""
        return self.torrents[torrent_id].set_file_priorities(priorities)
    
    def export_block_ip_range(self, range):
        """Block an ip range"""
        try:
            self.ip_filter.add_rule(range[0], range[1], 1)
        except AttributeError:
            self.export_reset_ip_filter()
            self.ip_filter.add_rule(range[0], range[1], 1)
    
    def export_reset_ip_filter(self):
        """Clears the ip filter"""
        self.ip_filter = lt.ip_filter()
        self.session.set_ip_filter(self.ip_filter)
    
    def export_get_health(self):
        """Returns True if we have established incoming connections"""
        return self.session.status().has_incoming_connections

    ## Queueing functions ##
    def export_queue_top(self, torrent_ids):
        log.debug("Attempting to queue %s to top", torrent_ids)
        for torrent_id in torrent_ids:
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrents.queue.top(torrent_id):
                    self._torrent_queue_changed()
            except KeyError:
                log.warning("torrent_id: %s does not exist in the queue", torrent_id)

    def export_queue_up(self, torrent_ids):
        log.debug("Attempting to queue %s to up", torrent_ids)
        #torrent_ids must be sorted before moving.
        torrent_ids.sort(key = lambda id: self.torrents.torrents[id].get_queue_position())
        for torrent_id in torrent_ids:
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrents.queue.up(torrent_id):
                    self._torrent_queue_changed()
            except KeyError:
                log.warning("torrent_id: %s does not exist in the queue", torrent_id)

    def export_queue_down(self, torrent_ids):
        log.debug("Attempting to queue %s to down", torrent_ids)
        #torrent_ids must be sorted before moving.
        torrent_ids.sort(key = lambda id: -self.torrents.torrents[id].get_queue_position())
        for torrent_id in torrent_ids:
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrents.queue.down(torrent_id):
                    self._torrent_queue_changed()
            except KeyError:
                log.warning("torrent_id: %s does not exist in the queue", torrent_id)

    def export_queue_bottom(self, torrent_ids):
        log.debug("Attempting to queue %s to bottom", torrent_ids)
        for torrent_id in torrent_ids:
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrents.queue.bottom(torrent_id):
                    self._torrent_queue_changed()
            except KeyError:
                log.warning("torrent_id: %s does not exist in the queue", torrent_id)

    # Signals
    def torrent_removed(self, torrent_id):
        """Emitted when a torrent has been removed from the core"""
        log.debug("torrent_remove signal emitted")
        self.signals.emit("torrent_removed", torrent_id)
        
    def torrent_paused(self, torrent_id):
        """Emitted when a torrent is paused"""
        log.debug("torrent_paused signal emitted")
        self.signals.emit("torrent_paused", torrent_id)

    def torrent_resumed(self, torrent_id):
        """Emitted when a torrent is resumed"""
        log.debug("torrent_resumed signal emitted")
        self.signals.emit("torrent_resumed", torrent_id)

    def torrent_all_paused(self):
        """Emitted when all torrents have been paused"""
        log.debug("torrent_all_paused signal emitted")
        self.signals.emit("torrent_all_paused")

    def torrent_all_resumed(self):
        """Emitted when all torrents have been resumed"""
        log.debug("torrent_all_resumed signal emitted")
        self.signals.emit("torrent_all_resumed")

    def config_value_changed(self, key, value):
        """Emitted when a config value has changed"""
        log.debug("config_value_changed signal emitted")
        self.signals.emit("config_value_changed", key, value)

    def _torrent_queue_changed(self):
        """Emitted when a torrent queue position is changed"""
        log.debug("torrent_queue_changed signal emitted")
        self.signals.emit("torrent_queue_changed")
        
    # Config set functions
    def _on_config_value_change(self, key, value):
        self.config_value_changed(key, value)
        
    def _on_set_torrentfiles_location(self, key, value):
        try:
            old = self.config.get_previous_config()["torrentfiles_location"]
        except Exception, e:
            # This probably means it's not a real change but we're just loading
            # the config.
            log.debug("Unable to get previous torrentfiles_location: %s", e)
            return
            
        # First try to create the new directory
        try:
            os.makedirs(value)
        except Exception, e:
            log.debug("Unable to make directory: %s", e)

        # Now copy all files in the old directory to the new one
        for root, dirs, files in os.walk(old):
            for dir in dirs:
                os.makedirs(dir)
            for file in files:
                try:
                    shutil.copy2(os.path.join(root, file), value)
                except Exception, e:
                    log.debug("Unable to copy file to %s: %s", value, e)
        
    def _on_set_listen_ports(self, key, value):
        # Only set the listen ports if random_port is not true
        if self.config["random_port"] is not True:
            log.debug("listen port range set to %s-%s", value[0], value[1])
            self.session.listen_on(value[0], value[1])
        
    def _on_set_random_port(self, key, value):
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
    
    def _on_set_dht(self, key, value):
        log.debug("dht value set to %s", value)
        if value:
            self.session.start_dht(None)
            self.session.add_dht_router("router.bittorrent.com", 6881)
            self.session.add_dht_router("router.utorrent.com", 6881)
            self.session.add_dht_router("router.bitcomet.com", 6881)
        else:
            self.session.stop_dht()
    
    def _on_set_upnp(self, key, value):
        log.debug("upnp value set to %s", value)
        if value:
            self.session.start_upnp()
        else:
            self.session.stop_upnp()
    
    def _on_set_natpmp(self, key, value):
        log.debug("natpmp value set to %s", value)
        if value:
            self.session.start_natpmp()
        else:
            self.session.stop_natpmp()

    def _on_set_lsd(self, key, value):
        log.debug("lsd value set to %s", value)
        if value:
            self.session.start_lsd()
        else:
            self.session.stop_lsd()
                
    def _on_set_utpex(self, key, value):
        log.debug("utpex value set to %s", value)
        if value:
            self.session.add_extension(lt.create_ut_pex_plugin)

    def _on_set_encryption(self, key, value):
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

    def _on_set_max_connections_global(self, key, value):
        log.debug("max_connections_global set to %s..", value)
        self.session.set_max_connections(value)
        
    def _on_set_max_upload_speed(self, key, value):
        log.debug("max_upload_speed set to %s..", value)
        # We need to convert Kb/s to B/s
        self.session.set_upload_rate_limit(int(value * 1024))

    def _on_set_max_download_speed(self, key, value):
        log.debug("max_download_speed set to %s..", value)
        # We need to convert Kb/s to B/s
        self.session.set_download_rate_limit(int(value * 1024))
        
    def _on_set_max_upload_slots_global(self, key, value):
        log.debug("max_upload_slots_global set to %s..", value)
        self.session.set_max_uploads(value)
