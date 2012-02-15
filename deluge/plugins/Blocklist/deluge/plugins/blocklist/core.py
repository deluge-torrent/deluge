#
# core.py
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009-2010 John Garland <johnnybg+deluge@gmail.com>
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
import time
import logging
from datetime import datetime, timedelta
from wsgiref.handlers import format_date_time
from urlparse import urljoin
import shutil

from twisted.internet.task import LoopingCall
from twisted.internet import threads, defer
from twisted.web import error

from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.common import is_url
from deluge.core.rpcserver import export
from deluge.httpdownloader import download_file
from common import IP, BadIP
from detect import detect_compression, detect_format, create_reader, UnknownFormatError
from readers import ReaderParseError

# TODO: check return values for deferred callbacks
# TODO: review class attributes for redundancy

log = logging.getLogger(__name__)

DEFAULT_PREFS = {
    "url": "http://deluge-torrent.org/blocklist/nipfilter.dat.gz",
    "load_on_start": False,
    "check_after_days": 4,
    "list_compression": "",
    "list_type": "",
    "last_update": 0.0,
    "list_size": 0,
    "timeout": 180,
    "try_times": 3,
    "whitelisted": [],
}

# Constants
ALLOW_RANGE = 0
BLOCK_RANGE = 1

class Core(CorePluginBase):
    def enable(self):
        log.debug('Blocklist: Plugin enabled...')

        self.is_url = True
        self.is_downloading = False
        self.is_importing = False
        self.has_imported = False
        self.up_to_date = False
        self.need_to_resume_session = False
        self.num_whited = 0
        self.num_blocked = 0
        self.file_progress = 0.0

        self.core = component.get("Core")
        self.config = deluge.configmanager.ConfigManager("blocklist.conf", DEFAULT_PREFS)
        if "whitelisted" not in self.config:
            self.config["whitelisted"] = []

        self.reader = create_reader(self.config["list_type"], self.config["list_compression"])

        if type(self.config["last_update"]) is not float:
            self.config.config["last_update"] = 0.0

        update_now = False
        if self.config["load_on_start"]:
            self.pause_session()
            if self.config["last_update"]:
                last_update = datetime.fromtimestamp(self.config["last_update"])
                check_period = timedelta(days=self.config["check_after_days"])
            if not self.config["last_update"] or last_update + check_period < datetime.now():
                update_now = True
            else:
                d = self.import_list(deluge.configmanager.get_config_dir("blocklist.cache"))
                d.addCallbacks(self.on_import_complete, self.on_import_error)
                if self.need_to_resume_session:
                    d.addBoth(self.resume_session)

        # This function is called every 'check_after_days' days, to download
        # and import a new list if needed.
        self.update_timer = LoopingCall(self.check_import)
        if self.config["check_after_days"] > 0:
            self.update_timer.start(
                self.config["check_after_days"] * 24 * 60 * 60, update_now
            )

    def disable(self):
        self.config.save()
        log.debug("Reset IP filter")
        self.core.session.get_ip_filter().add_rule(
            "0.0.0.0", "255.255.255.255", ALLOW_RANGE
        )
        log.debug('Blocklist: Plugin disabled')

    def update(self):
        pass

    ## Exported RPC methods ###
    @export
    def check_import(self, force=False):
        """
        Imports latest blocklist specified by blocklist url
        Only downloads/imports if necessary or forced

        :param force: optional argument to force download/import
        :type force: boolean
        :returns: a Deferred which fires when the blocklist has been imported
        :rtype: Deferred
        """

        # Reset variables
        self.filename = None
        self.force_download = force
        self.failed_attempts = 0
        self.auto_detected = False
        self.up_to_date = False
        if force:
            self.reader = None
        self.is_url = is_url(self.config["url"])

        # Start callback chain
        if self.is_url:
            d = self.download_list()
            d.addCallbacks(self.on_download_complete, self.on_download_error)
            d.addCallback(self.import_list)
        else:
            d = self.import_list(self.config["url"])
        d.addCallbacks(self.on_import_complete, self.on_import_error)
        if self.need_to_resume_session:
            d.addBoth(self.resume_session)

        return d

    @export
    def get_config(self):
        """
        Returns the config dictionary

        :returns: the config dictionary
        :rtype: dict
        """
        return self.config.config

    @export
    def set_config(self, config):
        """
        Sets the config based on values in 'config'

        :param config: config to set
        :type config: dictionary
        """
        needs_blocklist_import = False
        for key in config.keys():
            if key == 'whitelisted':
                saved = set(self.config[key])
                update = set(config[key])
                diff = saved.symmetric_difference(update)
                if diff:
                    log.debug("Whitelist changed. Updating...")
                    added = update.intersection(diff)
                    removed = saved.intersection(diff)
                    if added:
                        for ip in added:
                            try:
                                ip = IP.parse(ip)
                                self.blocklist.add_rule(
                                    ip.address, ip.address, ALLOW_RANGE
                                )
                                saved.add(ip.address)
                                log.debug("Added %s to whitelisted", ip)
                                self.num_whited += 1
                            except BadIP, e:
                                log.error("Bad IP: %s", e)
                                continue
                    if removed:
                        needs_blocklist_import = True
                        for ip in removed:
                            try:
                                ip = IP.parse(ip)
                                saved.remove(ip.address)
                                log.debug("Removed %s from whitelisted", ip)
                            except BadIP, e:
                                log.error("Bad IP: %s", e)
                                continue

                self.config[key] = list(saved)
                continue
            elif key == "check_after_days":
                if self.config[key] != config[key]:
                    self.config[key] = config[key]
                    update_now = False
                    if self.config["last_update"]:
                        last_update = datetime.fromtimestamp(self.config["last_update"])
                        check_period = timedelta(days=self.config["check_after_days"])
                    if not self.config["last_update"] or last_update + check_period < datetime.now():
                        update_now = True
                    self.update_timer.running and self.update_timer.stop()
                    if self.config["check_after_days"] > 0:
                        self.update_timer.start(
                            self.config["check_after_days"] * 24 * 60 * 60, update_now
                        )
                continue
            self.config[key] = config[key]

        if needs_blocklist_import:
            log.debug("IP addresses were removed from the whitelist. Since we "
                      "don't know if they were blocked before. Re-import "
                      "current blocklist and re-add whitelisted.")
            self.has_imported = False
            d = self.import_list(deluge.configmanager.get_config_dir("blocklist.cache"))
            d.addCallbacks(self.on_import_complete, self.on_import_error)

    @export
    def get_status(self):
        """
        Returns the status of the plugin

        :returns: the status dict of the plugin
        :rtype: dict
        """
        status = {}
        if self.is_downloading:
            status["state"] = "Downloading"
        elif self.is_importing:
            status["state"] = "Importing"
        else:
            status["state"] = "Idle"

        status["up_to_date"] = self.up_to_date
        status["num_whited"] = self.num_whited
        status["num_blocked"] = self.num_blocked
        status["file_progress"] = self.file_progress
        status["file_url"] = self.config["url"]
        status["file_size"] = self.config["list_size"]
        status["file_date"] = self.config["last_update"]
        status["file_type"] = self.config["list_type"]
        status["whitelisted"] = self.config["whitelisted"]
        if self.config["list_compression"]:
            status["file_type"] += " (%s)" % self.config["list_compression"]
        return status

    ####

    def update_info(self, blocklist):
        """
        Updates blocklist info

        :param blocklist: path of blocklist
        :type blocklist: string
        :returns: path of blocklist
        :rtype: string
        """
        log.debug("Updating blocklist info: %s", blocklist)
        self.config["last_update"] = time.time()
        self.config["list_size"] = os.path.getsize(blocklist)
        self.filename = blocklist
        return blocklist

    def download_list(self, url=None):
        """
        Downloads the blocklist specified by 'url' in the config

        :param url: optional url to download from, defaults to config value
        :type url: string
        :returns: a Deferred which fires once the blocklist has been downloaded
        :rtype: Deferred
        """
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

        if not url:
            url = self.config["url"]

        headers = {}
        if self.config["last_update"] and not self.force_download:
            headers['If-Modified-Since'] = format_date_time(self.config["last_update"])

        log.debug("Attempting to download blocklist %s", url)
        log.debug("Sending headers: %s", headers)
        self.is_downloading = True
        return download_file(
            url, deluge.configmanager.get_config_dir("blocklist.download"),
            on_retrieve_data, headers
        )

    def on_download_complete(self, blocklist):
        """
        Runs any download clean up functions

        :param blocklist: path of blocklist
        :type blocklist: string
        :returns: a Deferred which fires when clean up is done
        :rtype: Deferred
        """
        log.debug("Blocklist download complete: %s", blocklist)
        self.is_downloading = False
        return threads.deferToThread(self.update_info, blocklist)

    def on_download_error(self, f):
        """
        Recovers from download error

        :param f: failure that occured
        :type f: Failure
        :returns: a Deferred if recovery was possible
                  else the original failure
        :rtype: Deferred or Failure
        """
        self.is_downloading = False
        error_msg = f.getErrorMessage()
        d = f
        if f.check(error.PageRedirect):
            # Handle redirect errors
            location = urljoin(self.config["url"], error_msg.split(" to ")[1])
            if "Moved Permanently" in error_msg:
                log.debug("Setting blocklist url to %s", location)
                self.config["url"] = location
            d = self.download_list(location)
            d.addCallbacks(self.on_download_complete, self.on_download_error)
        else:
            if "Not Modified" in error_msg:
                log.debug("Blocklist is up-to-date!")
                self.up_to_date = True
                blocklist = deluge.configmanager.get_config_dir("blocklist.cache")
                d = threads.deferToThread(self.update_info, blocklist)
            else:
                log.warning("Blocklist download failed: %s", error_msg)
                if self.failed_attempts < self.config["try_times"]:
                    log.debug("Let's try again")
                    self.failed_attempts += 1
                    d = self.download_list()
                    d.addCallbacks(self.on_download_complete, self.on_download_error)
        return d

    def import_list(self, blocklist):
        """
        Imports the downloaded blocklist into the session

        :param blocklist: path of blocklist
        :type blocklist: string
        :returns: a Deferred that fires when the blocklist has been imported
        :rtype: Deferred
        """
        log.trace("on import_list")
        def on_read_ip_range(start, end):
            """Add ip range to blocklist"""
