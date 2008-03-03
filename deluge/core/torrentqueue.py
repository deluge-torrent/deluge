#
# torrentqueue.py
#
# Copyright (C) 2007,2008 Andrew Resch ('andar') <andrewresch@gmail.com>
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

import deluge.component as component
import deluge.common
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

class TorrentQueue(component.Component):
    def __init__(self):
        component.Component.__init__(self, "TorrentQueue", depend=["TorrentManager"])
        # This is a list of torrent_ids in the queueing order
        self.queue = []
        
        self.torrents = component.get("TorrentManager")
        self.config = ConfigManager("core.conf")
        
    def update(self):
        seeding = []
        queued_seeding = []
        downloading = []
        queued_downloading = []
        
        for torrent_id in self.torrents.get_torrent_list():
            if self.torrents[torrent_id].get_status(["state"])["state"] == "Seeding":
                seeding.append((self.queue.index(torrent_id), torrent_id))
            elif self.torrents[torrent_id].get_status(["state"])["state"] == "Downloading":
                downloading.append((self.queue.index(torrent_id), torrent_id))
            elif self.torrents[torrent_id].get_status(["state"])["state"] == "Queued":
                if self.torrents[torrent_id].get_status(["is_seed"])["is_seed"]:
                    queued_seeding.append((self.queue.index(torrent_id), torrent_id))
                else:
                    queued_downloading.append((self.queue.index(torrent_id), torrent_id))
                    
        # We need to sort these lists by queue position
        seeding.sort()
        downloading.sort()
        queued_downloading.sort()
        queued_seeding.sort()
        
#        log.debug("total seeding: %s", len(seeding))
#        log.debug("total downloading: %s", len(downloading))
        
        if self.config["max_active_seeding"] > -1:
            if len(seeding) > self.config["max_active_seeding"]:
                # We need to queue some more torrents because we're over the active limit
                num_to_queue = len(seeding) - self.config["max_active_seeding"]
                for (pos, torrent_id) in seeding[-num_to_queue:]:
                    self.torrents[torrent_id].set_state("Queued")
            else:
                # We need to unqueue more torrents if possible
                num_to_unqueue = self.config["max_active_seeding"] - len(seeding)
                to_unqueue = []
                if num_to_unqueue <= len(queued_seeding):
                    to_unqueue = queued_seeding[:num_to_unqueue]
                else:
                    to_unqueue = queued_seeding
                for (pos, torrent_id) in to_unqueue:
                    self.torrents[torrent_id].set_state("Seeding")
                    
        if self.config["max_active_downloading"] > -1:
            if len(downloading) > self.config["max_active_downloading"]:
                num_to_queue = len(downloading) - self.config["max_active_downloading"]
                for (pos, torrent_id) in downloading[-num_to_queue:]:
                    self.torrents[torrent_id].set_state("Queued")
            else:
                # We need to unqueue more torrents if possible
                num_to_unqueue = self.config["max_active_downloading"] - len(downloading)
                to_unqueue = []
                if num_to_unqueue <= len(queued_downloading):
                    to_unqueue = queued_downloading[:num_to_unqueue]
                else:
                    to_unqueue = queued_downloading
                for (pos, torrent_id) in to_unqueue:
                    self.torrents[torrent_id].set_state("Downloading")
                            
    def set_size(self, size):
        """Clear and set the self.queue list to the length of size"""
        log.debug("Setting queue size to %s..", size)
        self.queue = [None] * size
        
    def __getitem__(self, torrent_id):
        """Return the queue position of the torrent_id"""
        try:
            return self.queue.index(torrent_id)
        except ValueError:
            return None
                
    def append(self, torrent_id):
        """Append torrent_id to the bottom of the queue"""
        log.debug("Append torrent %s to queue..", torrent_id)
        self.queue.append(torrent_id)
        return self.queue.index(torrent_id)
            
    def prepend(self, torrent_id):
        """Prepend torrent_id to the top of the queue"""
        log.debug("Prepend torrent %s to queue..", torrent_id)
        self.queue.insert(0, torrent_id)
        return self.queue.index(torrent_id)
            
    def insert(self, position, torrent_id):
        """Inserts torrent_id at position in queue."""
        log.debug("Inserting torrent %s at position %s..", torrent_id, position)

        if position < 0:
            for q in self.queue:
                if q == None:
                    self.queue[self.queue.index(q)] = torrent_id
                    break
        else:
            if self.queue[position] == None:
                self.queue[position] = torrent_id
            else:
                self.queue.insert(position, torrent_id)
                

        try:
            return self.queue.index(torrent_id)
        except ValueError:
            self.queue.append(torrent_id)
            return self.queue.index(torrent_id)
        
    def remove(self, torrent_id):
        """Removes torrent_id from the list"""
        log.debug("Remove torrent %s from queue..", torrent_id)
        self.queue.remove(torrent_id)
            
    def up(self, torrent_id):
        """Move torrent_id up one in the queue"""
        if torrent_id not in self.queue:
            # Raise KeyError if the torrent_id is not in the queue
            raise KeyError
        
        log.debug("Move torrent %s up..", torrent_id)
        # Get the index of the torrent_id
        index = self.queue.index(torrent_id)
        
        # Can't queue up if torrent is already at top
        if index is 0:
            return False
        
        # Pop and insert the torrent_id at index - 1
        self.queue.insert(index - 1, self.queue.pop(index))

        return True
        
    def top(self, torrent_id):
        """Move torrent_id to top of the queue"""
        if torrent_id not in self.queue:
            # Raise KeyError if the torrent_id is not in the queue
            raise KeyError

        log.debug("Move torrent %s to top..", torrent_id)
        # Get the index of the torrent_id
        index = self.queue.index(torrent_id)
        
        # Can't queue up if torrent is already at top
        if index is 0:
            return False
        
        self.queue.insert(0, self.queue.pop(index))
        
        return True
                
    def down(self, torrent_id):
        """Move torrent_id down one in the queue"""
        if torrent_id not in self.queue:
            # Raise KeyError if torrent_id is not in the queue
            raise KeyError
            
        log.debug("Move torrent %s down..", torrent_id)
        # Get the index of the torrent_id
        index = self.queue.index(torrent_id)
        
        # Can't queue down of torrent_id is at bottom
        if index is len(self.queue) - 1:
            return False
            
        # Pop and insert the torrent_id at index + 1
        self.queue.insert(index + 1, self.queue.pop(index))

        return True
        
    def bottom(self, torrent_id):
        """Move torrent_id to bottom of the queue"""
        if torrent_id not in self.queue:
            # Raise KeyError if torrent_id is not in the queue
            raise KeyError

        log.debug("Move torrent %s to bottom..", torrent_id)
        # Get the index of the torrent_id
        index = self.queue.index(torrent_id)
        
        # Can't queue down of torrent_id is at bottom
        if index is len(self.queue) - 1:
            return False
        
        # Pop and append the torrent_id
        self.append(self.queue.pop(index))
           
        return True
