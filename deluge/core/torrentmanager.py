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

import cPickle
import os.path
import os

import gobject

import deluge.libtorrent as lt

import deluge.common
import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.core.torrent import Torrent
from deluge.log import LOG as log

class TorrentState:
    def __init__(self, torrent_id, filename, compact, paused, save_path,
        total_uploaded, trackers):
        self.torrent_id = torrent_id
        self.filename = filename
        self.compact = compact
        self.paused = paused
        self.save_path = save_path
        self.total_uploaded = total_uploaded
        self.trackers = trackers

class TorrentManagerState:
    def __init__(self):
        self.torrents = []

class TorrentManager(component.Component):
    """TorrentManager contains a list of torrents in the current libtorrent
    session.  This object is also responsible for saving the state of the
    session for use on restart."""
    
    def __init__(self, session, alerts):
        component.Component.__init__(self, "TorrentManager")
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

    def start(self):
        # Try to load the state from file
        self.load_state()

        # Save the state every 5 minutes
        self.save_state_timer = gobject.timeout_add(300000, self.save_state)
                    
    def stop(self):
        # Save state on shutdown
        self.save_state()
        # Pause all torrents and save the .fastresume files
        self.pause_all()
        for key in self.torrents.keys():
            self.write_fastresume(key)
        
    def shutdown(self):
        self.stop()
                        
    def __getitem__(self, torrent_id):
        """Return the Torrent with torrent_id"""
        return self.torrents[torrent_id]
    
    def get_torrent_list(self):
        """Returns a list of torrent_ids"""
        return self.torrents.keys()
        
    def add(self, filename, filedump=None, compact=None, paused=False,
        save_path=None, total_uploaded=0, trackers=None):
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
            filedump = lt.bdecode(filedump)
        else:
            # Get the data from the file
            filedump = self.load_torrent(filename)

        # Attempt to load fastresume data
        try:
            _file = open(
                os.path.join(
                    self.config["torrentfiles_location"], 
                    filename + ".fastresume"),
                    "rb")
            fastresume = lt.bdecode(_file.read())
            _file.close()
        except IOError, e:
            log.debug("Unable to load .fastresume: %s", e)
            fastresume = None
            
        handle = None

        # Make sure we have a valid download_location
        if save_path is None:
            save_path = self.config["download_location"]

        # Make sure we are adding it with the correct allocation method.
        if compact is None:
            compact = self.config["compact_allocation"]
        
        # Set the right storage_mode
        if compact:
            storage_mode = lt.storage_mode_t(1)
        else:
            storage_mode = lt.storage_mode_t(2)
        
        try:
            handle = self.session.add_torrent(
                                    lt.torrent_info(filedump), 
                                    str(save_path),
                                    resume_data=fastresume,
                                    storage_mode=storage_mode,
                                    paused=True)
        except RuntimeError, e:
            log.warning("Error adding torrent: %s", e)
            
        if not handle or not handle.is_valid():
            # The torrent was not added to the session
            return None       

        # Create a Torrent object
        torrent = Torrent(filename, handle, compact, 
            save_path, total_uploaded, trackers)
        
        # Add the torrent object to the dictionary
        self.torrents[torrent.torrent_id] = torrent

        # Set the trackers
        if trackers != None:
            self.set_trackers(str(handle.info_hash()), trackers)
                    
        # Set per-torrent limits
        handle.set_max_connections(self.max_connections)
        handle.set_max_uploads(self.max_uploads)

        # Resume the torrent if needed
        if paused == False:
            handle.resume()
            
        # Save the torrent file        
        self.save_torrent(filename, filedump)

        # Save the session state
        self.save_state()
        return torrent.torrent_id
    
    def save_torrent(self, filename, filedump):
        """Saves a torrent file"""
        log.debug("Attempting to save torrent file: %s", filename)
        # Test if the torrentfiles_location is accessible
        if os.access(
            os.path.join(self.config["torrentfiles_location"]), os.F_OK) \
                                                                    is False:
            # The directory probably doesn't exist, so lets create it
            try:
               os.makedirs(os.path.join(self.config["torrentfiles_location"]))
            except IOError, e:
                log.warning("Unable to create torrent files directory: %s", e)
        
        # Write the .torrent file to the torrent directory
        try:
            save_file = open(os.path.join(self.config["torrentfiles_location"], 
                    filename),
                    "wb")
            save_file.write(lt.bencode(filedump))
            save_file.close()
        except IOError, e:
            log.warning("Unable to save torrent file: %s", e)

    def load_torrent(self, filename):
        """Load a torrent file and return it's torrent info"""
        filedump = None
        # Get the torrent data from the torrent file
        try:
            log.debug("Attempting to open %s for add.", filename)
            _file = open(
                os.path.join(
                    self.config["torrentfiles_location"], filename), 
                        "rb")
            filedump = lt.bdecode(_file.read())
            _file.close()
        except IOError, e:
            log.warning("Unable to open %s: e", filename, e)
            return False
        
        return filedump
        
    def remove(self, torrent_id, remove_torrent, remove_data):
        """Remove a torrent from the manager"""
        try:
            # Remove from libtorrent session
            option = 0
            # Remove data if set
            if remove_data:
                option = 1
            self.session.remove_torrent(self.torrents[torrent_id].handle, 
                option)
        except (RuntimeError, KeyError), e:
            log.warning("Error removing torrent: %s", e)
            return False
            
        # Remove the .torrent file if requested
        if remove_torrent:
            try:
                torrent_file = os.path.join(
                    self.config["torrentfiles_location"], 
                    self.torrents[torrent_id].filename)
                os.remove(torrent_file)
            except Exception, e:
                log.warning("Unable to remove .torrent file: %s", e)

        # Remove the .fastresume if it exists
        self.delete_fastresume(torrent_id)
        
        # Remove the torrent from deluge's session
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
    
    def set_trackers(self, torrent_id, trackers):
        """Sets trackers"""
        if trackers == None:
            trackers = []
            
        log.debug("Setting trackers for %s: %s", torrent_id, trackers)
        tracker_list = []

        for tracker in trackers:
            new_entry = lt.announce_entry(tracker["url"])
            new_entry.tier = tracker["tier"]
            tracker_list.append(new_entry)
            
        self.torrents[torrent_id].handle.replace_trackers(tracker_list)
        # Print out the trackers
        for t in self.torrents[torrent_id].handle.trackers():
            log.debug("tier: %s tracker: %s", t.tier, t.url)
        # Set the tracker list in the torrent object
        self.torrents[torrent_id].trackers = trackers
        if len(trackers) > 0:
            # Force a reannounce if there is at least 1 tracker
            self.force_reannounce(torrent_id)
        
    def force_reannounce(self, torrent_id):
        """Force a tracker reannounce"""
        try:
            self.torrents[torrent_id].handle.force_reannounce()
        except Exception, e:
            log.debug("Unable to force reannounce: %s", e)
            return False
        
        return True
    
    def scrape_tracker(self, torrent_id):
        """Scrape the tracker"""
        try:
            self.torrents[torrent_id].handle.scrape_tracker()
        except Exception, e:
            log.debug("Unable to scrape tracker: %s", e)
            return False
        
        return True
        
    def force_recheck(self, torrent_id):
        """Forces a re-check of the torrent's data"""
        log.debug("Doing a forced recheck on %s", torrent_id)
        torrent = self.torrents[torrent_id]
        paused = self.torrents[torrent_id].handle.status().paused
        torrent_info = None
        ### Check for .torrent file prior to removing and make a copy if needed
        if os.access(os.path.join(self.config["torrentfiles_location"] +\
                 "/" + torrent.filename), os.F_OK) is False:
            torrent_info = torrent.handle.get_torrent_info().create_torrent()
            self.save_torrent(torrent.filename, torrent_info)

        # We start by removing it from the lt session            
        try:
            self.session.remove_torrent(torrent.handle, 0)
        except (RuntimeError, KeyError), e:
            log.warning("Error removing torrent: %s", e)
            return False

        # Remove the fastresume file if there
        self.delete_fastresume(torrent_id)
        
        # Load the torrent info from file if needed
        if torrent_info == None:
            torrent_info = self.load_torrent(torrent.filename)

        # Next we re-add the torrent
        
        # Set the right storage_mode
        if torrent.compact:
            storage_mode = lt.storage_mode_t(1)
        else:
            storage_mode = lt.storage_mode_t(2)
        
        # Add the torrent to the lt session  
        try:
            torrent.handle = self.session.add_torrent(
                                    lt.torrent_info(torrent_info),
                                    str(torrent.save_path),
                                    storage_mode=storage_mode,
                                    paused=paused)
        except RuntimeError, e:
            log.warning("Error adding torrent: %s", e)
            
        if not torrent.handle or not torrent.handle.is_valid():
            # The torrent was not added to the session
            return False       
        
        return True
        
    def load_state(self):
        """Load the state of the TorrentManager from the torrents.state file"""
        state = TorrentManagerState()
        
        try:
            log.debug("Opening torrent state file for load.")
            state_file = open(deluge.common.get_config_dir("torrents.state"),
                                                                        "rb")
            state = cPickle.load(state_file)
            state_file.close()
        except IOError:
            log.warning("Unable to load state file.")

        # Try to add the torrents in the state to the session        
        for torrent_state in state.torrents:
            self.add(torrent_state.filename, compact=torrent_state.compact,
                paused=torrent_state.paused, save_path=torrent_state.save_path,
                total_uploaded=torrent_state.total_uploaded,
                trackers=torrent_state.trackers)
            
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
            cPickle.dump(state, state_file)
            state_file.close()
        except IOError:
            log.warning("Unable to save state file.")
            
        # We return True so that the timer thread will continue
        return True
    
    def delete_fastresume(self, torrent_id):
        """Deletes the .fastresume file"""
        torrent = self.torrents[torrent_id]
        path = "%s/%s.fastresume" % (
            self.config["torrentfiles_location"], 
            torrent.filename)
        log.debug("Deleting fastresume file: %s", path)
        try:
            os.remove(path)
        except Exception, e:
            log.warning("Unable to delete the fastresume file: %s", e)
            
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
            if alert.msg != "Got peers from DHT":
                self.torrents[torrent_id].set_tracker_status(_("Announce OK"))
        except KeyError:
            log.debug("torrent_id doesn't exist.")
        
        # Check to see if we got any peer information from the tracker
        if alert.handle.status().num_complete == -1 or \
            alert.handle.status().num_incomplete == -1:
            # We didn't get peer information, so lets send a scrape request
            self.scrape_tracker(torrent_id)

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
        tracker_status = "%s: %s" % \
            (_("Alert"), str(alert.msg()).strip('"')[8:])
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
