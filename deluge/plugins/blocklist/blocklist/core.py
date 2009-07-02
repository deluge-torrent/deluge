#
# core.py
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 John Garland <johnnybg@gmail.com>
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
import datetime
import shutil

from twisted.internet.task import LoopingCall
from twisted.internet import reactor, threads
from twisted.web import error

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
from deluge.httpdownloader import download_file

from peerguardian import PGReader, PGException
from text import TextReader, GZMuleReader, PGZip, PGTextReaderGzip

DEFAULT_PREFS = {
    "url": "http://deluge-torrent.org/blocklist/nipfilter.dat.gz",
    "load_on_start": False,
    "check_after_days": 4,
    "list_type": "gzmule",
    "last_update": "",
    "list_size": 0,
    "timeout": 180,
    "try_times": 3,
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

        self.has_imported = False
        self.up_to_date = False
        self.num_blocked = 0
        self.file_progress = 0.0

        self.core = component.get("Core")

        self.config = deluge.configmanager.ConfigManager("blocklist.conf", DEFAULT_PREFS)
        if self.config["load_on_start"]:
            # TODO: Check if been more than check_after_days
            self.use_cache = True
            d = self.import_list()
            d.addCallbacks(self.on_import_complete, self.on_import_error)

        # This function is called every 'check_after_days' days, to download
        # and import a new list if needed.
        self.update_timer = LoopingCall(self.check_import)
        self.update_timer.start(self.config["check_after_days"] * 24 * 60 * 60)

    def disable(self):
        log.debug("Reset IP Filter..")
        component.get("Core").reset_ip_filter()
        self.config.save()
        log.debug('Blocklist: Plugin disabled')

    def update(self):
        pass

    ## Exported RPC methods ###
    @export()
    def check_import(self, force=False):
        """Imports latest blocklist specified by blocklist url.
           Only downloads/imports if necessary or forced."""

        # Reset variables
        self.force_download = force
        self.use_cache = False
        self.failed_attempts = 0
        
        # Start callback chain
        d = self.download_list()
        d.addCallbacks(self.on_download_complete, self.on_download_error)
        d.addCallback(self.import_list)
        d.addCallbacks(self.on_import_complete, self.on_import_error)

        return d

    @export()
    def get_config(self):
        """Returns the config dictionary"""
        return self.config.config

    @export()
    def set_config(self, config):
        """Sets the config based on values in 'config'"""
        for key in config.keys():
            self.config[key] = config[key]

    @export()
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
        status["file_type"] = self.config["list_type"]
        status["file_url"] = self.config["url"]
        status["file_size"] = self.config["list_size"]
        status["file_date"] = self.config["last_update"]

        return status

    ####

    def update_info(self, blocklist):
        """Updates blocklist info"""
        self.config["last_update"] = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        self.config["list_size"] = os.path.getsize(blocklist)

    def download_list(self, url=None):
        """Downloads the blocklist specified by 'url' in the config"""
        def on_retrieve_data(data, current_length, total_length):
            if total_length:
                fp = float(current_length) / total_length
                if fp > 1.0:
                    fp = 1.0
            else:
                fp = 0.0

            self.file_progress = fp

        import socket
        socket.setdefaulttimeout(self.config["timeout"])

        headers = {}
        if not url:
            url = self.config["url"]

        if self.config["last_update"] and not self.force_download:
            headers['If-Modified-Since'] = self.config["last_update"]

        log.debug("Attempting to download blocklist %s", url)
        self.is_downloading = True
        return download_file(url, deluge.configmanager.get_config_dir("blocklist.download"), headers)

    def on_download_complete(self, result):
        """Runs any download clean up functions"""
        log.debug("Blocklist download complete!")
        self.is_downloading = False
        return threads.deferToThread(self.update_info,
                deluge.configmanager.ConfigManager("blocklist.download"))

    def on_download_error(self, f):
        """Recovers from download error"""
        self.is_downloading = False
        error_msg = f.getErrorMessage()
        d = None
        if f.check(error.PageRedirect):
            # Handle redirect errors
            location = error_msg.split(" to ")[1]
            if "Moved Permanently" in error:
                log.debug("Setting blocklist url to %s" % location)
                self.config["url"] = location
            f.trap(f.type)
            d = self.download_list(url=location)
            d.addCallbacks(self.on_download_complete, self.on_download_error)
        else:
            if "Not Modified" in error_msg:
                log.debug("Blocklist is up-to-date!")
                d = threads.deferToThread(update_info,
                        deluge.configmanager.ConfigManager("blocklist.cache"))
                self.use_cache = True
                f.trap(f.type)
            elif self.failed_attempts < self.config["try_times"]:
                log.warning("Blocklist download failed!")
                self.failed_attempts += 1
                f.trap(f.type)
        return d

    def import_list(self, force=False):
        """Imports the downloaded blocklist into the session"""
        if self.use_cache and self.has_imported:
            log.debug("Latest blocklist is already imported")
            return True

        self.is_importing = True
        log.debug("Reset IP Filter..")
        # Does this return a deferred?
        self.core.reset_ip_filter()

        self.num_blocked = 0

        # TODO: Make non-blocking (use deferToThread)

        # Open the file for reading
        read_list = FORMATS[self.config["listtype"]][1](bl_file)
        log.debug("Blocklist import starting..")
        ips = read_list.next()
        while ips:
            self.core.block_ip_range(ips)
            self.num_blocked += 1
            ips = read_list.next()
        read_list.close()

    def on_import_complete(self, result):
        """Runs any import clean up functions"""
        d = None
        self.is_importing = False
        self.has_imported = True
        log.debug("Blocklist import complete!")
        # Move downloaded blocklist to cache
        if not self.use_cache:
            d = threads.deferToThread(shutil.move,
                    deluge.configmanager.ConfigManager("blocklist.download"),
                    deluge.configmanager.ConfigManager("blocklist.cache"))
        return d

    def on_import_error(self, f):
        """Recovers from import error"""
        d = None
        self.is_importing = False
        blocklist = deluge.configmanager.get_config_dir("blocklist.cache")
        # If we have a backup and we haven't already used it
        if os.path.exists(blocklist) and not self.use_cache:
            e = f.trap(error.Error, IOError, TextException, PGException)
            log.warning("Error reading blocklist: ", e)
            d = self.import_list()
            d.addCallbacks(on_import_complete, on_import_error)
        return d
