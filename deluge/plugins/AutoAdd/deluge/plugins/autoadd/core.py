# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 GazpachoKing <chase.sterling@gmail.com>
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import base64
import logging
import os
import shutil

from twisted.internet import reactor
from twisted.internet.task import LoopingCall, deferLater

import deluge.component as component
import deluge.configmanager
from deluge._libtorrent import lt
from deluge.common import AUTH_LEVEL_ADMIN
from deluge.core.rpcserver import export
from deluge.event import DelugeEvent
from deluge.plugins.pluginbase import CorePluginBase

log = logging.getLogger(__name__)


DEFAULT_PREFS = {
    "watchdirs": {},
    "next_id": 1
}


OPTIONS_AVAILABLE = {  # option: builtin
    "enabled": False,
    "path": False,
    "append_extension": False,
    "copy_torrent": False,
    "delete_copy_torrent_toggle": False,
    "abspath": False,
    "download_location": True,
    "max_download_speed": True,
    "max_upload_speed": True,
    "max_connections": True,
    "max_upload_slots": True,
    "prioritize_first_last": True,
    "auto_managed": True,
    "stop_at_ratio": True,
    "stop_ratio": True,
    "remove_at_ratio": True,
    "move_completed": True,
    "move_completed_path": True,
    "label": False,
    "add_paused": True,
    "queue_to_top": False,
    "owner": True,
    "seed_mode": True
}

MAX_NUM_ATTEMPTS = 10


class AutoaddOptionsChangedEvent(DelugeEvent):
    """Emitted when the options for the plugin are changed."""
    def __init__(self):
        pass


def check_input(cond, message):
    if not cond:
        raise Exception(message)


