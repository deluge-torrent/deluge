#
# core.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
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

import errno
import os

from twisted.internet.utils import getProcessOutputAndValue

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
from deluge.common import windows_check
from extractor.which import which

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
    ## Future suport:
    ## 7-zip cannot extract tar.* with single command.
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
    required_cmds=["unrar", "unzip", "tar", "unxz", "unlzma", "7zr", "bunzip2"]
    ## Possible future suport:
    # gunzip: gz (cmd will delete original archive)
    ## the following do not extract to dest dir
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
            for k,v in EXTRACT_COMMANDS.items():
                if cmd in v[0]:
                    log.warning("EXTRACTOR: %s not found, disabling support for %s", cmd, k)
                    del EXTRACT_COMMANDS[k]

if not EXTRACT_COMMANDS:
    raise Exception("EXTRACTOR: No archive extracting programs found, plugin will be disabled")

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
        tid_status = tid.get_status(["save_path", "name"])

        files = tid.get_files()
        for f in files:
            file_root, file_ext = os.path.splitext(f["path"])
            file_ext_sec = os.path.splitext(file_root)[1]
            if file_ext_sec and file_ext_sec + file_ext in EXTRACT_COMMANDS:
                file_ext = file_ext_sec + file_ext
            elif file_ext not in EXTRACT_COMMANDS or file_ext_sec == '.tar':
                log.debug("EXTRACTOR: Can't extract file with unknown file type: %s", f["path"])
                continue
            elif file_ext == ".rar" and "part" in file_ext_sec:
                part_num = file_ext_sec.split("part")[1]
                if part_num.isdigit() and int(part_num) != 1:
                    log.debug("Skipping remaining multi-part rar files: %s", f["path"])
                    continue

            cmd = EXTRACT_COMMANDS[file_ext]
            fpath = os.path.join(tid_status["save_path"], os.path.normpath(f["path"]))
            dest = os.path.normpath(self.config["extract_path"])
            if self.config["use_name_folder"]:
                dest = os.path.join(dest, tid_status["name"])

            try:
                os.makedirs(dest)
            except OSError, ex:
                if not (ex.errno == errno.EEXIST and os.path.isdir(dest)):
                    log.error("EXTRACTOR: Error creating destination folder: %s", ex)
                    break

            def on_extract(result, torrent_id, fpath):
                # Check command exit code.
                if not result[2]:
                    log.info("EXTRACTOR: Extract successful: %s (%s)", fpath, torrent_id)
                else:
                    log.error("EXTRACTOR: Extract failed: %s (%s) %s", fpath, torrent_id, result[1])

            # Run the command and add callback.
            log.debug("EXTRACTOR: Extracting %s from %s with %s %s to %s", fpath, torrent_id, cmd[0], cmd[1], dest)
            d = getProcessOutputAndValue(cmd[0], cmd[1].split() + [str(fpath)], os.environ, str(dest))
            d.addCallback(on_extract, torrent_id, fpath)

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
