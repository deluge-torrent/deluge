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
from deluge.configmanager import ConfigManager
from deluge.core.torrent import Torrent
from deluge.log import LOG as log

class TorrentState:
    def __init__(self, torrent_id, filename, compact, paused):
        self.torrent_id = torrent_id
        self.filename = filename
        self.compact = compact
        self.paused = paused

class TorrentManagerState:
    def __init__(self):
        self.torrents = []

class TorrentManager:
    """TorrentManager contains a list of torrents in the current libtorrent
    session.  This object is also responsible for saving the state of the
    session for use on restart."""
    
    def __init__(self, session, alerts):
        log.debug("TorrentManager init..")
        # Set the libtorrent session
        self.session = session
        # Set the alertmanager
        self.alerts = alerts
        # Get the core config
        self.config = ConfigManager("core.conf")
        # Per torrent connection limit and upload slot limit
        self.max_connections = -1
        self.max_uploads = -1
        # Create the torrents dict { torrent_id: Torrent }
        self.torrents = {}
        # Try to load the state from file
        self.load_state()
    
        # Register set functions
        self.config.register_set_function("max_connections_per_torrent",
            self.on_set_max_connections_per_torrent)
        self.config.register_set_function("max_upload_slots_per_torrent",
            self.on_set_max_upload_slots_per_torrent)
            
        # Register alert functions
        self.alerts.register_handler("torrent_finished_alert", 
            self.on_alert_torrent_finished)
        self.alerts.register_handler("torrent_paused_alert",
            self.on_alert_torrent_paused)
        self.alerts.register_handler("tracker_reply_alert",
            self.on_alert_tracker_reply)
        self.alerts.register_handler("tracker_announce_alert",
            self.on_alert_tracker_announce)
        self.alerts.register_handler("tracker_alert", self.on_alert_tracker)
        self.alerts.register_handler("tracker_warning_alert",
            self.on_alert_tracker_warning)
            
    def shutdown(self):
        log.debug("TorrentManager shutting down..")
        # Save state on shutdown
        self.save_state()
        # Pause all torrents and save the .fastresume files
        self.pause_all()
        for key in self.torrents.keys():
            self.write_fastresume(key)
        
    def __getitem__(self, torrent_id):
        """Return the Torrent with torrent_id"""
        return self.torrents[torrent_id]
    
    def get_torrent_list(self):
        """Returns a list of torrent_ids"""
        return self.torrents.keys()
        
    def add(self, filename, filedump=None, compact=None, paused=False):
        """Add a torrent to the manager and returns it's torrent_id"""
        log.info("Adding torrent: %s", filename)

        # Make sure 'filename' is a python string
        filename = str(filename)

        # Convert the filedump data array into a string of bytes
        if filedump is not None:
            # If the filedump is already of type str, then it's already been
            # joined.
            if type(filedump) is not str:
                filedump = "".join(chr(b) for b in filedump)
        else:
            # Get the data from the file
            try:
                log.debug("Attempting to open %s for add.", filename)
                _file = open(
                    os.path.join(
                        self.config["torrentfiles_location"], filename), "rb")
                filedump = _file.read()
                _file.close()
            except IOError:
                log.warning("Unable to open %s", filename)
                return None

        # Attempt to load fastresume data
        try:
            _file = open(
                os.path.join(
                    self.config["torrentfiles_location"], 
                    filename + ".fastresume"),
                    "rb")
            fastresume = lt.bdecode(_file.read())
            _file.close()
        except IOError:
            log.debug("Unable to load .fastresume..")
            fastresume = None
            
        # Bdecode the filedata
        torrent_filedump = lt.bdecode(filedump)
        handle = None

        # Make sure we are adding it with the correct allocation method.
        if compact is None:
            compact = self.config["compact_allocation"]
            
        try:
            handle = self.session.add_torrent(
                                    lt.torrent_info(torrent_filedump), 
                                    self.config["download_location"],
                                    resume_data=fastresume,
                                    compact_mode=compact,
                                    paused=paused)
        except RuntimeError:
            log.warning("Error adding torrent") 
            
        if not handle or not handle.is_valid():
            # The torrent was not added to the session
            return None       

        # Create a Torrent object
        torrent = Torrent(filename, handle, compact)
        # Add the torrent object to the dictionary
        self.torrents[torrent.torrent_id] = torrent
        
        # Set per-torrent limits
        handle.set_max_connections(self.max_connections)
        handle.set_max_uploads(self.max_uploads)
        
        log.debug("Attemping to save torrent file: %s", filename)
        # Test if the torrentfiles_location is accessible
        if os.access(
            os.path.join(self.config["torrentfiles_location"]), os.F_OK) \
                                                                    is False:
            # The directory probably doesn't exist, so lets create it
            try:
               os.makedirs(os.path.join(self.config["torrentfiles_location"]))
            except IOError:
                log.warning("Unable to create torrent files directory..")
        
        # Write the .torrent file to the torrent directory
        try:
            save_file = open(os.path.join(self.config["torrentfiles_location"], 
                    filename),
                    "wb")
            save_file.write(lt.bencode(torrent_filedump))
            save_file.close()
        except IOError:
            log.warning("Unable to save torrent file: %s", filename)
        
        log.debug("Torrent %s added.", handle.info_hash())

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
    
    def pause_all(self):
        """Pauses all torrents.. Returns a list of torrents paused."""
        torrent_was_paused = False
        for key in self.torrents.keys():
            try:
                self.torrents[key].handle.pause()
                torrent_was_paused = True
            except:
                log.warning("Unable to pause torrent %s", key)
        
        return torrent_was_paused
        
    def resume(self, torrent_id):
        """Resume a torrent"""
        try:
            self.torrents[torrent_id].handle.resume()
        except:
            return False
        
        status = self.torrents[torrent_id].get_status(
            ["total_done", "total_wanted"])
        
        # Only delete the .fastresume file if we're still downloading stuff
        if status["total_done"] < status["total_wanted"]:
            self.delete_fastresume(torrent_id)
        return True

    def resume_all(self):
        """Resumes all torrents.. Returns a list of torrents resumed"""
        torrent_was_resumed = False
        for key in self.torrents.keys():
            if self.resume(key):
                torrent_was_resumed = True
            else:
                log.warning("Unable to resume torrent %s", key)

        return torrent_was_resumed
                        
    def force_reannounce(self, torrent_id):
        """Force a tracker reannounce"""
        try:
            self.torrents[torrent_id].handle.force_reannounce()
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
            self.add(torrent_state.filename, compact=torrent_state.compact,
                paused=torrent_state.paused)
            
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
    
    def delete_fastresume(self, torrent_id):
        """Deletes the .fastresume file"""
        torrent = self.torrents[torrent_id]
        path = "%s/%s.fastresume" % (
            self.config["torrentfiles_location"], 
            torrent.filename)
        log.debug("Deleting fastresume file: %s", path)
        try:
            os.remove(path)
        except IOError:
            log.warning("Unable to delete the fastresume file: %s", path)
            
    def write_fastresume(self, torrent_id):
        """Writes the .fastresume file for the torrent"""
        torrent = self.torrents[torrent_id]
        resume_data = lt.bencode(torrent.handle.write_resume_data())
        path = "%s/%s.fastresume" % (
            self.config["torrentfiles_location"], 
            torrent.filename)
        log.debug("Saving fastresume file: %s", path)
        try:
            fastresume = open(path,"wb")
            fastresume.write(resume_data)
            fastresume.close()
        except IOError:
            log.warning("Error trying to save fastresume file")

    def on_set_max_connections_per_torrent(self, key, value):
        """Sets the per-torrent connection limit"""
        log.debug("max_connections_per_torrent set to %s..", value)
        self.max_connections = value
        for key in self.torrents.keys():
            self.torrents[key].handle.set_max_connections(value)
        
    def on_set_max_upload_slots_per_torrent(self, key, value):
        """Sets the per-torrent upload slot limit"""
        log.debug("max_upload_slots_per_torrent set to %s..", value)
        self.max_uploads = value
        for key in self.torrents.keys():
            self.torrents[key].handle.set_max_uploads(value)
    
    ## Alert handlers ##
    def on_alert_torrent_finished(self, alert):
        log.debug("on_alert_torrent_finished")
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        log.debug("%s is finished..", torrent_id)
        # Write the fastresume file
        self.write_fastresume(torrent_id)
        
    def on_alert_torrent_paused(self, alert):
        log.debug("on_alert_torrent_paused")
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        # Write the fastresume file
        self.write_fastresume(torrent_id)
        
    def on_alert_tracker_reply(self, alert):
        log.debug("on_alert_tracker_reply")
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        # Set the tracker status for the torrent
        try:
            self.torrents[torrent_id].set_tracker_status(_("Announce OK"))
        except KeyError:
            log.debug("torrent_id doesn't exist.")

    def on_alert_tracker_announce(self, alert):
        log.debug("on_alert_tracker_announce")
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        # Set the tracker status for the torrent
        try:
            self.torrents[torrent_id].set_tracker_status(_("Announce Sent"))
        except KeyError:
            log.debug("torrent_id doesn't exist.")

    def on_alert_tracker(self, alert):
        log.debug("on_alert_tracker")
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        tracker_status = "%s: %s (%s=%s, %s=%s)" % \
            (_("Alert"), str(alert.msg()), 
            _("HTTP code"), alert.status_code, 
            _("times in a row"), alert.times_in_row)
        # Set the tracker status for the torrent
        try:
            self.torrents[torrent_id].set_tracker_status(tracker_status)
        except KeyError:
            log.debug("torrent_id doesn't exist.")
                
    def on_alert_tracker_warning(self, alert):
        log.debug("on_alert_tracker_warning")
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        tracker_status = '%s: %s' % (_("Warning"), str(alert.msg()))
        # Set the tracker status for the torrent
        try:
            self.torrents[torrent_id].set_tracker_status(tracker_status)
        except KeyError:
            log.debug("torrent_id doesn't exist.")