class Core(CorePluginBase):
    def enable(self):

        # reduce typing, assigning some values to self...
        self.config = deluge.configmanager.ConfigManager("autoadd.conf", DEFAULT_PREFS)
        self.config.run_converter((0, 1), 2, self.__migrate_config_1_to_2)
        self.config.save()
        self.watchdirs = self.config["watchdirs"]

        component.get("EventManager").register_event_handler(
            "PreTorrentRemovedEvent", self.__on_pre_torrent_removed
        )

        # Dict of Filename:Attempts
        self.invalid_torrents = {}
        # Loopingcall timers for each enabled watchdir
        self.update_timers = {}
        deferLater(reactor, 5, self.enable_looping)

    def enable_looping(self):
        # Enable all looping calls for enabled watchdirs here
        for watchdir_id, watchdir in self.watchdirs.iteritems():
            if watchdir["enabled"]:
                self.enable_watchdir(watchdir_id)

    def disable(self):
        # disable all running looping calls
        component.get("EventManager").deregister_event_handler(
            "PreTorrentRemovedEvent", self.__on_pre_torrent_removed
        )
        for loopingcall in self.update_timers.itervalues():
            loopingcall.stop()
        self.config.save()

    def update(self):
        pass

    @export
    def set_options(self, watchdir_id, options):
        """Update the options for a watch folder."""
        watchdir_id = str(watchdir_id)
        options = self._make_unicode(options)
        check_input(
            watchdir_id in self.watchdirs, _("Watch folder does not exist.")
        )
        if "path" in options:
            options["abspath"] = os.path.abspath(options["path"])
            check_input(
                os.path.isdir(options["abspath"]), _("Path does not exist.")
            )
            for w_id, w in self.watchdirs.iteritems():
                if options["abspath"] == w["abspath"] and watchdir_id != w_id:
                    raise Exception("Path is already being watched.")
        for key in options.keys():
            if key not in OPTIONS_AVAILABLE:
                if key not in [key2 + "_toggle" for key2 in OPTIONS_AVAILABLE.iterkeys()]:
                    raise Exception("autoadd: Invalid options key:%s" % key)
        # disable the watch loop if it was active
        if watchdir_id in self.update_timers:
            self.disable_watchdir(watchdir_id)

        self.watchdirs[watchdir_id].update(options)
        # re-enable watch loop if appropriate
        if self.watchdirs[watchdir_id]["enabled"]:
            self.enable_watchdir(watchdir_id)
        self.config.save()
        component.get("EventManager").emit(AutoaddOptionsChangedEvent())

    def load_torrent(self, filename, magnet):
        try:
            log.debug("Attempting to open %s for add.", filename)
            if magnet:
                _file = open(filename, "r")
            else:
                _file = open(filename, "rb")

            filedump = _file.read()
            if not filedump:
                raise RuntimeError("Torrent is 0 bytes!")
            _file.close()
        except IOError as ex:
            log.warning("Unable to open %s: %s", filename, ex)
            raise ex

        # Get the info to see if any exceptions are raised
        if not magnet:
            lt.torrent_info(lt.bdecode(filedump))

        return base64.encodestring(filedump)

    def split_magnets(self, filename):
        log.debug("Attempting to open %s for splitting magnets.", filename)
        try:
            _file = open(filename, "r")
        except IOError as ex:
            log.warning("Unable to open %s: %s", filename, ex)
            raise ex
        else:
            magnets = list(filter(len, _file.readlines()))
            _file.close()
            if len(magnets) < 2:
                return
            n = 0
            path = filename.rsplit(os.sep, 1)[0]
            for magnet in magnets:
                for part in magnet.split("&"):
                    if part.startswith("dn="):
                        mname = os.sep.join([path, part[3:] + ".magnet"])
                        break
                else:
                    mname = ".".join([filename, str(n), "magnet"])
                    n += 1
                try:
                    _mfile = open(mname, "w")
                except IOError as ex:
                    log.warning("Unable to open %s: %s", mname, ex)
                else:
                    _mfile.write(magnet)
                    _mfile.close()
            return magnets

    def update_watchdir(self, watchdir_id):
        """Check the watch folder for new torrents to add."""
        log.trace("Updating watchdir id: %s", watchdir_id)
        watchdir_id = str(watchdir_id)
        watchdir = self.watchdirs[watchdir_id]
        if not watchdir["enabled"]:
            # We shouldn't be updating because this watchdir is not enabled
            log.debug("Watchdir id %s is not enabled. Disabling it.",
                      watchdir_id)
            self.disable_watchdir(watchdir_id)
            return

        if not os.path.isdir(watchdir["abspath"]):
            log.warning("Invalid AutoAdd folder: %s", watchdir["abspath"])
            self.disable_watchdir(watchdir_id)
            return

        # Generate options dict for watchdir
        opts = {}
        if "stop_at_ratio_toggle" in watchdir:
            watchdir["stop_ratio_toggle"] = watchdir["stop_at_ratio_toggle"]
        # We default to True when reading _toggle values, so a config
        # without them is valid, and applies all its settings.
        for option, value in watchdir.iteritems():
            if OPTIONS_AVAILABLE.get(option):
                if watchdir.get(option + "_toggle", True) or option in ["owner", "seed_mode"]:
                    opts[option] = value

        # Check for .magnet files containing multiple magnet links and
        # create a new .magnet file for each of them.
        for filename in os.listdir(watchdir["abspath"]):
            try:
                filepath = os.path.join(watchdir["abspath"], filename)
            except UnicodeDecodeError as ex:
                log.error("Unable to auto add torrent due to improper filename encoding: %s", ex)
                continue
            if os.path.isdir(filepath):
                # Skip directories
                continue
            elif os.path.splitext(filename)[1] == ".magnet" and \
                    self.split_magnets(filepath):
                os.remove(filepath)

        for filename in os.listdir(watchdir["abspath"]):
            try:
                filepath = os.path.join(watchdir["abspath"], filename)
            except UnicodeDecodeError as ex:
                log.error("Unable to auto add torrent due to improper filename encoding: %s", ex)
                continue
            if os.path.isdir(filepath):
                # Skip directories
                continue
            else:
                ext = os.path.splitext(filename)[1]
                if ext == ".torrent":
                    magnet = False
                elif ext == ".magnet":
                    magnet = True
                else:
                    continue
                try:
                    filedump = self.load_torrent(filepath, magnet)
                except (RuntimeError, Exception) as ex:
                    # If the torrent is invalid, we keep track of it so that we
                    # can try again on the next pass.  This is because some
                    # torrents may not be fully saved during the pass.
                    log.debug("Torrent is invalid: %s", ex)
                    if filename in self.invalid_torrents:
                        self.invalid_torrents[filename] += 1
                        if self.invalid_torrents[filename] >= MAX_NUM_ATTEMPTS:
                            log.warning(
                                "Maximum attempts reached while trying to add the "
                                "torrent file with the path %s", filepath
                            )
                            os.rename(filepath, filepath + ".invalid")
                            del self.invalid_torrents[filename]
                    else:
                        self.invalid_torrents[filename] = 1
                    continue

                # The torrent looks good, so lets add it to the session.
                if magnet:
                    torrent_id = component.get("Core").add_torrent_magnet(filedump, opts)
                else:
                    torrent_id = component.get("Core").add_torrent_file(filename, filedump, opts)

                # If the torrent added successfully, set the extra options.
                if torrent_id:
                    if "Label" in component.get("CorePluginManager").get_enabled_plugins():
                        if watchdir.get("label_toggle", True) and watchdir.get("label"):
                            label = component.get("CorePlugin.Label")
                            if not watchdir["label"] in label.get_labels():
                                label.add(watchdir["label"])
                            label.set_torrent(torrent_id, watchdir["label"])
                    if watchdir.get("queue_to_top_toggle", True) and "queue_to_top" in watchdir:
                        if watchdir["queue_to_top"]:
                            component.get("TorrentManager").queue_top(torrent_id)
                        else:
                            component.get("TorrentManager").queue_bottom(torrent_id)
                else:
                    # torrent handle is invalid and so is the magnet link
                    if magnet:
                        log.debug("invalid magnet link")
                        os.rename(filepath, filepath + ".invalid")
                        continue

                # Rename, copy or delete the torrent once added to deluge.
                if watchdir.get("append_extension_toggle"):
                    if not watchdir.get("append_extension"):
                        watchdir["append_extension"] = ".added"
                    os.rename(filepath, filepath + watchdir["append_extension"])
                elif watchdir.get("copy_torrent_toggle"):
                    copy_torrent_path = watchdir["copy_torrent"]
                    copy_torrent_file = os.path.join(copy_torrent_path, filename)
                    log.debug("Moving added torrent file \"%s\" to \"%s\"",
                              os.path.basename(filepath), copy_torrent_path)
                    shutil.move(filepath, copy_torrent_file)

                else:
                    os.remove(filepath)

    def on_update_watchdir_error(self, failure, watchdir_id):
        """Disables any watch folders with un-handled exceptions."""
        self.disable_watchdir(watchdir_id)
        log.error("Disabling '%s', error during update: %s",
                  self.watchdirs[watchdir_id]["path"], failure)

    @export
    def enable_watchdir(self, watchdir_id):
        w_id = str(watchdir_id)
        # Enable the looping call
        if w_id not in self.update_timers or not self.update_timers[w_id].running:
            self.update_timers[w_id] = LoopingCall(self.update_watchdir, w_id)
            self.update_timers[w_id].start(5).addErrback(
                self.on_update_watchdir_error, w_id
            )
        # Update the config
        if not self.watchdirs[w_id]["enabled"]:
            self.watchdirs[w_id]["enabled"] = True
            self.config.save()
            component.get("EventManager").emit(AutoaddOptionsChangedEvent())

    @export
    def disable_watchdir(self, watchdir_id):
        w_id = str(watchdir_id)
        # Disable the looping call
        if w_id in self.update_timers:
            if self.update_timers[w_id].running:
                self.update_timers[w_id].stop()
            del self.update_timers[w_id]
        # Update the config
        if self.watchdirs[w_id]["enabled"]:
            self.watchdirs[w_id]["enabled"] = False
            self.config.save()
            component.get("EventManager").emit(AutoaddOptionsChangedEvent())

    @export
    def set_config(self, config):
        """Sets the config dictionary."""
        config = self._make_unicode(config)
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()
        component.get("EventManager").emit(AutoaddOptionsChangedEvent())

    @export
    def get_config(self):
        """Returns the config dictionary."""
        return self.config.config

    @export
    def get_watchdirs(self):
        rpcserver = component.get("RPCServer")
        session_user = rpcserver.get_session_user()
        session_auth_level = rpcserver.get_session_auth_level()
        if session_auth_level == AUTH_LEVEL_ADMIN:
            log.debug("Current logged in user %s is an ADMIN, send all "
                      "watchdirs", session_user)
            return self.watchdirs

        watchdirs = {}
        for watchdir_id, watchdir in self.watchdirs.iteritems():
            if watchdir.get("owner", "localclient") == session_user:
                watchdirs[watchdir_id] = watchdir

        log.debug("Current logged in user %s is not an ADMIN, send only "
                  "his watchdirs: %s", session_user, watchdirs.keys())
        return watchdirs

    def _make_unicode(self, options):
        opts = {}
        for key in options:
            if isinstance(options[key], str):
                options[key] = unicode(options[key], "utf8")
            opts[key] = options[key]
        return opts

    @export
    def add(self, options={}):
        """Add a watch folder."""
        options = self._make_unicode(options)
        abswatchdir = os.path.abspath(options["path"])
        check_input(os.path.isdir(abswatchdir), _("Path does not exist."))
        check_input(
            os.access(abswatchdir, os.R_OK | os.W_OK),
            "You must have read and write access to watch folder."
        )
        if abswatchdir in [wd["abspath"] for wd in self.watchdirs.itervalues()]:
            raise Exception("Path is already being watched.")
        options.setdefault("enabled", False)
        options["abspath"] = abswatchdir
        watchdir_id = self.config["next_id"]
        self.watchdirs[str(watchdir_id)] = options
        if options.get("enabled"):
            self.enable_watchdir(watchdir_id)
        self.config["next_id"] = watchdir_id + 1
        self.config.save()
        component.get("EventManager").emit(AutoaddOptionsChangedEvent())
        return watchdir_id

    @export
    def remove(self, watchdir_id):
        """Remove a watch folder."""
        watchdir_id = str(watchdir_id)
        check_input(watchdir_id in self.watchdirs, "Unknown Watchdir: %s" % self.watchdirs)
        if self.watchdirs[watchdir_id]["enabled"]:
            self.disable_watchdir(watchdir_id)
        del self.watchdirs[watchdir_id]
        self.config.save()
        component.get("EventManager").emit(AutoaddOptionsChangedEvent())

    def __migrate_config_1_to_2(self, config):
        for watchdir_id in config["watchdirs"].iterkeys():
            config["watchdirs"][watchdir_id]["owner"] = "localclient"
        return config

    def __on_pre_torrent_removed(self, torrent_id):
        try:
            torrent = component.get("TorrentManager")[torrent_id]
        except KeyError:
            log.warning("Unable to remove torrent file for torrent id %s. It"
                        "was already deleted from the TorrentManager",
                        torrent_id)
            return
        torrent_fname = torrent.filename
        for watchdir in self.watchdirs.itervalues():
            if not watchdir.get("copy_torrent_toggle", False):
                # This watchlist does copy torrents
                continue
            elif not watchdir.get("delete_copy_torrent_toggle", False):
                # This watchlist is not set to delete finished torrents
                continue
            copy_torrent_path = watchdir["copy_torrent"]
            torrent_fname_path = os.path.join(copy_torrent_path, torrent_fname)
            if os.path.isfile(torrent_fname_path):
                try:
                    os.remove(torrent_fname_path)
                    log.info("Removed torrent file \"%s\" from \"%s\"",
                             torrent_fname, copy_torrent_path)
                    break
                except OSError as ex:
                    log.info("Failed to removed torrent file \"%s\" from "
                             "\"%s\": %s", torrent_fname, copy_torrent_path, ex)
