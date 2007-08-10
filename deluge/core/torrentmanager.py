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
import pickle
import os.path

import deluge.libtorrent as lt

import deluge.common
from deluge.config import Config
from deluge.core.torrent import Torrent
from deluge.core.torrentmanagerstate import TorrentManagerState, TorrentState

# Get the logger
log = logging.getLogger("deluge")

class TorrentManager:
    def __init__(self, session):
        log.debug("TorrentManager init..")
        # Set the libtorrent session
        self.session = session
        # Create the torrents dict { torrent_id: Torrent }
        self.torrents = {}
        
    def __getitem__(self, torrent_id):
        """Return the Torrent with torrent_id"""
        return self.torrents[torrent_id]
    
    def add(self, filename, filedump=None):
        """Add a torrent to the manager and returns it's torrent_id"""
        # Get the core config
        config = Config("core.conf")
        
        # Convert the filedump data array into a string of bytes
        if filedump is not None:
            filedump = "".join(chr(b) for b in filedump)
        else:
            # Get the data from the file
            try:
                filedump = open(os.path.join(config["torrentfiles_location"],
                                    filename, "rb")).read()
            except IOError:
                log.warning("Unable to open %s", filename)
                return None
        
        # Bdecode the filedata
        torrent_filedump = lt.bdecode(filedump)
        handle = None
        
        try:
            handle = self.session.add_torrent(lt.torrent_info(torrent_filedump), 
                                    config["download_location"],
                                    config["compact_allocation"])
        except RuntimeError:
            log.warning("Error adding torrent") 
            
        if not handle or not handle.is_valid():
            # The torrent was not added to the session
            return None
        
        # Write the .torrent file to the torrent directory
        log.debug("Attemping to save torrent file: %s", filename)
        try:
            f = open(os.path.join(config["torrentfiles_location"], 
                    filename),
                    "wb")
            f.write(filedump)
            f.close()
        except IOError:
            log.warning("Unable to save torrent file: %s", filename)
        
        # Create a Torrent object
        torrent = Torrent(filename, handle)
        # Add the torrent object to the dictionary
        self.torrents[torrent.torrent_id] = torrent
        return torrent.torrent_id
    
    def remove(self, torrent_id):
        """Remove a torrent from the manager"""
        try:
            # Remove from libtorrent session
            self.session.remove_torrent(self.torrents[torrent_id].handle)
        except RuntimeError, KeyError:
            log.warning("Error removing torrent")
            return False
            
        try:
            del self.torrents[torrent_id]
        except KeyError, ValueError:
            return False
        return True

    def pause(self, torrent_id):
        """Pause a torrent"""
        try:
            self.torrents[torrent_id].handle.pause()
        except:
            return False
            
        return True
        
    def resume(self, torrent_id):
        """Resume a torrent"""
        try:
            self.torrents[torrent_id].handle.resume()
        except:
            return False
        
        return True
        
    def save_state(self):
        """Save the state of the TorrentManager to the torrents.state file"""
        state = TorrentManagerState()
        # Create the state for each Torrent and append to the list
        for (key, torrent) in self.torrents:
            t = TorrentState(torrent.get_state())
            state.torrents.append(t)
        
        # Pickle the TorrentManagerState object
        try:
            log.debug("Saving torrent state file.")
            state_file = open(deluge.common.get_config_dir("torrents.state"), "wb")
            pickle.dump(state, state_file)
            state_file.close()
        except IOError:
            log.warning("Unable to save state file.")
            
