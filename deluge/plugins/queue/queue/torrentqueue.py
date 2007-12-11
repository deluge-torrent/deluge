#
# torrentqueue.py
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

import pickle

import deluge.common
from deluge.log import LOG as log

class TorrentQueue:
    def __init__(self, torrent_list):
        # Try to load the queue state from file
        self.queue = self.load_state()

        # First remove any torrent_ids in self.queue that are not in the current
        # session list.
        for torrent_id in self.queue:
            if torrent_id not in torrent_list:
                self.queue.remove(torrent_id)
        
        # Next we append any torrents in the session list to self.queue
        for torrent_id in torrent_list:
            if torrent_id not in self.queue:
                self.queue.append(torrent_id)
        
    def __getitem__(self, torrent_id):
        """Return the queue position of the torrent_id"""
        try:
            return self.queue.index(torrent_id)
        except ValueError:
            return None
        
    def load_state(self):
        """Load the queue state"""
        try:
            log.debug("Opening queue state file for load.")
            state_file = open(deluge.common.get_config_dir("queue.state"),
                                                                        "rb")
            state = pickle.load(state_file)
            state_file.close()
            return state
        except IOError, e:
            log.warning("Unable to load queue state file: %s", e)
        
        return []
        
    def save_state(self):
        """Save the queue state"""
        try:
            log.debug("Saving queue state file.")
            state_file = open(deluge.common.get_config_dir("queue.state"), 
                                                                        "wb")
            pickle.dump(self.queue, state_file)
            state_file.close()
        except IOError:
            log.warning("Unable to save queue state file.")
            
    def append(self, torrent_id):
        """Append torrent_id to the bottom of the queue"""
        log.debug("Append torrent %s to queue..", torrent_id)
        self.queue.append(torrent_id)
        self.save_state()
    
    def prepend(self, torrent_id):
        """Prepend torrent_id to the top of the queue"""
        log.debug("Prepend torrent %s to queue..", torrent_id)
        self.queue.insert(0, torrent_id)
        self.save_state()
    
    def remove(self, torrent_id):
        """Removes torrent_id from the list"""
        log.debug("Remove torrent %s from queue..", torrent_id)
        self.queue.remove(torrent_id)
        self.save_state()
            
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

        self.save_state()
                
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
        
        # Pop and prepend the torrent_id
        self.prepend(self.queue.pop(index))

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

        self.save_state()
                
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
