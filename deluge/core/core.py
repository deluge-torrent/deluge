#
# core.py
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
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
# 	Boston, MA  02110-1301, USA.
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
#

#


import gettext
import locale
import pkg_resources
import sys
import glob
import shutil
import os
import os.path
import signal
import deluge.SimpleXMLRPCServer as SimpleXMLRPCServer
from SocketServer import ThreadingMixIn
import deluge.xmlrpclib as xmlrpclib
import gobject
import threading
import socket

try:
    import deluge.libtorrent as lt
except ImportError:
    import libtorrent as lt
    if not (lt.version_major == 0 and lt.version_minor == 14):
        raise ImportError("This version of Deluge requires libtorrent 0.14!")

import deluge.configmanager
import deluge.common
import deluge.component as component
from deluge.core.torrentmanager import TorrentManager
from deluge.core.pluginmanager import PluginManager
from deluge.core.alertmanager import AlertManager
from deluge.core.signalmanager import SignalManager
from deluge.core.filtermanager import FilterManager
from deluge.core.preferencesmanager import PreferencesManager
from deluge.core.autoadd import AutoAdd
from deluge.core.authmanager import AuthManager
from deluge.core.rpcserver import BasicAuthXMLRPCRequestHandler

from deluge.log import LOG as log

STATUS_KEYS = ['active_time', 'compact', 'distributed_copies', 'download_payload_rate', 'eta',
    'file_priorities', 'file_progress', 'files', 'hash', 'is_auto_managed', 'is_seed', 'max_connections',
    'max_download_speed', 'max_upload_slots', 'max_upload_speed', 'message', 'move_on_completed',
    'move_on_completed_path', 'name', 'next_announce', 'num_files', 'num_peers', 'num_pieces',
    'num_seeds', 'paused', 'peers', 'piece_length', 'prioritize_first_last', 'private', 'progress',
    'queue', 'ratio', 'remove_at_ratio', 'save_path', 'seed_rank', 'seeding_time', 'state', 'stop_at_ratio',
    'stop_ratio', 'time_added', 'total_done', 'total_payload_download', 'total_payload_upload', 'total_peers',
    'total_seeds', 'total_size', 'total_uploaded', 'total_wanted', 'tracker', 'tracker_host',
    'tracker_status', 'trackers', 'upload_payload_rate']

