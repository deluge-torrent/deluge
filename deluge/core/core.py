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
# 	Boston, MA    02110-1301, USA.
#

import glob
import shutil
import os
import os.path
import threading
import pkg_resources
import base64

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
import twisted.web.client

try:
    import deluge.libtorrent as lt
except ImportError:
    import libtorrent as lt
    if not (lt.version_major == 0 and lt.version_minor == 14):
        raise ImportError("This version of Deluge requires libtorrent 0.14!")

import deluge.configmanager
import deluge.common
import deluge.component as component
from deluge.event import *
from deluge.core.torrentmanager import TorrentManager
from deluge.core.pluginmanager import PluginManager
from deluge.core.alertmanager import AlertManager
from deluge.core.filtermanager import FilterManager
from deluge.core.preferencesmanager import PreferencesManager
from deluge.core.autoadd import AutoAdd
from deluge.core.authmanager import AuthManager
from deluge.core.rpcserver import export

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

class Core(component.Component):
    def __init__(self):
        log.debug("Core init..")
        component.Component.__init__(self, "Core")

        # Start the libtorrent session
        log.debug("Starting libtorrent session..")

        # Create the client fingerprint
        version = [int(value.split("-")[0]) for value in deluge.common.get_version().split(".")]
        while len(version) < 4:
            version.append(0)

        self.session = lt.session(lt.fingerprint("DE", *version), flags=0)

        # Load the session state if available
        self.__load_session_state()

        # Load the GeoIP DB for country look-ups if available
        geoip_db = pkg_resources.resource_filename("deluge", os.path.join("data", "GeoIP.dat"))
        if os.path.exists(geoip_db):
            self.session.load_country_db(geoip_db)

        # Set the user agent
        self.settings = lt.session_settings()
        self.settings.user_agent = "Deluge %s" % deluge.common.get_version()

        # Set session settings
        self.settings.send_redundant_have = True
        self.session.set_settings(self.settings)

        # Create an ip filter
        self.ip_filter = lt.ip_filter()

        # This keeps track of the timer to set the ip filter.. We do this a few
        # seconds aftering adding a rule so that 'batch' adding of rules isn't slow.
        self.__set_ip_filter_timer = None

        # Load metadata extension
        self.session.add_extension(lt.create_metadata_plugin)
        self.session.add_extension(lt.create_ut_metadata_plugin)
        self.session.add_extension(lt.create_smart_ban_plugin)

        # Create the components
        self.preferencesmanager = PreferencesManager()
        self.alertmanager = AlertManager(self.session)
        self.pluginmanager = PluginManager(self)
        self.torrentmanager = TorrentManager(self.session, self.alertmanager)
        self.filtermanager = FilterManager(self)
        self.autoadd = AutoAdd()
        self.authmanager = AuthManager()

        # New release check information
        self.new_release = None

        # Get the core config
        self.config = deluge.configmanager.ConfigManager("core.conf")

    def start(self):
        """Starts the core"""
        # New release check information
        self.__new_release = None

    def stop(self):
        # Save the DHT state if necessary
        if self.config["dht"]:
            self.save_dht_state()
        # Save the libtorrent session state
        self.__save_session_state()

        # Make sure the config file has been saved
        self.config.save()

    def shutdown(self):
        pass

    def __save_session_state(self):
        """Saves the libtorrent session state"""
        try:
            open(deluge.common.get_default_config_dir("session.state"), "wb").write(
                lt.bencode(self.session.state()))
        except Exception, e:
            log.warning("Failed to save lt state: %s", e)

    def __load_session_state(self):
        """Loads the libtorrent session state"""
        try:
            self.session.load_state(lt.bdecode(
                open(deluge.common.get_default_config_dir("session.state"), "rb").read()))
        except Exception, e:
            log.warning("Failed to load lt state: %s", e)

    def save_dht_state(self):
        """Saves the dht state to a file"""
        try:
            dht_data = open(deluge.common.get_default_config_dir("dht.state"), "wb")
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
                component.get("RPCServer").emit_event(NewVersionAvailableEvent(self.new_release))
                return self.new_release
        return False

    # Exported Methods
    @export()
    def add_torrent_file(self, filename, filedump, options):
        """
        Adds a torrent file to the session.

        :param filename: str, the filename of the torrent
        :param filedump: str, a base64 encoded string of the torrent file contents
        :param options: dict, the options to apply to the torrent on add

        :returns: the torrent_id as a str or None

        """
        try:
            filedump = base64.decodestring(filedump)
        except Exception, e:
            log.error("There was an error decoding the filedump string!")
            log.exception(e)

        try:
            torrent_id = self.torrentmanager.add(filedump=filedump, options=options, filename=filename)
        except Exception, e:
            log.error("There was an error adding the torrent file %s", filename)
            log.exception(e)
        else:
            # Run the plugin hooks for 'post_torrent_add'
            self.pluginmanager.run_post_torrent_add(torrent_id)

    @export()
    def add_torrent_url(self, url, options):
        """
        Adds a torrent from a url.  Deluge will attempt to fetch the torrent
        from url prior to adding it to the session.

        :param url: str, the url pointing to the torrent file
        :param options: dict, the options to apply to the torrent on add

        :returns: the torrent_id as a str or None

        """
        log.info("Attempting to add url %s", url)
        def on_get_page(page):
            # We got the data, so attempt adding it to the session
            self.add_torrent_file(url.split("/")[-1], base64.encodestring(page), options)

        def on_get_page_error(reason):
            log.error("Error occured downloading torrent from %s", url)
            log.error("Reason: %s", reason)
            # XXX: Probably should raise an exception to the client here
            return

        twisted.web.client.getPage(url).addCallback(on_get_page).addErrback(on_get_page_error)

    @export()
    def add_torrent_magnets(self, uris, options):
        for uri in uris:
            log.debug("Attempting to add by magnet uri: %s", uri)
            try:
                option = options[uris.index(uri)]
            except IndexError:
                option = None

            torrent_id = self.torrentmanager.add(magnet=uri, options=option)

            # Run the plugin hooks for 'post_torrent_add'
            self.pluginmanager.run_post_torrent_add(torrent_id)


    @export()
    def remove_torrent(self, torrent_ids, remove_data):
        log.debug("Removing torrent %s from the core.", torrent_ids)
        for torrent_id in torrent_ids:
            if self.torrentmanager.remove(torrent_id, remove_data):
                # Run the plugin hooks for 'post_torrent_remove'
                self.pluginmanager.run_post_torrent_remove(torrent_id)

    @export()
    def get_stats(self):
        """
        document me!!!
        """
        stats = self.get_session_status(["payload_download_rate", "payload_upload_rate",
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

    @export()
    def get_session_status(self, keys):
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

    @export()
    def force_reannounce(self, torrent_ids):
        log.debug("Forcing reannouncment to: %s", torrent_ids)
        for torrent_id in torrent_ids:
            self.torrentmanager[torrent_id].force_reannounce()

    @export()
    def pause_torrent(self, torrent_ids):
        log.debug("Pausing: %s", torrent_ids)
        for torrent_id in torrent_ids:
            if not self.torrentmanager[torrent_id].pause():
                log.warning("Error pausing torrent %s", torrent_id)

    @export()
    def connect_peer(self, torrent_id, ip, port):
        log.debug("adding peer %s to %s", ip, torrent_id)
        if not self.torrentmanager[torrent_id].connect_peer(ip, port):
            log.warning("Error adding peer %s:%s to %s", ip, port, torrent_id)

    @export()
    def move_storage(self, torrent_ids, dest):
        log.debug("Moving storage %s to %s", torrent_ids, dest)
        for torrent_id in torrent_ids:
            if not self.torrentmanager[torrent_id].move_storage(dest):
                log.warning("Error moving torrent %s to %s", torrent_id, dest)

    @export()
    def pause_all_torrents(self):
        """Pause all torrents in the session"""
        self.session.pause()

    @export()
    def resume_all_torrents(self):
        """Resume all torrents in the session"""
        self.session.resume()
        component.get("RPCServer").emit_event(SessionResumedEvent())

    @export()
    def resume_torrent(self, torrent_ids):
        log.debug("Resuming: %s", torrent_ids)
        for torrent_id in torrent_ids:
            self.torrentmanager[torrent_id].resume()

    @export()
    def get_status_keys(self):
        """
        returns all possible keys for the keys argument in get_torrent(s)_status.
        """
        return STATUS_KEYS + self.pluginmanager.status_fields.keys()

    @export()
    def get_torrent_status(self, torrent_id, keys):
        # Build the status dictionary
        status = self.torrentmanager[torrent_id].get_status(keys)

        # Get the leftover fields and ask the plugin manager to fill them
        leftover_fields = list(set(keys) - set(status.keys()))
        if len(leftover_fields) > 0:
            status.update(self.pluginmanager.get_status(torrent_id, leftover_fields))
        return status

    @export()
    def get_torrents_status(self, filter_dict, keys):
        """
        returns all torrents , optionally filtered by filter_dict.
        """
        torrent_ids = self.filtermanager.filter_torrent_ids(filter_dict)
        status_dict = {}.fromkeys(torrent_ids)

        # Get the torrent status for each torrent_id
        for torrent_id in torrent_ids:
            status_dict[torrent_id] = self.get_torrent_status(torrent_id, keys)

        return status_dict

    @export()
    def get_filter_tree(self , show_zero_hits=True, hide_cat=None):
        """
        returns {field: [(value,count)] }
        for use in sidebar(s)
        """
        return self.filtermanager.get_filter_tree(show_zero_hits, hide_cat)

    @export()
    def get_session_state(self):
        """Returns a list of torrent_ids in the session."""
        # Get the torrent list from the TorrentManager
        return self.torrentmanager.get_torrent_list()

    @export()
    def get_config(self):
        """Get all the preferences as a dictionary"""
        return self.config.config

    @export()
    def get_config_value(self, key):
        """Get the config value for key"""
        try:
            value = self.config[key]
        except KeyError:
            return None

        return value

    @export()
    def get_config_values(self, keys):
        """Get the config values for the entered keys"""
        config = {}
        for key in keys:
            try:
                config[key] = self.config[key]
            except KeyError:
                pass
        return config

    @export()
    def set_config(self, config):
        """Set the config with values from dictionary"""
        # Load all the values into the configuration
        for key in config.keys():
            if isinstance(config[key], unicode) or isinstance(config[key], str):
                config[key] = config[key].encode("utf8")
            self.config[key] = config[key]

    @export()
    def get_listen_port(self):
        """Returns the active listen port"""
        return self.session.listen_port()

    @export()
    def get_num_connections(self):
        """Returns the current number of connections"""
        return self.session.num_connections()

    @export()
    def get_dht_nodes(self):
        """Returns the number of dht nodes"""
        return self.session.status().dht_nodes

    @export()
    def get_download_rate(self):
        """Returns the payload download rate"""
        return self.session.status().payload_download_rate

    @export()
    def get_upload_rate(self):
        """Returns the payload upload rate"""
        return self.session.status().payload_upload_rate

    @export()
    def get_available_plugins(self):
        """Returns a list of plugins available in the core"""
        return self.pluginmanager.get_available_plugins()

    @export()
    def get_enabled_plugins(self):
        """Returns a list of enabled plugins in the core"""
        return self.pluginmanager.get_enabled_plugins()

    @export()
    def enable_plugin(self, plugin):
        self.pluginmanager.enable_plugin(plugin)
        return None

    @export()
    def disable_plugin(self, plugin):
        self.pluginmanager.disable_plugin(plugin)
        return None

    @export()
    def force_recheck(self, torrent_ids):
        """Forces a data recheck on torrent_ids"""
        for torrent_id in torrent_ids:
            self.torrentmanager[torrent_id].force_recheck()

    @export()
    def set_torrent_options(self, torrent_ids, options):
        """Sets the torrent options for torrent_ids"""
        for torrent_id in torrent_ids:
            self.torrentmanager[torrent_id].set_options(options)

    @export()
    def set_torrent_trackers(self, torrent_id, trackers):
        """Sets a torrents tracker list.  trackers will be [{"url", "tier"}]"""
        return self.torrentmanager[torrent_id].set_trackers(trackers)

    @export()
    def set_torrent_max_connections(self, torrent_id, value):
        """Sets a torrents max number of connections"""
        return self.torrentmanager[torrent_id].set_max_connections(value)

    @export()
    def set_torrent_max_upload_slots(self, torrent_id, value):
        """Sets a torrents max number of upload slots"""
        return self.torrentmanager[torrent_id].set_max_upload_slots(value)

    @export()
    def set_torrent_max_upload_speed(self, torrent_id, value):
        """Sets a torrents max upload speed"""
        return self.torrentmanager[torrent_id].set_max_upload_speed(value)

    @export()
    def set_torrent_max_download_speed(self, torrent_id, value):
        """Sets a torrents max download speed"""
        return self.torrentmanager[torrent_id].set_max_download_speed(value)

    @export()
    def set_torrent_file_priorities(self, torrent_id, priorities):
        """Sets a torrents file priorities"""
        return self.torrentmanager[torrent_id].set_file_priorities(priorities)

    @export()
    def set_torrent_prioritize_first_last(self, torrent_id, value):
        """Sets a higher priority to the first and last pieces"""
        return self.torrentmanager[torrent_id].set_prioritize_first_last(value)

    @export()
    def set_torrent_auto_managed(self, torrent_id, value):
        """Sets the auto managed flag for queueing purposes"""
        return self.torrentmanager[torrent_id].set_auto_managed(value)

    @export()
    def set_torrent_stop_at_ratio(self, torrent_id, value):
        """Sets the torrent to stop at 'stop_ratio'"""
        return self.torrentmanager[torrent_id].set_stop_at_ratio(value)

    @export()
    def set_torrent_stop_ratio(self, torrent_id, value):
        """Sets the ratio when to stop a torrent if 'stop_at_ratio' is set"""
        return self.torrentmanager[torrent_id].set_stop_ratio(value)

    @export()
    def set_torrent_remove_at_ratio(self, torrent_id, value):
        """Sets the torrent to be removed at 'stop_ratio'"""
        return self.torrentmanager[torrent_id].set_remove_at_ratio(value)

    @export()
    def set_torrent_move_on_completed(self, torrent_id, value):
        """Sets the torrent to be moved when completed"""
        return self.torrentmanager[torrent_id].set_move_on_completed(value)

    @export()
    def set_torrent_move_on_completed_path(self, torrent_id, value):
        """Sets the path for the torrent to be moved when completed"""
        return self.torrentmanager[torrent_id].set_move_on_completed_path(value)

    @export()
    def block_ip_range(self, range):
        """Block an ip range"""
        self.ip_filter.add_rule(range[0], range[1], 1)

        # Start a 2 second timer (and remove the previous one if it exists)
        #if self.__set_ip_filter_timer:
        #    self.__set_ip_filter_timer.stop()

        #self.__set_ip_filter_timer = LoopingCall(self.session.set_ip_filter, self.ip_filter)
        #self.__set_ip_filter_timer.start(2, False)

    @export()
    def reset_ip_filter(self):
        """Clears the ip filter"""
        self.ip_filter = lt.ip_filter()
        self.session.set_ip_filter(self.ip_filter)

    @export()
    def get_health(self):
        """Returns True if we have established incoming connections"""
        return self.session.status().has_incoming_connections

    @export()
    def get_path_size(self, path):
        """Returns the size of the file or folder 'path' and -1 if the path is
        unaccessible (non-existent or insufficient privs)"""
        return deluge.common.get_path_size(path)

    @export()
    def create_torrent(self, path, tracker, piece_length, comment, target,
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
            self.add_torrent_file(os.path.split(target)[1], open(target, "rb").read(), None)

    @export()
    def upload_plugin(self, filename, plugin_data):
        """This method is used to upload new plugins to the daemon.  It is used
        when connecting to the daemon remotely and installing a new plugin on
        the client side. 'plugin_data' is a xmlrpc.Binary object of the file data,
        ie, plugin_file.read()"""

        f = open(os.path.join(self.config["config_location"], "plugins", filename), "wb")
        f.write(plugin_data.data)
        f.close()
        component.get("CorePluginManager").scan_for_plugins()

    @export()
    def rescan_plugins(self):
        """Rescans the plugin folders for new plugins"""
        component.get("CorePluginManager").scan_for_plugins()

    @export()
    def rename_files(self, torrent_id, filenames):
        """Renames files in 'torrent_id'. The 'filenames' parameter should be a
        list of (index, filename) pairs."""
        self.torrentmanager[torrent_id].rename_files(filenames)

    @export()
    def rename_folder(self, torrent_id, folder, new_folder):
        """Renames the 'folder' to 'new_folder' in 'torrent_id'."""
        self.torrentmanager[torrent_id].rename_folder(folder, new_folder)

    @export()
    def queue_top(self, torrent_ids):
        log.debug("Attempting to queue %s to top", torrent_ids)
        for torrent_id in torrent_ids:
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrentmanager.queue_top(torrent_id):
                    component.get("RPCServer").emit_event(TorrentQueueChangedEvent())
            except KeyError:
                log.warning("torrent_id: %s does not exist in the queue", torrent_id)

    @export()
    def queue_up(self, torrent_ids):
        log.debug("Attempting to queue %s to up", torrent_ids)
        #torrent_ids must be sorted before moving.
        torrent_ids = list(torrent_ids)
        torrent_ids.sort(key = lambda id: self.torrentmanager.torrents[id].get_queue_position())
        for torrent_id in torrent_ids:
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrentmanager.queue_up(torrent_id):
                    component.get("RPCServer").emit_event(TorrentQueueChangedEvent())
            except KeyError:
                log.warning("torrent_id: %s does not exist in the queue", torrent_id)

    @export()
    def queue_down(self, torrent_ids):
        log.debug("Attempting to queue %s to down", torrent_ids)
        #torrent_ids must be sorted before moving.
        torrent_ids = list(torrent_ids)
        torrent_ids.sort(key = lambda id: -self.torrentmanager.torrents[id].get_queue_position())
        for torrent_id in torrent_ids:
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrentmanager.queue_down(torrent_id):
                    component.get("RPCServer").emit_event(TorrentQueueChangedEvent())
            except KeyError:
                log.warning("torrent_id: %s does not exist in the queue", torrent_id)

    @export()
    def queue_bottom(self, torrent_ids):
        log.debug("Attempting to queue %s to bottom", torrent_ids)
        for torrent_id in torrent_ids:
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrentmanager.queue_bottom(torrent_id):
                    component.get("RPCServer").emit_event(TorrentQueueChangedEvent())
            except KeyError:
                log.warning("torrent_id: %s does not exist in the queue", torrent_id)

    @export()
    def glob(self, path):
        return glob.glob(path)

    @export()
    def test_listen_port(self):
        """ Checks if active port is open """
        import urllib
        port = self.get_listen_port()
        try:
            status = urllib.urlopen("http://deluge-torrent.org/test_port.php?port=%s" % port).read()
        except IOError:
            log.debug("Network error while trying to check status of port %s", port)
            return 0
        else:
            return int(status)
