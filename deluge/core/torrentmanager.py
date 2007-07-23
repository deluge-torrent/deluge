#
# torrentmanager.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.

import logging

from deluge.core.torrent import Torrent
from deluge.core.torrentqueue import TorrentQueue

# Get the logger
log = logging.getLogger("deluge")

class TorrentManager:
    def __init__(self):
        log.debug("TorrentManager init..")
        # Create the torrents dict { torrent_id: Torrent }
        self.torrents = {}
        self.queue = TorrentQueue()
        
    def __getitem__(self, torrent_id):
        """Return the Torrent with torrent_id"""
        return self.torrents[torrent_id]
    
    def add(self, handle):
        """Add a torrent to the manager and returns it's torrent_id"""
        # Create a Torrent object
        torrent = Torrent(handle, self.queue)
        # Add the torrent object to the dictionary
        self.torrents[torrent.torrent_id] = torrent
        # Add the torrent to the queue
        self.queue.append(torrent.torrent_id)
        return torrent.torrent_id