#            log.trace("Adding ip range %s - %s to ipfilter as blocked", start, end)
            self.blocklist.add_rule(start.address, end.address, BLOCK_RANGE)
            self.num_blocked += 1

        def on_finish_read(result):
            """Add any whitelisted IP's and add the blocklist to session"""
            # White listing happens last because the last rules added have
            # priority
            log.info("Added %d ranges to ipfilter as blocked", self.num_blocked)
            for ip in self.config["whitelisted"]:
                ip = IP.parse(ip)
                self.blocklist.add_rule(ip.address, ip.address, ALLOW_RANGE)
                self.num_whited += 1
                log.trace("Added %s to the ipfiler as white-listed", ip.address)
            log.info("Added %d ranges to ipfilter as white-listed", self.num_whited)
            self.core.session.set_ip_filter(self.blocklist)
            return result

        # TODO: double check logic
        if self.up_to_date and self.has_imported:
            log.debug("Latest blocklist is already imported")
            return defer.succeed(blocklist)

        self.is_importing = True
        self.num_blocked = 0
        self.num_whited = 0
        self.blocklist = self.core.session.get_ip_filter()

        if not blocklist:
            blocklist = self.filename

        if not self.reader:
            self.auto_detect(blocklist)
            self.auto_detected = True

        def on_reader_failure(failure):
            log.error("Failed to read!!!!!!")
            log.exception(failure)

        log.debug("Importing using reader: %s", self.reader)
        log.debug("Reader type: %s compression: %s", self.config["list_type"], self.config["list_compression"])
        log.debug("Clearing current ip filtering")
