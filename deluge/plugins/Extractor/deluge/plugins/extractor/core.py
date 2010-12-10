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

import os

from twisted.internet.utils import getProcessValue

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export

DEFAULT_PREFS = {
    "extract_path": "",
    "use_name_folder": True
}

# The first format is the source file, the second is the dest path
EXTRACT_COMMANDS = {
    ".rar": ["unrar", "x -o+ -y"],
    ".zip": ["unzip", ""],
    ".tar.gz": ["tar", "xvzf"],
    ".tar.bz2": ["tar", "xvjf"],
    ".tar.lzma": ["tar", "--lzma xvf"]
}

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
        This is called when a torrent finishes.  We need to check to see if there
        are any files to extract.
        """
        # Get the save path
        save_path = component.get("TorrentManager")[torrent_id].get_status(["save_path"])["save_path"]
        files = component.get("TorrentManager")[torrent_id].get_files()
        for f in files:
            ext = os.path.splitext(f["path"])
            if ext[1] in (".gz", ".bz2", ".lzma"):
                # We need to check if this is a tar
                if os.path.splitext(ext[0]) == ".tar":
                    cmd = EXTRACT_COMMANDS[".tar" + ext[1]]
            else:
                if ext[1] in EXTRACT_COMMANDS:
                    cmd = EXTRACT_COMMANDS[ext[1]]
                else:
                    log.debug("Can't extract unknown file type: %s", ext[1])
                    continue

            # Now that we have the cmd, lets run it to extract the files
            fp = os.path.join(save_path, f["path"])
            
            # Get the destination path
            dest = self.config["extract_path"]
            if self.config["use_name_folder"]:
                name = component.get("TorrentManager")[torrent_id].get_status(["name"])["name"]
                dest = os.path.join(dest, name)

            # Create the destination folder if it doesn't exist                
            if not os.path.exists(dest):
                try:
                    os.makedirs(dest)
                except Exception, e:
                    log.error("Error creating destination folder: %s", e)
                    return
            
            log.debug("Extracting to %s", dest)        
            def on_extract_success(result, torrent_id):
                # XXX: Emit an event
                log.debug("Extract was successful for %s", torrent_id)

            def on_extract_failed(result, torrent_id):
                # XXX: Emit an event
                log.debug("Extract failed for %s", torrent_id)

            # Run the command and add some callbacks
            d = getProcessValue(cmd[0], cmd[1].split() + [str(fp)], {}, str(dest))
            d.addCallback(on_extract_success, torrent_id)
            d.addErrback(on_extract_failed, torrent_id)

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
