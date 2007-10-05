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

"""Internal Torrent class"""

import deluge.common

class Torrent:
    """Torrent holds information about torrents added to the libtorrent session.
    """
    def __init__(self, filename, handle, compact, save_path):
        # Set the filename
        self.filename = filename
        # Set the libtorrent handle
        self.handle = handle
        # Set the torrent_id for this torrent
        self.torrent_id = str(handle.info_hash())
        # This is for saving the total uploaded between sessions
        self.total_uploaded = 0
        # Set the allocation mode
        self.compact = compact
        # Where the torrent is being saved to
        self.save_path = save_path
        # The tracker status
        self.tracker_status = ""
    
    def set_tracker_status(self, status):
        """Sets the tracker status"""
        self.tracker_status = status
        
    def get_state(self):
        """Returns the state of this torrent for saving to the session state"""
        status = self.handle.status()
        return (self.torrent_id, self.filename, self.compact, status.paused,
            self.save_path)
        
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
    
    def get_ratio(self):
        """Returns the ratio for this torrent"""
        up = self.total_uploaded + self.handle.status().total_payload_upload
        down = self.handle.status().total_done
        
        # Convert 'up' and 'down' to floats for proper calculation
        up = float(up)
        down = float(down)
        
        try:
            ratio = up / down
        except ZeroDivisionError:
            return 0.0

        return ratio
                    
    def get_status(self, keys):
        """Returns the status of the torrent based on the keys provided"""
        # Create the full dictionary
        status = self.handle.status()
        
        # Adjust progress to be 0-100 value
        progress = status.progress*100
        
        # Get the total number of seeds and peers
        if status.num_complete == -1:
            total_seeds = status.num_seeds
        else:
            total_seeds = status.num_complete
            
        if status.num_incomplete == -1:
            total_peers = status.num_peers - status.num_seeds
        else:
            total_peers = status.num_incomplete
        
        # Set the state to 'Paused' if the torrent is paused.
        state = status.state
        if status.paused:
            state = deluge.common.TORRENT_STATE.index("Paused")
        
        # Adjust status.distributed_copies to return a non-negative value
        distributed_copies = status.distributed_copies
        if distributed_copies < 0:
            distributed_copies = 0.0
               
        full_status = {
            "name": self.handle.torrent_info().name(),
            "total_size": self.handle.torrent_info().total_size(),
            "num_files": self.handle.torrent_info().num_files(),
            "num_pieces": self.handle.torrent_info().num_pieces(),
            "piece_length": self.handle.torrent_info().piece_length(),
            "distributed_copies": distributed_copies,
            "total_done": status.total_done,
            "total_uploaded": self.total_uploaded + status.total_payload_upload,
            "state": int(state),
            "paused": status.paused,
            "progress": progress,
            "next_announce": status.next_announce.seconds,
            "total_payload_download": status.total_payload_download,
            "total_payload_upload": status.total_payload_upload,
            "download_payload_rate": status.download_payload_rate,
            "upload_payload_rate": status.upload_payload_rate,
            "num_peers": status.num_peers - status.num_seeds,
            "num_seeds": status.num_seeds,
            "total_peers": total_peers,
            "total_seeds": total_seeds,
            "total_wanted": status.total_wanted,
            "eta": self.get_eta(),
            "ratio": self.get_ratio(),
            "tracker": status.current_tracker,
            "tracker_status": self.tracker_status,
            "save_path": self.save_path
        }
        
        # Create the desired status dictionary and return it
        status_dict = {}
        
        for key in keys:
            if key in full_status:
                status_dict[key] = full_status[key]

        return status_dict
