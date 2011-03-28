#
# autoadd.py
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

from deluge._libtorrent import lt

import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

MAX_NUM_ATTEMPTS = 10

class AutoAdd(component.Component):
    def __init__(self):
        component.Component.__init__(self, "AutoAdd", depend=["TorrentManager"], interval=5)
        # Get the core config
        self.config = ConfigManager("core.conf")

        # A list of filenames
        self.invalid_torrents = []
        # Filename:Attempts
        self.attempts = {}

        # Register set functions
        self.config.register_set_function("autoadd_enable",
            self._on_autoadd_enable, apply_now=True)
        self.config.register_set_function("autoadd_location",
            self._on_autoadd_location)

    def update(self):
        if not self.config["autoadd_enable"]:
            # We shouldn't be updating because autoadd is not enabled
            component.pause("AutoAdd")
            return

        # Check the auto add folder for new torrents to add
        if not os.path.isdir(self.config["autoadd_location"]):
            log.warning("Invalid AutoAdd folder: %s", self.config["autoadd_location"])
            component.pause("AutoAdd")
            return

        for filename in os.listdir(self.config["autoadd_location"]):
            try:
                filepath = os.path.join(self.config["autoadd_location"], filename)
            except UnicodeDecodeError, e:
                log.error("Unable to auto add torrent due to improper filename encoding: %s", e)
                continue
            if os.path.isfile(filepath) and filename.endswith(".torrent"):
                try:
                    filedump = self.load_torrent(filepath)
                except (RuntimeError, Exception), e:
                    # If the torrent is invalid, we keep track of it so that we
                    # can try again on the next pass.  This is because some
                    # torrents may not be fully saved during the pass.
                    log.debug("Torrent is invalid: %s", e)
                    if filename in self.invalid_torrents:
                        self.attempts[filename] += 1
                        if self.attempts[filename] >= MAX_NUM_ATTEMPTS:
                            os.rename(filepath, filepath + ".invalid")
                            del self.attempts[filename]
                            self.invalid_torrents.remove(filename)
                    else:
                        self.invalid_torrents.append(filename)
                        self.attempts[filename] = 1
                    continue

                # The torrent looks good, so lets add it to the session
                component.get("TorrentManager").add(filedump=filedump, filename=filename)

                os.remove(filepath)

    def load_torrent(self, filename):
        try:
            log.debug("Attempting to open %s for add.", filename)
            _file = open(filename, "rb")
            filedump = _file.read()
            if not filedump:
                raise RuntimeError, "Torrent is 0 bytes!"
            _file.close()
        except IOError, e:
            log.warning("Unable to open %s: %s", filename, e)
            raise e

        # Get the info to see if any exceptions are raised
        info = lt.torrent_info(lt.bdecode(filedump))

        return filedump

    def _on_autoadd_enable(self, key, value):
        log.debug("_on_autoadd_enable")
        if value:
            component.resume("AutoAdd")
        else:
            component.pause("AutoAdd")

    def _on_autoadd_location(self, key, value):
        log.debug("_on_autoadd_location")
        # We need to resume the component just incase it was paused due to
        # an invalid autoadd location.
        if self.config["autoadd_enable"]:
            component.resume("AutoAdd")
