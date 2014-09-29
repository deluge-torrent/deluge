# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging
import os

from twisted.internet.utils import getProcessValue
from twisted.python.procutils import which

import deluge.component as component
import deluge.configmanager
from deluge.common import windows_check
from deluge.core.rpcserver import export
from deluge.plugins.pluginbase import CorePluginBase

log = logging.getLogger(__name__)

DEFAULT_PREFS = {
    "extract_path": "",
    "use_name_folder": True
}

if windows_check():
    win_7z_exes = [
        '7z.exe',
        'C:\\Program Files\\7-Zip\\7z.exe',
        'C:\\Program Files (x86)\\7-Zip\\7z.exe',
    ]

    import _winreg
    try:
        hkey = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Software\\7-Zip")
    except WindowsError:
        pass
    else:
        win_7z_path = os.path.join(_winreg.QueryValueEx(hkey, "Path")[0], "7z.exe")
        _winreg.CloseKey(hkey)
        win_7z_exes.insert(1, win_7z_path)

    switch_7z = "x -y"
    # Future suport:
    # 7-zip cannot extract tar.* with single command.
    #    ".tar.gz", ".tgz",
    #    ".tar.bz2", ".tbz",
    #    ".tar.lzma", ".tlz",
    #    ".tar.xz", ".txz",
    exts_7z = [
        ".rar", ".zip", ".tar",
        ".7z", ".xz", ".lzma",
    ]
    for win_7z_exe in win_7z_exes:
        if which(win_7z_exe):
            EXTRACT_COMMANDS = dict.fromkeys(exts_7z, [win_7z_exe, switch_7z])
            break
else:
    required_cmds = ["unrar", "unzip", "tar", "unxz", "unlzma", "7zr", "bunzip2"]
    # Possible future suport:
    # gunzip: gz (cmd will delete original archive)
    # the following do not extract to dest dir
    # ".xz": ["xz", "-d --keep"],
    # ".lzma": ["xz", "-d --format=lzma --keep"],
    # ".bz2": ["bzip2", "-d --keep"],

    EXTRACT_COMMANDS = {
        ".rar": ["unrar", "x -o+ -y"],
        ".tar": ["tar", "-xf"],
        ".zip": ["unzip", ""],
        ".tar.gz": ["tar", "-xzf"], ".tgz": ["tar", "-xzf"],
        ".tar.bz2": ["tar", "-xjf"], ".tbz": ["tar", "-xjf"],
        ".tar.lzma": ["tar", "--lzma -xf"], ".tlz": ["tar", "--lzma -xf"],
        ".tar.xz": ["tar", "--xz -xf"], ".txz": ["tar", "--xz -xf"],
        ".7z": ["7zr", "x"],
    }
    # Test command exists and if not, remove.
    for cmd in required_cmds:
        if not which(cmd):
            for k, v in EXTRACT_COMMANDS.items():
                if cmd in v[0]:
                    log.warning("%s not found, disabling support for %s", cmd, k)
                    del EXTRACT_COMMANDS[k]

if not EXTRACT_COMMANDS:
    raise Exception("No archive extracting programs found, plugin will be disabled")


class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager("extractor.conf", DEFAULT_PREFS)
        if not self.config["extract_path"]:
            self.config["extract_path"] = deluge.configmanager.ConfigManager("core.conf")["download_location"]
        component.get("EventManager").register_event_handler("TorrentFinishedEvent", self._on_torrent_finished)

    def disable(self):
        component.get("EventManager").deregister_event_handler("TorrentFinishedEvent", self._on_torrent_finished)

    def update(self):
        pass

    def _on_torrent_finished(self, torrent_id):
        """
        This is called when a torrent finishes and checks if any files to extract.
        """
        tid = component.get("TorrentManager").torrents[torrent_id]
        tid_status = tid.get_status(["download_location", "name"])

        files = tid.get_files()
        for f in files:
            file_root, file_ext = os.path.splitext(f["path"])
            file_ext_sec = os.path.splitext(file_root)[1]
            if file_ext_sec and file_ext_sec + file_ext in EXTRACT_COMMANDS:
                file_ext = file_ext_sec + file_ext
            elif file_ext not in EXTRACT_COMMANDS or file_ext_sec == '.tar':
                log.warning("Can't extract file with unknown file type: %s" % f["path"])
                continue
            cmd = EXTRACT_COMMANDS[file_ext]

            # Now that we have the cmd, lets run it to extract the files
            fpath = os.path.join(tid_status["download_location"], os.path.normpath(f["path"]))

            # Get the destination path
            dest = os.path.normpath(self.config["extract_path"])
            if self.config["use_name_folder"]:
                name = tid_status["name"]
                dest = os.path.join(dest, name)

            # Create the destination folder if it doesn't exist
            if not os.path.exists(dest):
                try:
                    os.makedirs(dest)
                except OSError as ex:
                    log.error("Error creating destination folder: %s", ex)
                    return

            def on_extract_success(result, torrent_id, fpath):
                # XXX: Emit an event
                log.info("Extract successful: %s (%s)", fpath, torrent_id)

            def on_extract_failed(result, torrent_id, fpath):
                # XXX: Emit an event
                log.error("Extract failed: %s (%s)", fpath, torrent_id)

            # Run the command and add some callbacks
            log.debug("Extracting %s with %s %s to %s", fpath, cmd[0], cmd[1], dest)
            d = getProcessValue(cmd[0], cmd[1].split() + [str(fpath)], {}, str(dest))
            d.addCallback(on_extract_success, torrent_id, fpath)
            d.addErrback(on_extract_failed, torrent_id, fpath)

    @export
    def set_config(self, config):
        "sets the config dictionary"
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        "returns the config dictionary"
        return self.config.config