class Core(
        ThreadingMixIn,
        SimpleXMLRPCServer.SimpleXMLRPCServer,
        component.Component):
    def __init__(self, port):
        log.debug("Core init..")
        component.Component.__init__(self, "Core")
        self.client_address = None

        self.prefmanager = PreferencesManager()

        # Get config
        self.config = deluge.configmanager.ConfigManager("core.conf")

        if port == None:
            port = self.config["daemon_port"]

        if self.config["allow_remote"]:
            hostname = ""
        else:
            hostname = "127.0.0.1"

        # Setup the xmlrpc server
        try:
            log.info("Starting XMLRPC server on port %s", port)
            SimpleXMLRPCServer.SimpleXMLRPCServer.__init__(
                self, (hostname, port),
                requestHandler=BasicAuthXMLRPCRequestHandler,
                logRequests=False, allow_none=True)
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
        try:
            locale.setlocale(locale.LC_ALL, '')
            if hasattr(locale, "bindtextdomain"):
                locale.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
            if hasattr(locale, "textdomain"):
                locale.textdomain("deluge")
            gettext.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
            gettext.textdomain("deluge")
            gettext.install("deluge", pkg_resources.resource_filename("deluge", "i18n"))
        except Exception, e:
            log.error("Unable to initialize gettext/locale: %s", e)

        # Setup signals
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
        if not deluge.common.windows_check():
            signal.signal(signal.SIGHUP, self._shutdown)
        else:
            from win32api import SetConsoleCtrlHandler
            from win32con import CTRL_CLOSE_EVENT
            from win32con import CTRL_SHUTDOWN_EVENT
            result = 0
            def win_handler(ctrl_type):
                log.debug("ctrl_type: %s", ctrl_type)
                if ctrl_type == CTRL_CLOSE_EVENT or ctrl_type == CTRL_SHUTDOWN_EVENT:
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
            version.append(int(value.split("-")[0]))
        while len(version) < 4:
            version.append(0)
        fingerprint = lt.fingerprint("DE", *version)

        # Start the libtorrent session
        log.debug("Starting libtorrent session..")
        self.session = lt.session(fingerprint, flags=0)

        # Load the session state if available
        self.load_session_state()

        # Load the GeoIP DB for country look-ups if available
        geoip_db = pkg_resources.resource_filename("deluge", os.path.join("data", "GeoIP.dat"))
        if os.path.exists(geoip_db):
            try:
                self.session.load_country_db(geoip_db)
            except Exception, e:
                log.error("Unable to load geoip database!")
                log.exception(e)

        # Set the user agent
        self.settings = lt.session_settings()
        self.settings.user_agent = "Deluge %s" % deluge.common.get_version()

        # Set session settings
        self.settings.lazy_bitfields = 1
        self.settings.send_redundant_have = True
        self.session.set_settings(self.settings)

        # Create an ip filter
        self.ip_filter = lt.ip_filter()
        # This keeps track of the timer to set the ip filter.. We do this a few
        # seconds aftering adding a rule so that 'batch' adding of rules isn't slow.
        self._set_ip_filter_timer = None

        # Load metadata extension
        self.session.add_extension(lt.create_metadata_plugin)
        self.session.add_extension(lt.create_ut_metadata_plugin)
        self.session.add_extension(lt.create_smart_ban_plugin)

        # Start the AlertManager
        self.alerts = AlertManager(self.session)

        # Start the SignalManager
        self.signals = SignalManager()

        # Load plugins
        self.plugins = PluginManager(self)

        # Start the TorrentManager
        self.torrents = TorrentManager(self.session, self.alerts)

        # Start the FilterManager
        self.filtermanager = FilterManager(self)

        # Create the AutoAdd component
        self.autoadd = AutoAdd()

        # Start the AuthManager
        self.authmanager = AuthManager()

        # New release check information
        self.new_release = None

        component.start("PreferencesManager")
        component.start()

        self._should_shutdown = False

        self.listen_thread = threading.Thread(target=self.handle_thread)
        self.listen_thread.setDaemon(False)
        self.listen_thread.start()
        gobject.threads_init()

        self.loop = gobject.MainLoop()
        try:
            self.loop.run()
        except KeyboardInterrupt:
            self._shutdown()

    def handle_thread(self):
        try:
            while not self._should_shutdown:
                self.handle_request()
            self._should_shutdown = False

        except Exception, e:
            log.debug("handle_thread: %s", e)

    def shutdown(self):
        pass

    def _shutdown(self, *data):
        """This is called by a thread from shutdown()"""
        log.info("Shutting down core..")
        self._should_shutdown = True

        # Save the DHT state if necessary
        if self.config["dht"]:
            self.save_dht_state()

        # Save the libtorrent session state
        self.save_session_state()

        # Shutdown the socket
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except Exception, e:
            log.debug("exception in socket shutdown: %s", e)
        log.debug("Joining listen thread to make sure it shutdowns cleanly..")
        # Join the listen thread for a maximum of 1 second
        self.listen_thread.join(1.0)

        # Start shutting down the components
        component.shutdown()

        # Make sure the config file has been saved
        self.config.save()
        del self.config
        del deluge.configmanager
        del self.session
        self.loop.quit()

    def save_session_state(self):
        """Saves the libtorrent session state"""
        try:
            open(deluge.configmanager.get_config_dir("session.state"), "wb").write(
                lt.bencode(self.session.state()))
        except Exception, e:
            log.warning("Failed to save lt state: %s", e)

    def load_session_state(self):
        """Loads the libtorrent session state"""
        try:
            self.session.load_state(lt.bdecode(
                open(deluge.configmanager.get_config_dir("session.state"), "rb").read()))
        except Exception, e:
            log.warning("Failed to load lt state: %s", e)

    def save_dht_state(self):
        """Saves the dht state to a file"""
        try:
            dht_data = open(deluge.configmanager.get_config_dir("dht.state"), "wb")
            dht_data.write(lt.bencode(self.session.dht_state()))
            dht_data.close()
        except Exception, e:
            log.warning("Failed to save dht state: %s", e)

    def get_new_release(self):
        log.debug("get_new_release")
        from urllib2 import urlopen
        try:
            self.new_release = urlopen(
                "http://download.deluge-torrent.org/version-1.0").read().strip()
        except Exception, e:
            log.debug("Unable to get release info from website: %s", e)
            return
        self.check_new_release()

    def check_new_release(self):
        if self.new_release:
            log.debug("new_release: %s", self.new_release)
            class VersionSplit(object):
                def __init__(self, ver):
                    ver = ver.lower()
                    vs = ver.split("_") if "_" in ver else ver.split("-")
                    self.version = vs[0]
                    self.suffix = None
                    if len(vs) > 1:
                        for s in ("rc", "alpha", "beta", "dev"):
                            if s in vs[1][:len(s)]:
                                self.suffix = vs[1]

                def __cmp__(self, ver):
                    if self.version > ver.version or (self.suffix and self.suffix[:3] == "dev"):
                        return 1
                    if self.version < ver.version:
                        return -1

                    if self.version == ver.version:
                        if self.suffix == ver.suffix:
                            return 0
                        if self.suffix is None:
                            return 1
                        if ver.suffix is None:
                            return -1
                        if self.suffix < ver.suffix:
                            return -1
                        if self.suffix > ver.suffix:
                            return 1

            if VersionSplit(self.new_release) > VersionSplit(deluge.common.get_version()):
                self.signals.emit("new_version_available", self.new_release)
                return self.new_release
        return False

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
        if self.config["new_release_check"]:
            self.check_new_release()

    def export_deregister_client(self):
        """De-registers a client with the signal manager."""
        self.signals.deregister_client(self.client_address)

    def export_add_torrent_file(self, filename, filedump, options):
        """Adds a torrent file to the libtorrent session
            This requires the torrents filename and a dump of it's content
        """
        gobject.idle_add(self._add_torrent_file, filename, filedump, options)

    def _add_torrent_file(self, filename, filedump, options):
        # Turn the filedump into a torrent_info
        if not isinstance(filedump, str):
            filedump = filedump.data

        if len(filedump) == 0:
            log.warning("Torrent file is corrupt!")
            return

        try:
            torrent_info = lt.torrent_info(lt.bdecode(filedump))
        except RuntimeError, e:
            log.warning("Unable to decode torrent file: %s", e)
            return None

        torrent_id = self.torrents.add(filedump=filedump, options=options, filename=filename)

        # Run the plugin hooks for 'post_torrent_add'
        self.plugins.run_post_torrent_add(torrent_id)


    def export_get_stats(self):
        """
        document me!!!
        """
        stats = self.export_get_session_status(["payload_download_rate", "payload_upload_rate",
            "dht_nodes", "has_incoming_connections", "download_rate", "upload_rate"])

        stats.update({
            #dynamic stats:
            "num_connections":self.session.num_connections(),
            "free_space":deluge.common.free_space(self.config["download_location"]),
            #max config values:
            "max_download":self.config["max_download_speed"],
            "max_upload":self.config["max_upload_speed"],
            "max_num_connections":self.config["max_connections_global"],
        })

        return stats


    def export_get_session_status(self, keys):
        """
        Gets the session status values for 'keys'

        :param keys: list of strings, the keys for which we want values
        :returns: a dictionary of {key: value, ...}
        :rtype: dict

        """
        status = {}
        session_status = self.session.status()
        for key in keys:
            status[key] = getattr(session_status, key)

        return status

    def export_add_torrent_url(self, url, options):
        log.info("Attempting to add url %s", url)

        threading.Thread(target=self.fetch_torrent_url_thread, args=(self.export_add_torrent_file, url, options)).start()

    def fetch_torrent_url_thread(self, callback, url, options):
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
        return callback(filename, filedump, options)

    def export_add_torrent_magnets(self, uris, options):
        for uri in uris:
            log.debug("Attempting to add by magnet uri: %s", uri)
            try:
                option = options[uris.index(uri)]
            except IndexError:
                option = None

            torrent_id = self.torrents.add(magnet=uri, options=option)

            # Run the plugin hooks for 'post_torrent_add'
            self.plugins.run_post_torrent_add(torrent_id)

    def export_remove_torrent(self, torrent_ids, remove_data):
        log.debug("Removing torrent %s from the core.", torrent_ids)
        for torrent_id in torrent_ids:
            if self.torrents.remove(torrent_id, remove_data):
                # Run the plugin hooks for 'post_torrent_remove'
                self.plugins.run_post_torrent_remove(torrent_id)

    def export_force_reannounce(self, torrent_ids):
        log.debug("Forcing reannouncment to: %s", torrent_ids)
        for torrent_id in torrent_ids:
            self.torrents[torrent_id].force_reannounce()

    def export_pause_torrent(self, torrent_ids):
        log.debug("Pausing: %s", torrent_ids)
        for torrent_id in torrent_ids:
            if not self.torrents[torrent_id].pause():
                log.warning("Error pausing torrent %s", torrent_id)

    def export_connect_peer(self, torrent_id, ip, port):
        log.debug("adding peer %s to %s", ip, torrent_id)
        if not self.torrents[torrent_id].connect_peer(ip, port):
            log.warning("Error adding peer %s:%s to %s", ip, port, torrent_id)

    def export_move_storage(self, torrent_ids, dest):
        log.debug("Moving storage %s to %s", torrent_ids, dest)
        for torrent_id in torrent_ids:
            if not self.torrents[torrent_id].move_storage(dest):
                log.warning("Error moving torrent %s to %s", torrent_id, dest)

    def export_pause_all_torrents(self):
        """Pause all torrents in the session"""
        for torrent in self.torrents.torrents.values():
            torrent.pause()

    def export_resume_all_torrents(self):
        """Resume all torrents in the session"""
        for torrent in self.torrents.torrents.values():
            torrent.resume()
        self.signals.emit("torrent_all_resumed")

    def export_resume_torrent(self, torrent_ids):
        log.debug("Resuming: %s", torrent_ids)
        for torrent_id in torrent_ids:
            self.torrents[torrent_id].resume()

    def export_get_status_keys(self):
        """
        returns all possible keys for the keys argument in get_torrent(s)_status.
        """
        return STATUS_KEYS + self.plugins.status_fields.keys()

    def export_get_torrent_status(self, torrent_id, keys):
        # Build the status dictionary
        status = self.torrents[torrent_id].get_status(keys)

        # Get the leftover fields and ask the plugin manager to fill them
        leftover_fields = list(set(keys) - set(status.keys()))
        if len(leftover_fields) > 0:
            status.update(self.plugins.get_status(torrent_id, leftover_fields))
        return status

    def export_get_torrents_status(self, filter_dict, keys):
        """
        returns all torrents , optionally filtered by filter_dict.
        """
        torrent_ids = self.filtermanager.filter_torrent_ids(filter_dict)
        status_dict = {}.fromkeys(torrent_ids)

        # Get the torrent status for each torrent_id
        for torrent_id in torrent_ids:
            status_dict[torrent_id] = self.export_get_torrent_status(torrent_id, keys)

        return status_dict

    def export_get_filter_tree(self , show_zero_hits=True, hide_cat=None):
        """
        returns {field: [(value,count)] }
        for use in sidebar(s)
        """
        return self.filtermanager.get_filter_tree(show_zero_hits, hide_cat)

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
        return self.config.config

    def export_get_config_value(self, key):
        """Get the config value for key"""
        try:
            value = self.config[key]
        except KeyError:
            return None

        return value

    def export_get_config_values(self, keys):
        """Get the config values for the entered keys"""
        config = {}
        for key in keys:
            try:
                config[key] = self.config[key]
            except KeyError:
                pass
        return config


    def export_set_config(self, config):
        """Set the config with values from dictionary"""
        # Load all the values into the configuration
        for key in config.keys():
            if isinstance(config[key], unicode) or isinstance(config[key], str):
                config[key] = config[key].encode("utf8")
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
            self.torrents[torrent_id].force_recheck()

    def export_set_torrent_options(self, torrent_ids, options):
        """Sets the torrent options for torrent_ids"""
        for torrent_id in torrent_ids:
            self.torrents[torrent_id].set_options(options)

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

    def export_set_torrent_file_priorities(self, torrent_id, priorities):
        """Sets a torrents file priorities"""
        return self.torrents[torrent_id].set_file_priorities(priorities)

    def export_set_torrent_prioritize_first_last(self, torrent_id, value):
        """Sets a higher priority to the first and last pieces"""
        return self.torrents[torrent_id].set_prioritize_first_last(value)

    def export_set_torrent_auto_managed(self, torrent_id, value):
        """Sets the auto managed flag for queueing purposes"""
        return self.torrents[torrent_id].set_auto_managed(value)

    def export_set_torrent_stop_at_ratio(self, torrent_id, value):
        """Sets the torrent to stop at 'stop_ratio'"""
        return self.torrents[torrent_id].set_stop_at_ratio(value)

    def export_set_torrent_stop_ratio(self, torrent_id, value):
        """Sets the ratio when to stop a torrent if 'stop_at_ratio' is set"""
        return self.torrents[torrent_id].set_stop_ratio(value)

    def export_set_torrent_remove_at_ratio(self, torrent_id, value):
        """Sets the torrent to be removed at 'stop_ratio'"""
        return self.torrents[torrent_id].set_remove_at_ratio(value)

    def export_set_torrent_move_on_completed(self, torrent_id, value):
        """Sets the torrent to be moved when completed"""
        return self.torrents[torrent_id].set_move_on_completed(value)

    def export_set_torrent_move_on_completed_path(self, torrent_id, value):
        """Sets the path for the torrent to be moved when completed"""
        return self.torrents[torrent_id].set_move_on_completed_path(value)

    def export_block_ip_range(self, range):
        """Block an ip range"""
        self.ip_filter.add_rule(range[0], range[1], 1)

        # Start a 2 second timer (and remove the previous one if it exists)
        if self._set_ip_filter_timer:
            gobject.source_remove(self._set_ip_filter_timer)
        self._set_ip_filter_timer = gobject.timeout_add(2000, self.session.set_ip_filter, self.ip_filter)

    def export_reset_ip_filter(self):
        """Clears the ip filter"""
        self.ip_filter = lt.ip_filter()
        self.session.set_ip_filter(self.ip_filter)

    def export_get_health(self):
        """Returns True if we have established incoming connections"""
        return self.session.status().has_incoming_connections

    def export_get_path_size(self, path):
        """Returns the size of the file or folder 'path' and -1 if the path is
        unaccessible (non-existent or insufficient privs)"""
        return deluge.common.get_path_size(path)

    def export_create_torrent(self, path, tracker, piece_length, comment, target,
                        url_list, private, created_by, httpseeds, add_to_session):

        log.debug("creating torrent..")
        threading.Thread(target=_create_torrent_thread,
            args=(
                path,
                tracker,
                piece_length,
                comment,
                target,
                url_list,
                private,
                created_by,
                httpseeds,
                add_to_session)).start()

    def _create_torrent_thread(self, path, tracker, piece_length, comment, target,
                    url_list, private, created_by, httpseeds, add_to_session):
        import deluge.metafile
        deluge.metafile.make_meta_file(
            path,
            tracker,
            piece_length,
            comment=comment,
            target=target,
            url_list=url_list,
            private=private,
            created_by=created_by,
            httpseeds=httpseeds)
        log.debug("torrent created!")
        if add_to_session:
            self.export_add_torrent_file(os.path.split(target)[1], open(target, "rb").read(), None)

    def export_upload_plugin(self, filename, plugin_data):
        """This method is used to upload new plugins to the daemon.  It is used
        when connecting to the daemon remotely and installing a new plugin on
        the client side. 'plugin_data' is a xmlrpc.Binary object of the file data,
        ie, plugin_file.read()"""

        f = open(os.path.join(self.config["config_location"], "plugins", filename), "wb")
        f.write(plugin_data.data)
        f.close()
        component.get("PluginManager").scan_for_plugins()

    def export_rescan_plugins(self):
        """Rescans the plugin folders for new plugins"""
        component.get("PluginManager").scan_for_plugins()

    def export_rename_files(self, torrent_id, filenames):
        """Renames files in 'torrent_id'. The 'filenames' parameter should be a
        list of (index, filename) pairs."""
        self.torrents[torrent_id].rename_files(filenames)

    def export_rename_folder(self, torrent_id, folder, new_folder):
        """Renames the 'folder' to 'new_folder' in 'torrent_id'."""
        self.torrents[torrent_id].rename_folder(folder, new_folder)

    ## Queueing functions ##
    def export_queue_top(self, torrent_ids):
        log.debug("Attempting to queue %s to top", torrent_ids)
        for torrent_id in torrent_ids:
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrents.queue_top(torrent_id):
                    self.signals.emit("torrent_queue_changed")
            except KeyError:
                log.warning("torrent_id: %s does not exist in the queue", torrent_id)

    def export_queue_up(self, torrent_ids):
        log.debug("Attempting to queue %s to up", torrent_ids)
        #torrent_ids must be sorted before moving.
        torrent_ids.sort(key = lambda id: self.torrents.torrents[id].get_queue_position())
        for torrent_id in torrent_ids:
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrents.queue_up(torrent_id):
                    self.signals.emit("torrent_queue_changed")
            except KeyError:
                log.warning("torrent_id: %s does not exist in the queue", torrent_id)

    def export_queue_down(self, torrent_ids):
        log.debug("Attempting to queue %s to down", torrent_ids)
        #torrent_ids must be sorted before moving.
        torrent_ids.sort(key = lambda id: -self.torrents.torrents[id].get_queue_position())
        for torrent_id in torrent_ids:
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrents.queue_down(torrent_id):
                    self.signals.emit("torrent_queue_changed")
            except KeyError:
                log.warning("torrent_id: %s does not exist in the queue", torrent_id)

    def export_queue_bottom(self, torrent_ids):
        log.debug("Attempting to queue %s to bottom", torrent_ids)
        for torrent_id in torrent_ids:
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrents.queue_bottom(torrent_id):
                    self.signals.emit("torrent_queue_changed")
            except KeyError:
                log.warning("torrent_id: %s does not exist in the queue", torrent_id)

    def export_glob(self, path):
        return glob.glob(path)

    def export_test_listen_port(self):
        """ Checks if active port is open """
        import urllib
        port = self.export_get_listen_port()
        try:
            status = urllib.urlopen("http://deluge-torrent.org/test_port.php?port=%s" % port).read()
        except IOError:
            log.debug("Network error while trying to check status of port %s", port)
            return 0
        else:
            return int(status)
