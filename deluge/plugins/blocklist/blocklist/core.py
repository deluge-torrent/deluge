#
# core.py
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
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


import threading
import urllib
import os
import datetime
import gobject
import time
import shutil

from deluge.log import LOG as log
from deluge.plugins.corepluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export

from peerguardian import PGReader, PGException
from text import TextReader, GZMuleReader, PGZip, PGTextReaderGzip

DEFAULT_PREFS = {
    "url": "http://deluge-torrent.org/blocklist/nipfilter.dat.gz",
    "load_on_start": False,
    "check_after_days": 4,
    "listtype": "gzmule",
    "timeout": 180,
    "try_times": 3,
    "file_type": "",
    "file_url": "",
    "file_date": "",
    "file_size": 0,
}

FORMATS =  {
    'gzmule': ["Emule IP list (GZip)", GZMuleReader],
    'spzip': ["SafePeer Text (Zipped)", PGZip],
    'pgtext': ["PeerGuardian Text (Uncompressed)", TextReader],
    'p2bgz': ["PeerGuardian P2B (GZip)", PGReader],
    'pgtextgz': ["PeerGuardian Text (GZip)",  PGTextReaderGzip]
}

class Core(CorePluginBase):
    def enable(self):
        log.debug('Blocklist: Plugin enabled..')

        self.is_downloading = False
        self.is_importing = False
        self.has_imported = False
        self.num_blocked = 0
        self.file_progress = 0.0

        self.core = component.get("Core")

        self.config = deluge.configmanager.ConfigManager("blocklist.conf", DEFAULT_PREFS)
        if self.config["load_on_start"]:
            self.import_list()

        # This function is called every 'check_after_days' days, to download
        # and import a new list if needed.
        self.update_timer = gobject.timeout_add(
            self.config["check_after_days"] * 24 * 60 * 60 * 1000,
            self.download_blocklist, True)

    def disable(self):
        log.debug("Reset IP Filter..")
        component.get("Core").reset_ip_filter()
        self.config.save()
        log.debug('Blocklist: Plugin disabled')

    def update(self):
        pass

    ## Exported RPC methods ###
    @export
    def download_list(self, _import=False):
        """Download the blocklist specified in the config as url"""
        self.download_blocklist(_import)

    @export
    def import_list(self, force=False):
        """Import the blocklist from the blocklist.cache, if load is True, then
        it will download the blocklist file if needed."""
        threading.Thread(target=self.import_blocklist, kwargs={"force": force}).start()

    @export
    def get_config(self):
        """Returns the config dictionary"""
        return self.config.config

    @export
    def set_config(self, config):
        """Sets the config based on values in 'config'"""
        for key in config.keys():
            self.config[key] = config[key]

    @export
    def get_status(self):
        """Returns the status of the plugin."""
        status = {}
        if self.is_downloading:
            status["state"] = "Downloading"
        elif self.is_importing:
            status["state"] = "Importing"
        else:
            status["state"] = "Idle"

        status["num_blocked"] = self.num_blocked
        status["file_progress"] = self.file_progress
        status["file_type"] = self.config["file_type"]
        status["file_url"] = self.config["file_url"]
        status["file_size"] = self.config["file_size"]
        status["file_date"] = self.config["file_date"]

        return status

    ####


    def on_download_blocklist(self, load):
        self.is_downloading = False
        if load:
            self.import_list()

    def import_blocklist(self, force=False):
        """Imports the downloaded blocklist into the session"""
        if self.is_downloading:
            return

        if force or self.need_new_blocklist():
            self.download_blocklist(True)
            return

        # If we have a newly downloaded file, lets try that before the .cache
        if os.path.exists(deluge.configmanager.get_config_dir("blocklist.download")):
            bl_file = deluge.configmanager.get_config_dir("blocklist.download")
            using_download = True
        elif self.has_imported:
            # Blocklist is up to date so doesn't need to be imported
            log.debug("Latest blocklist is already imported")
            return
        else:
            bl_file = deluge.configmanager.get_config_dir("blocklist.cache")
            using_download = False

        self.is_importing = True
        log.debug("Reset IP Filter..")
        component.get("Core").reset_ip_filter()

        self.num_blocked = 0

        # Open the file for reading
        try:
            read_list = FORMATS[self.config["listtype"]][1](bl_file)
        except Exception, e:
            log.debug("Unable to read blocklist file: %s", e)
            self.is_importing = False
            return

        try:
            log.debug("Blocklist import starting..")
            ips = read_list.next()
            while ips:
                self.core.block_ip_range(ips)
                self.num_blocked += 1
                ips = read_list.next()
            read_list.close()
        except Exception, e:
            log.debug("Exception during import: %s", e)
        else:
            log.debug("Blocklist import complete!")
            # The import was successful so lets move this to blocklist.cache
            if using_download:
                log.debug("Moving blocklist.download to blocklist.cache")
                shutil.move(bl_file, deluge.configmanager.get_config_dir("blocklist.cache"))
            # Set information about the file
            self.config["file_type"] = self.config["listtype"]
            self.config["file_url"] = self.config["url"]

        self.is_importing = False
        self.has_imported = True

    def download_blocklist(self, load=False):
        """Runs download_blocklist_thread() in a thread and calls on_download_blocklist
            when finished.  If load is True, then we will import the blocklist
            upon download completion."""
        if self.is_importing:
            return

        self.is_downloading = True
        threading.Thread(
            target=self.download_blocklist_thread,
            args=(self.on_download_blocklist, load)).start()

    def download_blocklist_thread(self, callback, load):
        """Downloads the blocklist specified by 'url' in the config"""
        def _call_callback(callback, load):
            callback(load)
            return False

        def on_retrieve_data(count, block_size, total_blocks):
            fp = float(count * block_size) / total_blocks
            if fp > 1.0:
                fp = 1.0
            self.file_progress = fp

        import socket
        socket.setdefaulttimeout(self.config["timeout"])

        for i in xrange(self.config["try_times"]):
            log.debug("Attempting to download blocklist %s", self.config["url"])
            try:
                (filename, headers) = urllib.urlretrieve(
                    self.config["url"],
                    deluge.configmanager.get_config_dir("blocklist.download"),
                    on_retrieve_data)
            except Exception, e:
                log.debug("Error downloading blocklist: %s", e)
                os.remove(deluge.configmanager.get_config_dir("blocklist.download"))
                continue
            else:
                log.debug("Blocklist successfully downloaded..")
                self.config["file_date"] = datetime.datetime.strptime(headers["last-modified"],"%a, %d %b %Y %H:%M:%S GMT").ctime()
                self.config["file_size"] = long(headers["content-length"])
                gobject.idle_add(_call_callback, callback, load)
                return

    def need_new_blocklist(self):
        """Returns True if a new blocklist file should be downloaded"""
        # Check to see if we've just downloaded a new blocklist
        if os.path.exists(deluge.configmanager.get_config_dir("blocklist.download")):
            log.debug("New blocklist waiting to be imported")
            return False

        if os.path.exists(deluge.configmanager.get_config_dir("blocklist.cache")):
            # Check current block lists time stamp and decide if it needs to be replaced
            list_size = long(os.stat(deluge.configmanager.get_config_dir("blocklist.cache")).st_size)
            list_time = datetime.datetime.strptime(self.config["file_date"], "%a %b %d %H:%M:%S %Y")
        else:
            log.debug("Blocklist doesn't exist")
            return True

        # If local blocklist file exists but nothing is in it
        if list_size == 0:
            log.debug("Empty blocklist")
            return True

        # If blocklist has just started up don't check for updates
        if not self.has_imported:
            return False

        import socket
        socket.setdefaulttimeout(self.config["timeout"])

        try:
            # Get remote blocklist time stamp and size
            remote_stats = urllib.urlopen(self.config["url"]).info()
            remote_size = long(remote_stats["content-length"])
            remote_time = datetime.datetime.strptime(remote_stats["last-modified"],"%a, %d %b %Y %H:%M:%S GMT")
        except Exception, e:
            log.debug("Unable to get blocklist stats: %s", e)
            return False

        # Check if remote blocklist is newer (in date or size)
        if list_time < remote_time or list_size < remote_size:
            log.debug("Newer blocklist exists (%s & %d vs %s & %d)", remote_time, remote_size, list_time, list_size)
            return True

        log.debug("Blocklist is up to date")
        return False
