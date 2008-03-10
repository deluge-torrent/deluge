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
from deluge.core.torrentqueue import TorrentQueue
from deluge.configmanager import ConfigManager
from deluge.core.torrent import Torrent
from deluge.log import LOG as log

class TorrentState:
    def __init__(self,
            torrent_id, 
            filename, 
            total_uploaded, 
            trackers,
            compact, 
            state, 
            save_path,
            max_connections,
            max_upload_slots,
            max_upload_speed,
            max_download_speed,
            prioritize_first_last,
            private,
            file_priorities,
            queue
        ):
        self.torrent_id = torrent_id
        self.filename = filename
        self.total_uploaded = total_uploaded
        self.trackers = trackers
        self.queue = queue

        # Options
        self.compact = compact
        self.state = state
        self.save_path = save_path
        self.max_connections = max_connections
        self.max_upload_slots = max_upload_slots
        self.max_upload_speed = max_upload_speed
        self.max_download_speed = max_download_speed
        self.prioritize_first_last = prioritize_first_last
        self.private = private
        self.file_priorities = file_priorities

class TorrentManagerState:
    def __init__(self):
        self.torrents = []

class TorrentManager(component.Component):
    """TorrentManager contains a list of torrents in the current libtorrent
    session.  This object is also responsible for saving the state of the
    session for use on restart."""
    
    def __init__(self, session, alerts):
        component.Component.__init__(self, "TorrentManager", depend=["PluginManager"])
        log.debug("TorrentManager init..")
        # Set the libtorrent session
        self.session = session
        # Set the alertmanager
        self.alerts = alerts
        # Get the core config
        self.config = ConfigManager("core.conf")
        # Create the TorrentQueue object
        self.queue = TorrentQueue()

        # Create the torrents dict { torrent_id: Torrent }
        self.torrents = {}
    
        # List of torrents to note set state 'Paused' on lt alert
        self.not_state_paused = []
        
        # Register set functions
        self.config.register_set_function("max_connections_per_torrent",
            self.on_set_max_connections_per_torrent)
        self.config.register_set_function("max_upload_slots_per_torrent",
            self.on_set_max_upload_slots_per_torrent)
        self.config.register_set_function("max_upload_speed_per_torrent",
            self.on_set_max_upload_speed_per_torrent)
        self.config.register_set_function("max_download_speed_per_torrent",
            self.on_set_max_download_speed_per_torrent)
                        
        # Register alert functions
        self.alerts.register_handler("torrent_finished_alert", 
            self.on_alert_torrent_finished)
        self.alerts.register_handler("torrent_paused_alert",
            self.on_alert_torrent_paused)
        self.alerts.register_handler("torrent_checked_alert",
            self.on_alert_torrent_checked)
        self.alerts.register_handler("tracker_reply_alert",
            self.on_alert_tracker_reply)
        self.alerts.register_handler("tracker_announce_alert",
            self.on_alert_tracker_announce)
        self.alerts.register_handler("tracker_alert", self.on_alert_tracker)
        self.alerts.register_handler("tracker_warning_alert",
            self.on_alert_tracker_warning)
        self.alerts.register_handler("storage_moved_alert",
            self.on_alert_storage_moved)

    def start(self):
        # Get the pluginmanager reference
        self.plugins = component.get("PluginManager")
        
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
            self.torrents[key].write_fastresume()
                        
    def __getitem__(self, torrent_id):
        """Return the Torrent with torrent_id"""
        return self.torrents[torrent_id]
    
    def get_torrent_list(self):
        """Returns a list of torrent_ids"""
        return self.torrents.keys()
    
    def append_not_state_paused(self, torrent_id):
        """Appends to a list of torrents that we will not set state Paused to
        when we receive the paused alert from libtorrent.  The torrents are removed
        from this list once we receive the alert they have been paused in libtorrent."""
        self.not_state_paused.append(torrent_id)
            
    def add(self, filename, filedump=None, options=None, total_uploaded=0, 
            trackers=None, queue=-1, state=None, save_state=True):
        """Add a torrent to the manager and returns it's torrent_id"""
        log.info("Adding torrent: %s", filename)
        log.debug("options: %s", options)
        # Make sure 'filename' is a python string
        filename = str(filename)

        # Convert the filedump data array into a string of bytes
        if filedump is not None:
            # If the filedump is already of type str, then it's already been
            # joined.
            if type(filedump) is not str:
                filedump = "".join(chr(b) for b in filedump)
            try:
                filedump = lt.bdecode(filedump)
            except RuntimeError, e:
                log.warn("Unable to decode torrent file: %s", e)
                return None
        else:
            # Get the data from the file
            filedump = self.load_torrent(filename)
            if not filedump:
                log.warning("Unable to load torrent file..")
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
        except IOError, e:
            log.debug("Unable to load .fastresume: %s", e)
            fastresume = None
            
        handle = None

        # Check if options is None and load defaults
        options_keys = [
            "compact_allocation",
            "max_connections_per_torrent",
            "max_upload_slots_per_torrent",
            "max_upload_speed_per_torrent",
            "max_download_speed_per_torrent",
            "prioritize_first_last_pieces",
            "download_location",
            "add_paused",
            "default_private"
        ]

        if options == None:
            options = {}
            for key in options_keys:
                options[key] = self.config[key]
        else:
            for key in options_keys:
                if not options.has_key(key):
                    options[key] = self.config[key]
        
        # Set the right storage_mode
        if options["compact_allocation"]:
            storage_mode = lt.storage_mode_t(2)
        else:
            storage_mode = lt.storage_mode_t(1)
        
        try:
            handle = self.session.add_torrent(
                                    lt.torrent_info(filedump), 
                                    str(options["download_location"]),
                                    resume_data=fastresume,
                                    storage_mode=storage_mode,
                                    paused=True)
        except RuntimeError, e:
            log.warning("Error adding torrent: %s", e)
            
        if not handle or not handle.is_valid():
            # The torrent was not added to the session
            return None

        # Create a Torrent object
        torrent = Torrent(filename, handle, options["compact_allocation"], 
            options["download_location"], total_uploaded, trackers)

        # Add the torrent object to the dictionary
        self.torrents[torrent.torrent_id] = torrent

        # Add the torrent to the queue
        if queue == -1 and self.config["queue_new_to_top"]:
            self.queue.insert(0, torrent.torrent_id)
        else:
            self.queue.insert(queue, torrent.torrent_id)
                            
        # Set per-torrent options
        torrent.set_max_connections(options["max_connections_per_torrent"])
        torrent.set_max_upload_slots(options["max_upload_slots_per_torrent"])
        torrent.set_max_upload_speed(options["max_upload_speed_per_torrent"])
        torrent.set_max_download_speed(
            options["max_download_speed_per_torrent"])
        torrent.set_prioritize_first_last(
            options["prioritize_first_last_pieces"])
        torrent.set_private_flag(options["default_private"])

        if options.has_key("file_priorities"):
            if options["file_priorities"] != None:
                log.debug("set file priorities: %s", options["file_priorities"])
                torrent.set_file_priorities(options["file_priorities"])
        
        # Resume the torrent if needed
        if state == "Queued":
            torrent.state = "Queued"
        elif state == "Paused":
            torrent.state = "Paused"
        elif state == None and not options["add_paused"]:
            torrent.handle.resume()
            
        # Save the torrent file        
        torrent.save_torrent_file(filedump)

        if save_state:
            # Save the session state
            self.save_state()
         
        return torrent.torrent_id

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
        except (IOError, RuntimeError), e:
            log.warning("Unable to open %s: %s", filename, e)
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
        self.torrents[torrent_id].delete_fastresume()
        
        # Remove the torrent from the queue
        self.queue.remove(torrent_id)
        
        # Remove the torrent from deluge's session
        try:
            del self.torrents[torrent_id]
        except KeyError, ValueError:
            return False
        
        # Save the session state
        self.save_state()
        return True
    
    def pause_all(self):
        """Pauses all torrents.. Returns a list of torrents paused."""
        torrent_was_paused = False
        for key in self.torrents.keys():
            try:
                self.torrents[key].pause()
                torrent_was_paused = True
            except:
                log.warning("Unable to pause torrent %s", key)
        
        return torrent_was_paused

    def resume_all(self):
        """Resumes all torrents.. Returns True if at least 1 torrent is resumed"""
        torrent_was_resumed = False
        for key in self.torrents.keys():
            if self.torrents[key].resume():
                torrent_was_resumed = True
            else:
                log.warning("Unable to resume torrent %s", key)

        return torrent_was_resumed
       
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
            torrent.save_torrent_file()

        # We start by removing it from the lt session            
        try:
            self.session.remove_torrent(torrent.handle, 0)
        except (RuntimeError, KeyError), e:
            log.warning("Error removing torrent: %s", e)
            return False

        # Remove the fastresume file if there
        torrent.delete_fastresume()
        
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
        
        # Set the state to Checking
        torrent.set_state("Checking")
        
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
        add_paused = {}
        # First lets clear the queue and make it the correct length.. This will
        # help with inserting values at the right position.
        self.queue.set_size(len(state.torrents))
        
        # Reorder the state.torrents list to add torrents with .fastresume files
        # first.
        fr_first = []
        for torrent_state in state.torrents:
            if os.path.exists(os.path.join(
                    self.config["torrentfiles_location"], 
                    torrent_state.filename, ".fastresume")):
                fr_first.insert(0, torrent_state)
            else:
                fr_first.append(torrent_state)
                   
        for torrent_state in fr_first:
            try:
                options = {
                    "compact_allocation": torrent_state.compact,
                    "max_connections_per_torrent": torrent_state.max_connections,
                    "max_upload_slots_per_torrent": torrent_state.max_upload_slots,
                    "max_upload_speed_per_torrent": torrent_state.max_upload_speed,
                    "max_download_speed_per_torrent": torrent_state.max_download_speed,
                    "prioritize_first_last_pieces": torrent_state.prioritize_first_last,
                    "download_location": torrent_state.save_path,
                    "add_paused": True,
                    "default_private": torrent_state.private,
                    "file_priorities": torrent_state.file_priorities
                }
                # We need to resume all non-add_paused torrents after plugin hook
                if torrent_state.state == "Paused" or torrent_state.state == "Queued":
                    log.debug("torrent state: %s", torrent_state.state)
                    add_paused[torrent_state.torrent_id] = True
                else:
                    add_paused[torrent_state.torrent_id] = False
                
                self.add(
                    torrent_state.filename,
                    options=options,
                    total_uploaded=torrent_state.total_uploaded,
                    trackers=torrent_state.trackers,
                    queue=torrent_state.queue,
                    state=torrent_state.state,
                    save_state=False)
                
            except AttributeError, e:
                log.error("Torrent state file is either corrupt or incompatible!")
                add_paused = {}
                break
       
        # Run the post_session_load plugin hooks
        self.plugins.run_post_session_load()
        
        # Resume any torrents that need to be resumed
        log.debug("add_paused: %s", add_paused)
        for key in add_paused.keys():
            if add_paused[key] == False:
                self.torrents[key].handle.resume()
                if self.torrents[key].get_status(["is_seed"])["is_seed"]:
                    self.torrents[key].state = "Seeding"
                else:
                    self.torrents[key].state = "Downloading"
             
    def save_state(self):
        """Save the state of the TorrentManager to the torrents.state file"""
        state = TorrentManagerState()
        # Create the state for each Torrent and append to the list
        for torrent in self.torrents.values():
            torrent_state = TorrentState(
                torrent.torrent_id,
                torrent.filename, 
                torrent.get_status(["total_uploaded"])["total_uploaded"], 
                torrent.trackers,
                torrent.compact, 
                torrent.state, 
                torrent.save_path,
                torrent.max_connections,
                torrent.max_upload_slots,
                torrent.max_upload_speed,
                torrent.max_download_speed,
                torrent.prioritize_first_last,
                torrent.private,
                torrent.file_priorities,
                torrent.get_status(["queue"])["queue"] - 1 # We subtract 1 due to augmentation
            )
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
    
    def on_set_max_connections_per_torrent(self, key, value):
        """Sets the per-torrent connection limit"""
        log.debug("max_connections_per_torrent set to %s..", value)
        for key in self.torrents.keys():
            self.torrents[key].set_max_connections(value)
        
    def on_set_max_upload_slots_per_torrent(self, key, value):
        """Sets the per-torrent upload slot limit"""
        log.debug("max_upload_slots_per_torrent set to %s..", value)
        for key in self.torrents.keys():
            self.torrents[key].set_max_upload_slots(value)
    
    def on_set_max_upload_speed_per_torrent(self, key, value):
        log.debug("max_upload_speed_per_torrent set to %s..", value)
        for key in self.torrents.keys():
            self.torrents[key].set_max_upload_speed(value)
    
    def on_set_max_download_speed_per_torrent(self, key, value):
        log.debug("max_download_speed_per_torrent set to %s..", value)
        for key in self.torrents.keys():
            self.torrents[key].set_max_download_speed(value)

    ## Alert handlers ##
    def on_alert_torrent_finished(self, alert):
        log.debug("on_alert_torrent_finished")
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        log.debug("%s is finished..", torrent_id)
        # Queue to bottom if enabled
        if alert.msg() == "torrent has finished downloading":
            if self.config["queue_finished_to_bottom"]:
                self.queue.bottom(torrent_id)

        # Set the torrent state
        if self.queue.get_num_seeding() < self.config["max_active_seeding"] or\
                self.config["max_active_seeding"] == -1:
            self.torrents[torrent_id].set_state("Seeding")
        else:
            self.torrents[torrent_id].set_state("Queued")
            
        # Write the fastresume file
        self.torrents[torrent_id].write_fastresume()
        
    def on_alert_torrent_paused(self, alert):
        log.debug("on_alert_torrent_paused")
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        # Set the torrent state
        log.debug("not_state_paused: %s", self.not_state_paused)
        if not torrent_id in self.not_state_paused:
            log.debug("Setting state 'Paused'..")
            self.torrents[torrent_id].set_state("Paused")
            component.get("SignalManager").emit("torrent_paused", torrent_id)
        else:
            self.not_state_paused.remove(torrent_id)
            
        # Write the fastresume file
        self.torrents[torrent_id].write_fastresume()
            
    def on_alert_torrent_checked(self, alert):
        log.debug("on_alert_torrent_checked")
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        # Set the torrent state
        self.torrents[torrent_id].set_state("Downloading")
                
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
            self.torrents[torrent_id].scrape_tracker()

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
            
    def on_alert_storage_moved(self, alert):
        log.debug("on_alert_storage_moved")
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        try:
            self.torrents[torrent_id].set_save_path(alert.handle.save_path())
        except KeyError:
            log.debug("torrent_id doesn't exist.")
                    
