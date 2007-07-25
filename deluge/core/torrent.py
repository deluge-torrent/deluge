#
# torrent.py
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

import deluge.libtorrent as lt

# Get the logger
log = logging.getLogger("deluge")

class Torrent:
    def __init__(self, filename, handle, queue):
        # Set the filename
        self.filename = filename
        # Set the libtorrent handle
        self.handle = handle
        # Set the queue this torrent belongs too
        self.queue = queue
        # Set the torrent_id for this torrent
        self.torrent_id = str(handle.info_hash())
    
    def __del__(self):
        self.queue.remove(self.torrent_id)
    
    def get_state(self):
        """Returns the state of this torrent for saving to the session state"""
        return (self.torrent_id, self.filename)
        
    def get_eta(self):
        """Returns the ETA in seconds for this torrent"""
        left = self.handle.status().total_wanted \
                - self.handle.status().total_done
        
        if left == 0 or self.handle.status().download_payload_rate == 0:
            return 0
        
        try:
            eta = left / self.handle.status().download_payload_rate
        except ZeroDivisionError:
            eta = 0
            
        return eta
                
    def get_info(self):
        """Returns the torrents info.. stuff that remains constant, such as
            name."""
        
        return (
            self.handle.torrent_info().name(),
            self.handle.torrent_info().total_size(),
            self.handle.status().num_pieces
        )
                  
    def get_status(self):
        """Returns the torrent status"""
        status = self.handle.status()
        
        return (
            status.state,
            status.paused,
            status.progress,
            status.next_announce.seconds,
            status.total_payload_download,
            status.total_payload_upload,
            status.download_payload_rate,
            status.upload_payload_rate,
            status.num_peers,
            status.num_seeds,
            status.total_wanted,
            self.get_eta(),
            self.queue[self.torrent_id]
        )
    