#        self.blocklist.add_rule("0.0.0.0", "255.255.255.255", ALLOW_RANGE)
        d = threads.deferToThread(self.reader(blocklist).read, on_read_ip_range)
        d.addCallback(on_finish_read).addErrback(on_reader_failure)

        return d

    def on_import_complete(self, blocklist):
        """
        Runs any import clean up functions

        :param blocklist: path of blocklist
        :type blocklist: string
        :returns: a Deferred that fires when clean up is done
        :rtype: Deferred
        """
        log.trace("on_import_list_complete")
        d = blocklist
        self.is_importing = False
        self.has_imported = True
        log.debug("Blocklist import complete!")
        cache = deluge.configmanager.get_config_dir("blocklist.cache")
        if blocklist != cache:
            if self.is_url:
                log.debug("Moving %s to %s", blocklist, cache)
                d = threads.deferToThread(shutil.move, blocklist, cache)
            else:
                log.debug("Copying %s to %s", blocklist, cache)
                d = threads.deferToThread(shutil.copy, blocklist, cache)
        return d

    def on_import_error(self, f):
        """
        Recovers from import error

        :param f: failure that occured
        :type f: Failure
        :returns: a Deferred if recovery was possible
                  else the original failure
        :rtype: Deferred or Failure
        """
        log.trace("on_import_error: %s", f)
        d = f
        self.is_importing = False
        try_again = False
        cache = deluge.configmanager.get_config_dir("blocklist.cache")

        if f.check(ReaderParseError) and not self.auto_detected:
            # Invalid / corrupt list, let's detect it
            log.warning("Invalid / corrupt blocklist")
            self.reader = None
            blocklist = None
            try_again = True
        elif self.filename != cache and os.path.exists(cache):
            # If we have a backup and we haven't already used it
            log.warning("Error reading blocklist: %s", f.getErrorMessage())
            blocklist = cache
            try_again = True

        if try_again:
            d = self.import_list(blocklist)
            d.addCallbacks(self.on_import_complete, self.on_import_error)

        return d

    def auto_detect(self, blocklist):
        """
        Tries to auto-detect the blocklist type

        :param blocklist: path of blocklist to auto-detect
        :type blocklist: string
        :raises UnknownFormatError: if the format cannot be detected
        """
        self.config["list_compression"] = detect_compression(blocklist)
        self.config["list_type"] = detect_format(blocklist, self.config["list_compression"])
        log.debug("Auto-detected type: %s compression: %s", self.config["list_type"], self.config["list_compression"])
        if not self.config["list_type"]:
            self.config["list_compression"] = ""
            raise UnknownFormatError
        else:
            self.reader = create_reader(self.config["list_type"], self.config["list_compression"])


    def pause_session(self):
        if not self.core.session.is_paused():
            self.core.session.pause()
            self.need_to_resume_session = True
        else:
            self.need_to_resume_session = False

    def resume_session(self, result):
        self.core.session.resume()
        self.need_to_resume_session = False
        return result
