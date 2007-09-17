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

"""TorrentManager handles Torrent objects"""

import pickle
import os.path
import os

import deluge.libtorrent as lt

import deluge.common
from deluge.config import Config
from deluge.core.torrent import Torrent
from deluge.log import LOG as log

class TorrentState:
    def __init__(self, torrent_id, filename, compact):
        self.torrent_id = torrent_id
        self.filename = filename
        self.compact = compact

class TorrentManagerState:
    def __init__(self):
        self.torrents = []

class TorrentManager:
    """TorrentManager contains a list of torrents in the current libtorrent
    session.  This object is also responsible for saving the state of the
    session for use on restart."""
    
    def __init__(self, session):
        log.debug("TorrentManager init..")
        # Set the libtorrent session
        self.session = session
        # Create the torrents dict { torrent_id: Torrent }
        self.torrents = {}
        # Try to load the state from file
        self.load_state()
    
    def __del__(self):
        log.debug("TorrentManager shutting down..")
        # Save state on shutdown
        self.save_state()
            
    def __getitem__(self, torrent_id):
        """Return the Torrent with torrent_id"""
        return self.torrents[torrent_id]
    
    def get_torrent_list(self):
        """Returns a list of torrent_ids"""
        return self.torrents.keys()
        
    def add(self, filename, filedump=None, compact=None):
        """Add a torrent to the manager and returns it's torrent_id"""
        log.info("Adding torrent: %s", filename)
        # Get the core config
        config = Config("core.conf")

        # Make sure 'filename' is a python string
        filename = str(filename)

        # Convert the filedump data array into a string of bytes
        if filedump is not None:
            filedump = "".join(chr(b) for b in filedump)
        else:
            # Get the data from the file
            try:
                log.debug("Attempting to open %s for add.", filename)
                filedump = open(os.path.join(config["torrentfiles_location"],
                                    filename), "rb").read()
            except IOError:
                log.warning("Unable to open %s", filename)
                return None
        
        # Bdecode the filedata
        torrent_filedump = lt.bdecode(filedump)
        handle = None
        
        # Make sure we are adding it with the correct allocation method.
        if compact is None:
            compact = config["compact_allocation"]
        print "compact: ", compact
            
        try:
            handle = self.session.add_torrent(
                                    lt.torrent_info(torrent_filedump), 
                                    config["download_location"],
                                    compact)
        except RuntimeError:
            log.warning("Error adding torrent") 
            
        if not handle or not handle.is_valid():
            # The torrent was not added to the session
            return None       

        log.debug("Attemping to save torrent file: %s", filename)
        # Test if the torrentfiles_location is accessible
        if os.access(os.path.join(config["torrentfiles_location"]), os.F_OK) \
                                                                    is False:
            # The directory probably doesn't exist, so lets create it
            try:
               os.makedirs(os.path.join(config["torrentfiles_location"]))
            except IOError:
                log.warning("Unable to create torrent files directory..")
        
        # Write the .torrent file to the torrent directory
        try:
            save_file = open(os.path.join(config["torrentfiles_location"], 
                    filename),
                    "wb")
            save_file.write(filedump)
            save_file.close()
        except IOError:
            log.warning("Unable to save torrent file: %s", filename)
        
        log.debug("Torrent %s added.", handle.info_hash())
        # Create a Torrent object
        torrent = Torrent(filename, handle, compact)
        # Add the torrent object to the dictionary
        self.torrents[torrent.torrent_id] = torrent
        # Save the session state
        self.save_state()
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
        # Save the session state
        self.save_state()
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

    def load_state(self):
        """Load the state of the TorrentManager from the torrents.state file"""
        state = TorrentManagerState()
        
        try:
            log.debug("Opening torrent state file for load.")
            state_file = open(deluge.common.get_config_dir("torrents.state"),
                                                                        "rb")
            state = pickle.load(state_file)
            state_file.close()
        except IOError:
            log.warning("Unable to load state file.")

        # Try to add the torrents in the state to the session        
        for torrent_state in state.torrents:
            self.add(torrent_state.filename, compact=torrent_state.compact)
            
    def save_state(self):
        """Save the state of the TorrentManager to the torrents.state file"""
        state = TorrentManagerState()
        # Create the state for each Torrent and append to the list
        for torrent in self.torrents.values():
            torrent_state = TorrentState(*torrent.get_state())
            state.torrents.append(torrent_state)
        
        # Pickle the TorrentManagerState object
        try:
            log.debug("Saving torrent state file.")
            state_file = open(deluge.common.get_config_dir("torrents.state"), 
                                                                        "wb")
            pickle.dump(state, state_file)
            state_file.close()
        except IOError:
            log.warning("Unable to save state file.")
            
