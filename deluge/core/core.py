# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import base64
import glob
import logging
import os
import shutil
import tempfile
import threading

from twisted.internet import reactor, task
from twisted.web.client import getPage

import deluge.common
import deluge.component as component
from deluge import path_chooser_common
from deluge._libtorrent import lt
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.core.alertmanager import AlertManager
from deluge.core.authmanager import (AUTH_LEVEL_ADMIN, AUTH_LEVEL_NONE, AUTH_LEVELS_MAPPING,
                                     AUTH_LEVELS_MAPPING_REVERSE, AuthManager)
from deluge.core.eventmanager import EventManager
from deluge.core.filtermanager import FilterManager
from deluge.core.pluginmanager import PluginManager
from deluge.core.preferencesmanager import PreferencesManager
from deluge.core.rpcserver import export
from deluge.core.torrentmanager import TorrentManager
from deluge.error import DelugeError, InvalidPathError, InvalidTorrentError
from deluge.event import NewVersionAvailableEvent, SessionPausedEvent, SessionResumedEvent, TorrentQueueChangedEvent
from deluge.httpdownloader import download_file

log = logging.getLogger(__name__)


class Core(component.Component):
    def __init__(self, listen_interface=None):
        log.debug("Core init...")
        component.Component.__init__(self, "Core")

        # Create the client fingerprint
        client_id = "DE"
        client_version = deluge.common.VersionSplit(deluge.common.get_version()).version
        while len(client_version) < 4:
            client_version.append(0)

        # Start the libtorrent session
        log.info("Starting libtorrent %s (%s, %s) session...", lt.version, client_id, client_version)
        self.session = lt.session(lt.fingerprint(client_id, *client_version), flags=0)

        # Load the session state if available
        self.__load_session_state()

        # --- Set session settings ---
        settings = self.session.get_settings()
        settings["user_agent"] = "Deluge/%(deluge_version)s libtorrent/%(lt_version)s" % {
            'deluge_version': deluge.common.get_version(),
            'lt_version': self.get_libtorrent_version().rpartition(".")[0]
        }
        # No SSL torrent support in code so disable the listen port.
        settings["ssl_listen"] = 0
        self.session.set_settings(settings)

        # --- libtorrent plugins ---
        # Allows peers to download the metadata from the swarm directly
        self.session.add_extension("metadata_transfer")
        self.session.add_extension("ut_metadata")
        # Ban peers that sends bad data
        self.session.add_extension("smart_ban")

        # Create the components
        self.eventmanager = EventManager()
        self.preferencesmanager = PreferencesManager()
        self.alertmanager = AlertManager()
        self.pluginmanager = PluginManager(self)
        self.torrentmanager = TorrentManager()
        self.filtermanager = FilterManager(self)
        self.authmanager = AuthManager()

        # New release check information
        self.new_release = None

        # Get the core config
        self.config = ConfigManager("core.conf")
        self.config.save()

        # If there was an interface value from the command line, use it, but
        # store the one in the config so we can restore it on shutdown
        self.__old_interface = None
        if listen_interface:
            if deluge.common.is_ip(listen_interface):
                self.__old_interface = self.config["listen_interface"]
                self.config["listen_interface"] = listen_interface
            else:
                log.error("Invalid listen interface (must be IP Address): %s", listen_interface)

        # New release check information
        self.__new_release = None

    def start(self):
        """Starts the core"""
        pass

    def stop(self):
        log.debug("Core stopping...")

        # Save the libtorrent session state
        self.__save_session_state()

        # We stored a copy of the old interface value
        if self.__old_interface:
            self.config["listen_interface"] = self.__old_interface

        # Make sure the config file has been saved
        self.config.save()

    def shutdown(self):
        pass

    def __save_session_state(self):
        """Saves the libtorrent session state"""
        filename = "session.state"
        filepath = get_config_dir(filename)
        filepath_bak = filepath + ".bak"
        filepath_tmp = filepath + ".tmp"

        try:
            if os.path.isfile(filepath):
                log.debug("Creating backup of %s at: %s", filename, filepath_bak)
                shutil.copy2(filepath, filepath_bak)
        except IOError as ex:
            log.error("Unable to backup %s to %s: %s", filepath, filepath_bak, ex)
        else:
            log.info("Saving the %s at: %s", filename, filepath)
            try:
                with open(filepath_tmp, "wb") as _file:
                    _file.write(lt.bencode(self.session.save_state()))
                    _file.flush()
                    os.fsync(_file.fileno())
                shutil.move(filepath_tmp, filepath)
            except (IOError, EOFError) as ex:
                log.error("Unable to save %s: %s", filename, ex)
                if os.path.isfile(filepath_bak):
                    log.info("Restoring backup of %s from: %s", filename, filepath_bak)
                    shutil.move(filepath_bak, filepath)

    def __load_session_state(self):
        """Loads the libtorrent session state"""
        filename = "session.state"
        filepath = get_config_dir(filename)
        filepath_bak = filepath + ".bak"

        for _filepath in (filepath, filepath_bak):
            log.info("Opening %s for load: %s", filename, _filepath)
            try:
                with open(_filepath, "rb") as _file:
                    state = lt.bdecode(_file.read())
            except (IOError, EOFError, RuntimeError) as ex:
                log.warning("Unable to load %s: %s", _filepath, ex)
            else:
                log.info("Successfully loaded %s: %s", filename, _filepath)
                self.session.load_state(state)
                return

    def get_new_release(self):
        log.debug("get_new_release")
        from urllib2 import urlopen, URLError
        try:
            self.new_release = urlopen("http://download.deluge-torrent.org/version-1.0").read().strip()
        except URLError as ex:
            log.debug("Unable to get release info from website: %s", ex)
            return
        self.check_new_release()

    def check_new_release(self):
        if self.new_release:
            log.debug("new_release: %s", self.new_release)
            if deluge.common.VersionSplit(self.new_release) > deluge.common.VersionSplit(deluge.common.get_version()):
                component.get("EventManager").emit(NewVersionAvailableEvent(self.new_release))
                return self.new_release
        return False

    def _add_torrent_file(self, filename, filedump, options, save_state=True):
        """Adds a torrent file to the session.

        Args:
            filename (str): The filename of the torrent.
            filedump (str): A base64 encoded string of torrent file contents.
            options (dict): The options to apply to the torrent upon adding.
            save_state (bool): If the state should be saved after adding the file.

        Returns:
            str: The torrent ID or None.

        """
        try:
            filedump = base64.decodestring(filedump)
        except Exception as ex:
            log.error("There was an error decoding the filedump string: %s", ex)

        try:
            torrent_id = self.torrentmanager.add(
                filedump=filedump, options=options, filename=filename, save_state=save_state
            )
        except RuntimeError as ex:
            log.error("There was an error adding the torrent file %s: %s", filename, ex)
            torrent_id = None
        return torrent_id

    # Exported Methods
    @export
    def add_torrent_file(self, filename, filedump, options):
        """Adds a torrent file to the session.

        Args:
            filename (str): The filename of the torrent.
            filedump (str): A base64 encoded string of the torrent file contents.
            options (dict): The options to apply to the torrent upon adding.

        Returns:
            str: The torrent_id or None.

        """
        return self._add_torrent_file(filename, filedump, options)

    @export
    def add_torrent_files(self, torrent_files):
        """Adds multiple torrent files to the session.

        Args:
            torrent_files (list of tuples): Torrent files as tuple of (filename, filedump, options).

        Returns:
            Deferred

        """
        def add_torrents():
            torrent_ids = []
            count = len(torrent_files)
            for idx, torrent in enumerate(torrent_files):
                torrent_id = self._add_torrent_file(torrent[0], torrent[1],
                                                    torrent[2], save_state=idx == (count - 1))
                torrent_ids.append(torrent_id)
            return torrent_ids
        return task.deferLater(reactor, 0, add_torrents)

    @export
    def add_torrent_url(self, url, options, headers=None):
        """
        Adds a torrent from a url. Deluge will attempt to fetch the torrent
        from url prior to adding it to the session.

        :param url: the url pointing to the torrent file
        :type url: string
        :param options: the options to apply to the torrent on add
        :type options: dict
        :param headers: any optional headers to send
        :type headers: dict

        :returns: a Deferred which returns the torrent_id as a str or None
        """
        log.info("Attempting to add url %s", url)

        def on_download_success(filename):
            # We got the file, so add it to the session
            f = open(filename, "rb")
            data = f.read()
            f.close()
            try:
                os.remove(filename)
            except OSError as ex:
                log.warning("Couldn't remove temp file: %s", ex)
            return self.add_torrent_file(filename, base64.encodestring(data), options)

        def on_download_fail(failure):
            # Log the error and pass the failure onto the client
            log.error("Failed to add torrent from url %s", url)
            return failure

        d = download_file(
            url, tempfile.mkstemp()[1], headers=headers, force_filename=True
        )
        d.addCallbacks(on_download_success, on_download_fail)
        return d

    @export
    def add_torrent_magnet(self, uri, options):
        """
        Adds a torrent from a magnet link.

        :param uri: the magnet link
        :type uri: string
        :param options: the options to apply to the torrent on add
        :type options: dict

        :returns: the torrent_id
        :rtype: string

        """
        log.debug("Attempting to add by magnet uri: %s", uri)

        return self.torrentmanager.add(magnet=uri, options=options)

    @export
    def remove_torrent(self, torrent_id, remove_data):
        """Removes a single torrent from the session.

        Args:
            torrent_id (str): The torrent ID to remove.
            remove_data (bool): If True, also remove the downloaded data.

        Returns:
            bool: True if removed successfully.

        Raises:
             InvalidTorrentError: If the torrent ID does not exist in the session.

        """
        log.debug("Removing torrent %s from the core.", torrent_id)
        return self.torrentmanager.remove(torrent_id, remove_data)

    @export
    def remove_torrents(self, torrent_ids, remove_data):
        """Remove multiple torrents from the session.

        Args:
            torrent_ids (list): The torrent IDs to remove.
            remove_data (bool, optional): If True, also remove the downloaded data.

        Returns:
            list: a list containing all the errors, empty list if no errors occured

        """
        log.info("Removing %d torrents from core.", len(torrent_ids))

        def do_remove_torrents():
            errors = []
            for torrent_id in torrent_ids:
                try:
                    self.torrentmanager.remove(torrent_id, remove_data=remove_data, save_state=False)
                except InvalidTorrentError as ex:
                    errors.append((torrent_id, ex))
            # Save the session state
            self.torrentmanager.save_state()
            return errors
        return task.deferLater(reactor, 0, do_remove_torrents)

    @export
    def get_session_status(self, keys):
        """
        Gets the session status values for 'keys', these keys are taking
        from libtorrent's session status.

        See: http://www.rasterbar.com/products/libtorrent/manual.html#status

        :param keys: the keys for which we want values
        :type keys: list
        :returns: a dictionary of {key: value, ...}
        :rtype: dict

        """
        status = {}
        session_status = self.session.status()
        for key in keys:
            status[key] = getattr(session_status, key)

        return status

    @export
    def get_cache_status(self):
        """
        Returns a dictionary of the session's cache status.

        :returns: the cache status
        :rtype: dict

        """

        status = self.session.get_cache_status()
        cache = {}
        for attr in dir(status):
            if attr.startswith("_"):
                continue
            cache[attr] = getattr(status, attr)

        # Add in a couple ratios
        try:
            cache["write_hit_ratio"] = float((cache["blocks_written"] -
                                              cache["writes"])) / float(cache["blocks_written"])
        except ZeroDivisionError:
            cache["write_hit_ratio"] = 0.0

        try:
            cache["read_hit_ratio"] = float(cache["blocks_read_hit"]) / float(cache["blocks_read"])
        except ZeroDivisionError:
            cache["read_hit_ratio"] = 0.0

        return cache

    @export
    def force_reannounce(self, torrent_ids):
        log.debug("Forcing reannouncment to: %s", torrent_ids)
        for torrent_id in torrent_ids:
            self.torrentmanager[torrent_id].force_reannounce()

    @export
    def pause_torrent(self, torrent_ids):
        log.debug("Pausing: %s", torrent_ids)
        for torrent_id in torrent_ids:
            if not self.torrentmanager[torrent_id].pause():
                log.warning("Error pausing torrent %s", torrent_id)

    @export
    def connect_peer(self, torrent_id, ip, port):
        log.debug("adding peer %s to %s", ip, torrent_id)
        if not self.torrentmanager[torrent_id].connect_peer(ip, port):
            log.warning("Error adding peer %s:%s to %s", ip, port, torrent_id)

    @export
    def move_storage(self, torrent_ids, dest):
        log.debug("Moving storage %s to %s", torrent_ids, dest)
        for torrent_id in torrent_ids:
            if not self.torrentmanager[torrent_id].move_storage(dest):
                log.warning("Error moving torrent %s to %s", torrent_id, dest)

    @export
    def pause_session(self):
        """Pause all torrents in the session"""
        if not self.session.is_paused():
            self.session.pause()
            component.get("EventManager").emit(SessionPausedEvent())

    @export
    def resume_session(self):
        """Resume all torrents in the session"""
        if self.session.is_paused():
            self.session.resume()
            for torrent_id in self.torrentmanager.torrents:
                self.torrentmanager[torrent_id].update_state()
            component.get("EventManager").emit(SessionResumedEvent())

    @export
    def resume_torrent(self, torrent_ids):
        log.debug("Resuming: %s", torrent_ids)
        for torrent_id in torrent_ids:
            self.torrentmanager[torrent_id].resume()

    def create_torrent_status(self, torrent_id, torrent_keys, plugin_keys, diff=False, update=False, all_keys=False):
        try:
            status = self.torrentmanager[torrent_id].get_status(torrent_keys, diff, update=update, all_keys=all_keys)
        except KeyError:
            import traceback
            traceback.print_exc()
            # Torrent was probaly removed meanwhile
            return {}

        # Ask the plugin manager to fill in the plugin keys
        if len(plugin_keys) > 0 or all_keys:
            status.update(self.pluginmanager.get_status(torrent_id, plugin_keys))
        return status

    @export
    def get_torrent_status(self, torrent_id, keys, diff=False):
        torrent_keys, plugin_keys = self.torrentmanager.separate_keys(keys, [torrent_id])
        return self.create_torrent_status(torrent_id, torrent_keys, plugin_keys, diff=diff, update=True,
                                          all_keys=not keys)

    @export
    def get_torrents_status(self, filter_dict, keys, diff=False):
        """
        returns all torrents , optionally filtered by filter_dict.
        """
        torrent_ids = self.filtermanager.filter_torrent_ids(filter_dict)
        d = self.torrentmanager.torrents_status_update(torrent_ids, keys, diff=diff)

        def add_plugin_fields(args):
            status_dict, plugin_keys = args
            # Ask the plugin manager to fill in the plugin keys
            if len(plugin_keys) > 0:
                for key in status_dict.keys():
                    status_dict[key].update(self.pluginmanager.get_status(key, plugin_keys))
            return status_dict
        d.addCallback(add_plugin_fields)
        return d

    @export
    def get_filter_tree(self, show_zero_hits=True, hide_cat=None):
        """
        returns {field: [(value,count)] }
        for use in sidebar(s)
        """
        return self.filtermanager.get_filter_tree(show_zero_hits, hide_cat)

    @export
    def get_session_state(self):
        """Returns a list of torrent_ids in the session."""
        # Get the torrent list from the TorrentManager
        return self.torrentmanager.get_torrent_list()

    @export
    def get_config(self):
        """Get all the preferences as a dictionary"""
        return self.config.config

    @export
    def get_config_value(self, key):
        """Get the config value for key"""
        return self.config.get(key)

    @export
    def get_config_values(self, keys):
        """Get the config values for the entered keys"""
        return dict((key, self.config.get(key)) for key in keys)

    @export
    def set_config(self, config):
        """Set the config with values from dictionary"""
        # Load all the values into the configuration
        for key in config.keys():
            if isinstance(config[key], basestring):
                config[key] = config[key].encode("utf8")
            self.config[key] = config[key]

    @export
    def get_listen_port(self):
        """Returns the active listen port"""
        return self.session.listen_port()

    @export
    def get_i2p_proxy(self):
        """Returns the active listen port"""
        i2p_settings = self.session.i2p_proxy()
        i2p_dict = {"hostname": i2p_settings.hostname, "port": i2p_settings.port}
        return i2p_dict

    @export
    def get_proxy(self):
        """Returns the active listen port"""
        proxy_settings = self.session.proxy()
        proxy_dict = {
            "type": int(proxy_settings.type),
            "hostname": proxy_settings.hostname,
            "username": proxy_settings.username,
            "password": proxy_settings.password,
            "port": proxy_settings.port,
            "proxy_hostnames": proxy_settings.proxy_hostnames,
            "proxy_peer_connections": proxy_settings.proxy_peer_connections
        }
        return proxy_dict

    @export
    def get_available_plugins(self):
        """Returns a list of plugins available in the core"""
        return self.pluginmanager.get_available_plugins()

    @export
    def get_enabled_plugins(self):
        """Returns a list of enabled plugins in the core"""
        return self.pluginmanager.get_enabled_plugins()

    @export
    def enable_plugin(self, plugin):
        self.pluginmanager.enable_plugin(plugin)
        return None

    @export
    def disable_plugin(self, plugin):
        self.pluginmanager.disable_plugin(plugin)
        return None

    @export
    def force_recheck(self, torrent_ids):
        """Forces a data recheck on torrent_ids"""
        for torrent_id in torrent_ids:
            self.torrentmanager[torrent_id].force_recheck()

    @export
    def set_torrent_options(self, torrent_ids, options):
        """Sets the torrent options for torrent_ids"""
        for torrent_id in torrent_ids:
            self.torrentmanager[torrent_id].set_options(options)

    @export
    def set_torrent_trackers(self, torrent_id, trackers):
        """Sets a torrents tracker list.  trackers will be [{"url", "tier"}]"""
        return self.torrentmanager[torrent_id].set_trackers(trackers)

    @export
    def set_torrent_max_connections(self, torrent_id, value):
        # Deprecated method, use set_torrent_options instead
        """Sets a torrents max number of connections"""
        return self.torrentmanager[torrent_id].set_max_connections(value)

    @export
    def set_torrent_max_upload_slots(self, torrent_id, value):
        # Deprecated method, use set_torrent_options instead
        """Sets a torrents max number of upload slots"""
        return self.torrentmanager[torrent_id].set_max_upload_slots(value)

    @export
    def set_torrent_max_upload_speed(self, torrent_id, value):
        # Deprecated method, use set_torrent_options instead
        """Sets a torrents max upload speed"""
        return self.torrentmanager[torrent_id].set_max_upload_speed(value)

    @export
    def set_torrent_max_download_speed(self, torrent_id, value):
        # Deprecated method, use set_torrent_options instead
        """Sets a torrents max download speed"""
        return self.torrentmanager[torrent_id].set_max_download_speed(value)

    @export
    def set_torrent_file_priorities(self, torrent_id, priorities):
        # Deprecated method, use set_torrent_options instead
        # Used by at least one 3rd party plugin:
        """Sets a torrents file priorities"""
        return self.torrentmanager[torrent_id].set_file_priorities(priorities)

    @export
    def set_torrent_prioritize_first_last(self, torrent_id, value):
        # Deprecated method, use set_torrent_options instead
        """Sets a higher priority to the first and last pieces"""
        return self.torrentmanager[torrent_id].set_prioritize_first_last_pieces(value)

    @export
    def set_torrent_auto_managed(self, torrent_id, value):
        # Deprecated method, use set_torrent_options instead
        """Sets the auto managed flag for queueing purposes"""
        return self.torrentmanager[torrent_id].set_auto_managed(value)

    @export
    def set_torrent_stop_at_ratio(self, torrent_id, value):
        # Deprecated method, use set_torrent_options instead
        """Sets the torrent to stop at 'stop_ratio'"""
        return self.torrentmanager[torrent_id].set_stop_at_ratio(value)

    @export
    def set_torrent_stop_ratio(self, torrent_id, value):
        # Deprecated method, use set_torrent_options instead
        """Sets the ratio when to stop a torrent if 'stop_at_ratio' is set"""
        return self.torrentmanager[torrent_id].set_stop_ratio(value)

    @export
    def set_torrent_remove_at_ratio(self, torrent_id, value):
        # Deprecated method, use set_torrent_options instead
        """Sets the torrent to be removed at 'stop_ratio'"""
        return self.torrentmanager[torrent_id].set_remove_at_ratio(value)

    @export
    def set_torrent_move_completed(self, torrent_id, value):
        # Deprecated method, use set_torrent_options instead
        """Sets the torrent to be moved when completed"""
        return self.torrentmanager[torrent_id].set_move_completed(value)

    @export
    def set_torrent_move_completed_path(self, torrent_id, value):
        # Deprecated method, use set_torrent_options instead
        """Sets the path for the torrent to be moved when completed"""
        return self.torrentmanager[torrent_id].set_move_completed_path(value)

    @export(AUTH_LEVEL_ADMIN)
    def set_owner(self, torrent_ids, username):
        """Set's the torrent owner.

        :param torrent_id: the torrent_id of the torrent to remove
        :type torrent_id: string
        :param username: the new owner username
        :type username: string

        :raises DelugeError: if the username is not known
        """
        if not self.authmanager.has_account(username):
            raise DelugeError("Username \"%s\" is not known." % username)
        if isinstance(torrent_ids, basestring):
            torrent_ids = [torrent_ids]
        for torrent_id in torrent_ids:
            self.torrentmanager[torrent_id].set_owner(username)
        return None

    @export
    def get_path_size(self, path):
        """Returns the size of the file or folder 'path' and -1 if the path is
        unaccessible (non-existent or insufficient privs)"""
        return deluge.common.get_path_size(path)

    @export
    def create_torrent(self, path, tracker, piece_length, comment, target,
                       webseeds, private, created_by, trackers, add_to_session):

        log.debug("creating torrent..")
        threading.Thread(target=self._create_torrent_thread,
                         args=(
                             path,
                             tracker,
                             piece_length,
                             comment,
                             target,
                             webseeds,
                             private,
                             created_by,
                             trackers,
                             add_to_session)).start()

    def _create_torrent_thread(self, path, tracker, piece_length, comment, target,
                               webseeds, private, created_by, trackers, add_to_session):
        from deluge import metafile
        metafile.make_meta_file(
            path,
            tracker,
            piece_length,
            comment=comment,
            target=target,
            webseeds=webseeds,
            private=private,
            created_by=created_by,
            trackers=trackers)
        log.debug("torrent created!")
        if add_to_session:
            options = {}
            options["download_location"] = os.path.split(path)[0]
            self.add_torrent_file(os.path.split(target)[1], open(target, "rb").read(), options)

    @export
    def upload_plugin(self, filename, filedump):
        """This method is used to upload new plugins to the daemon.  It is used
        when connecting to the daemon remotely and installing a new plugin on
        the client side. 'plugin_data' is a xmlrpc.Binary object of the file data,
        ie, plugin_file.read()"""

        try:
            filedump = base64.decodestring(filedump)
        except Exception as ex:
            log.error("There was an error decoding the filedump string!")
            log.exception(ex)
            return

        f = open(os.path.join(get_config_dir(), "plugins", filename), "wb")
        f.write(filedump)
        f.close()
        component.get("CorePluginManager").scan_for_plugins()

    @export
    def rescan_plugins(self):
        """
        Rescans the plugin folders for new plugins
        """
        component.get("CorePluginManager").scan_for_plugins()

    @export
    def rename_files(self, torrent_id, filenames):
        """
        Rename files in torrent_id.  Since this is an asynchronous operation by
        libtorrent, watch for the TorrentFileRenamedEvent to know when the
        files have been renamed.

        :param torrent_id: the torrent_id to rename files
        :type torrent_id: string
        :param filenames: a list of index, filename pairs
        :type filenames: ((index, filename), ...)

        :raises InvalidTorrentError: if torrent_id is invalid

        """
        if torrent_id not in self.torrentmanager.torrents:
            raise InvalidTorrentError("torrent_id is not in session")

        self.torrentmanager[torrent_id].rename_files(filenames)

    @export
    def rename_folder(self, torrent_id, folder, new_folder):
        """
        Renames the 'folder' to 'new_folder' in 'torrent_id'.  Watch for the
        TorrentFolderRenamedEvent which is emitted when the folder has been
        renamed successfully.

        :param torrent_id: the torrent to rename folder in
        :type torrent_id: string
        :param folder: the folder to rename
        :type folder: string
        :param new_folder: the new folder name
        :type new_folder: string

        :raises InvalidTorrentError: if the torrent_id is invalid

        """
        if torrent_id not in self.torrentmanager.torrents:
            raise InvalidTorrentError("torrent_id is not in session")

        self.torrentmanager[torrent_id].rename_folder(folder, new_folder)

    @export
    def queue_top(self, torrent_ids):
        log.debug("Attempting to queue %s to top", torrent_ids)
        # torrent_ids must be sorted in reverse before moving to preserve order
        for torrent_id in sorted(torrent_ids, key=self.torrentmanager.get_queue_position, reverse=True):
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrentmanager.queue_top(torrent_id):
                    component.get("EventManager").emit(TorrentQueueChangedEvent())
            except KeyError:
                log.warning("torrent_id: %s does not exist in the queue", torrent_id)

    @export
    def queue_up(self, torrent_ids):
        log.debug("Attempting to queue %s to up", torrent_ids)
        torrents = ((self.torrentmanager.get_queue_position(torrent_id), torrent_id) for torrent_id in torrent_ids)
        torrent_moved = True
        prev_queue_position = None
        # torrent_ids must be sorted before moving.
        for queue_position, torrent_id in sorted(torrents):
            # Move the torrent if and only if there is space (by not moving it we preserve the order)
            if torrent_moved or queue_position - prev_queue_position > 1:
                try:
                    torrent_moved = self.torrentmanager.queue_up(torrent_id)
                except KeyError:
                    log.warning("torrent_id: %s does not exist in the queue", torrent_id)
            # If the torrent moved, then we should emit a signal
            if torrent_moved:
                component.get("EventManager").emit(TorrentQueueChangedEvent())
            else:
                prev_queue_position = queue_position

    @export
    def queue_down(self, torrent_ids):
        log.debug("Attempting to queue %s to down", torrent_ids)
        torrents = ((self.torrentmanager.get_queue_position(torrent_id), torrent_id) for torrent_id in torrent_ids)
        torrent_moved = True
        prev_queue_position = None
        # torrent_ids must be sorted before moving.
        for queue_position, torrent_id in sorted(torrents, reverse=True):
            # Move the torrent if and only if there is space (by not moving it we preserve the order)
            if torrent_moved or prev_queue_position - queue_position > 1:
                try:
                    torrent_moved = self.torrentmanager.queue_down(torrent_id)
                except KeyError:
                    log.warning("torrent_id: %s does not exist in the queue", torrent_id)
            # If the torrent moved, then we should emit a signal
            if torrent_moved:
                component.get("EventManager").emit(TorrentQueueChangedEvent())
            else:
                prev_queue_position = queue_position

    @export
    def queue_bottom(self, torrent_ids):
        log.debug("Attempting to queue %s to bottom", torrent_ids)
        # torrent_ids must be sorted before moving to preserve order
        for torrent_id in sorted(torrent_ids, key=self.torrentmanager.get_queue_position):
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrentmanager.queue_bottom(torrent_id):
                    component.get("EventManager").emit(TorrentQueueChangedEvent())
            except KeyError:
                log.warning("torrent_id: %s does not exist in the queue", torrent_id)

    @export
    def glob(self, path):
        return glob.glob(path)

    @export
    def test_listen_port(self):
        """
        Checks if the active port is open

        :returns: True if the port is open, False if not
        :rtype: bool

        """
        d = getPage("http://deluge-torrent.org/test_port.php?port=%s" %
                    self.get_listen_port(), timeout=30)

        def on_get_page(result):
            return bool(int(result))

        def on_error(failure):
            log.warning("Error testing listen port: %s", failure)

        d.addCallback(on_get_page)
        d.addErrback(on_error)

        return d

    @export
    def get_free_space(self, path=None):
        """
        Returns the number of free bytes at path

        :param path: the path to check free space at, if None, use the default download location
        :type path: string

        :returns: the number of free bytes at path
        :rtype: int

        :raises InvalidPathError: if the path is invalid

        """
        if not path:
            path = self.config["download_location"]
        try:
            return deluge.common.free_space(path)
        except InvalidPathError:
            return -1

    @export
    def get_libtorrent_version(self):
        """
        Returns the libtorrent version.

        :returns: the version
        :rtype: string

        """
        return lt.version

    @export
    def get_completion_paths(self, args):
        """
        Returns the available path completions for the input value.
        """
        return path_chooser_common.get_completion_paths(args)

    @export(AUTH_LEVEL_ADMIN)
    def get_known_accounts(self):
        return self.authmanager.get_known_accounts()

    @export(AUTH_LEVEL_NONE)
    def get_auth_levels_mappings(self):
        return (AUTH_LEVELS_MAPPING, AUTH_LEVELS_MAPPING_REVERSE)

    @export(AUTH_LEVEL_ADMIN)
    def create_account(self, username, password, authlevel):
        return self.authmanager.create_account(username, password, authlevel)

    @export(AUTH_LEVEL_ADMIN)
    def update_account(self, username, password, authlevel):
        return self.authmanager.update_account(username, password, authlevel)

    @export(AUTH_LEVEL_ADMIN)
    def remove_account(self, username):
        return self.authmanager.remove_account(username)
