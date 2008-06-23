#
# torrentmanager.py
#
# Copyright (C) 2007, 2008 Andrew Resch ('andar') <andrewresch@gmail.com>
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
    def __init__(self,
            torrent_id=None,
            filename=None,
            total_uploaded=None, 
            trackers=None,
            compact=None, 
            paused=None, 
            save_path=None,
            max_connections=None,
            max_upload_slots=None,
            max_upload_speed=None,
            max_download_speed=None,
            prioritize_first_last=None,
            file_priorities=None,
            queue=None,
            auto_managed=None,
            is_finished=False
        ):
        self.torrent_id = torrent_id
        self.filename = filename
        self.total_uploaded = total_uploaded
        self.trackers = trackers
        self.queue = queue
        self.is_finished = is_finished

        # Options
        self.compact = compact
        self.paused = paused
        self.save_path = save_path
        self.max_connections = max_connections
        self.max_upload_slots = max_upload_slots
        self.max_upload_speed = max_upload_speed
        self.max_download_speed = max_download_speed
        self.prioritize_first_last = prioritize_first_last
        self.file_priorities = file_priorities
        self.auto_managed = auto_managed

class TorrentManagerState:
    def __init__(self):
        self.torrents = []

class TorrentManager(component.Component):
    """TorrentManager contains a list of torrents in the current libtorrent
    session.  This object is also responsible for saving the state of the
    session for use on restart."""
    
    def __init__(self, session, alerts):
        component.Component.__init__(self, "TorrentManager", interval=5000, depend=["PluginManager"])
        log.debug("TorrentManager init..")
        # Set the libtorrent session
        self.session = session
        # Set the alertmanager
        self.alerts = alerts
        # Get the core config
        self.config = ConfigManager("core.conf")

        # Create the torrents dict { torrent_id: Torrent }
        self.torrents = {}
        
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
        self.alerts.register_handler("torrent_resumed_alert", 
            self.on_alert_torrent_resumed)
        
    def start(self):
        # Get the pluginmanager reference
        self.plugins = component.get("PluginManager")
        
        self.signals = component.get("SignalManager")
                
        # Try to load the state from file
        self.load_state()

        # Save the state every 5 minutes
        self.save_state_timer = gobject.timeout_add(300000, self.save_state)
                    
    def stop(self):
        # Save state on shutdown
        self.save_state()
        for key in self.torrents.keys():
            self.torrents[key].handle.pause()
        # Wait for all alerts
        self.alerts.handle_alerts(True)
                        
    def update(self):
        if self.config["stop_seed_at_ratio"]:
            for torrent in self.torrents:
                if torrent.get_ratio() >= self.config["stop_seed_ratio"] and torrent.is_finished:
                    torrent.pause()
                    if self.config["remove_seed_at_ratio"]:
                        self.remove(torrent.torrent_id)
                        
    def __getitem__(self, torrent_id):
        """Return the Torrent with torrent_id"""
        return self.torrents[torrent_id]
    
    def get_torrent_list(self):
        """Returns a list of torrent_ids"""
        return self.torrents.keys()
   
    def get_torrent_info_from_file(self, filepath):
        """Returns a torrent_info for the file specified or None"""
        torrent_info = None
        # Get the torrent data from the torrent file
        try:
            log.debug("Attempting to create torrent_info from %s", filepath)
            _file = open(filepath, "rb")
            torrent_info = lt.torrent_info(lt.bdecode(_file.read()))
            _file.close()
        except (IOError, RuntimeError), e:
            log.warning("Unable to open %s: %s", filepath, e)
        
        return torrent_info
    
    def get_resume_data_from_file(self, torrent_id):
        """Returns an entry with the resume data or None"""
        fastresume = None
        try:
            _file = open(
                os.path.join(
                    self.config["state_location"], 
                    torrent_id + ".fastresume"),
                    "rb")
            try:
                fastresume = lt.bdecode(_file.read())
            except RuntimeError, e:
                log.warning("Unable to bdecode fastresume file: %s", e)
                
            _file.close()
        except IOError, e:
            log.debug("Unable to load .fastresume: %s", e)
            
        return fastresume
                                    
    def add(self, torrent_info=None, state=None, options=None, save_state=True,
            filedump=None, filename=None):
        """Add a torrent to the manager and returns it's torrent_id"""
        
        if torrent_info is None and state is None and filedump is None:
            log.debug("You must specify a valid torrent_info or a torrent state object!")
            return

        log.debug("torrentmanager.add")
        add_torrent_params = {}
 
        if filedump is not None:
            try:
                torrent_info = lt.torrent_info(lt.bdecode(filedump))
            except Exception, e:
                log.error("Unable to decode torrent file!: %s", e)
            
        if torrent_info is None:
            # We have no torrent_info so we need to add the torrent with information
            # from the state object.

            # Populate the options dict from state
            options = {}
            options["max_connections_per_torrent"] = state.max_connections
            options["max_upload_slots_per_torrent"] = state.max_upload_slots
            options["max_upload_speed_per_torrent"] = state.max_upload_speed
            options["max_download_speed_per_torrent"] = state.max_download_speed
            options["prioritize_first_last_pieces"] = state.prioritize_first_last
            options["file_priorities"] = state.file_priorities
            options["compact_allocation"] = state.compact
            options["download_location"] = state.save_path
            options["auto_managed"] = state.auto_managed
            options["add_paused"] = state.paused
            
            add_torrent_params["ti"] =\
                self.get_torrent_info_from_file(
                    os.path.join(self.config["state_location"], state.torrent_id + ".torrent"))
            if not add_torrent_params["ti"]:
                log.error("Unable to add torrent!")
                return
                
            add_torrent_params["resume_data"] = self.get_resume_data_from_file(state.torrent_id)
        else:
            # We have a torrent_info object so we're not loading from state.
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
                "auto_managed"
            ]

            if options == None:
                options = {}
                for key in options_keys:
                    options[key] = self.config[key]
            else:
                for key in options_keys:
                    if not options.has_key(key):
                        options[key] = self.config[key]            

            add_torrent_params["ti"] = torrent_info
            add_torrent_params["resume_data"] = None
            
        #log.info("Adding torrent: %s", filename)
        log.debug("options: %s", options)
            
        # Set the right storage_mode
        if options["compact_allocation"]:
            storage_mode = lt.storage_mode_t(2)
        else:
            storage_mode = lt.storage_mode_t(1)
        
        # Fill in the rest of the add_torrent_params dictionary
        add_torrent_params["save_path"] = str(options["download_location"])

        add_torrent_params["storage_mode"] = storage_mode
        add_torrent_params["paused"] = True
        add_torrent_params["auto_managed"] = False
        add_torrent_params["duplicate_is_error"] = True
        
        # We need to pause the AlertManager momentarily to prevent alerts
        # for this torrent being generated before a Torrent object is created.
        component.pause("AlertManager")
        
        handle = None
        try:
            handle = self.session.add_torrent(add_torrent_params)
        except RuntimeError, e:
            log.warning("Error adding torrent: %s", e)
            
        if not handle or not handle.is_valid():
            log.debug("torrent handle is invalid!")
            # The torrent was not added to the session
            component.resume("AlertManager")
            return
        
        log.debug("handle id: %s", str(handle.info_hash()))
        # Create a Torrent object
        torrent = Torrent(handle, options, state, filename)
        # Add the torrent object to the dictionary
        self.torrents[torrent.torrent_id] = torrent
        if self.config["queue_new_to_top"]:
            handle.queue_position_top()
            
        component.resume("AlertManager")

        # Resume the torrent if needed
        if not options["add_paused"]:
            handle.resume()
            handle.auto_managed(options["auto_managed"])

        # Write the .torrent file to the state directory
        if filedump:
            try:
                save_file = open(os.path.join(self.config["state_location"], 
                        torrent.torrent_id + ".torrent"),
                        "wb")
                save_file.write(filedump)
                save_file.close()
            except IOError, e:
                log.warning("Unable to save torrent file: %s", e)

            # If the user has requested a copy of the torrent be saved elsewhere
            # we need to do that.
            if self.config["copy_torrent_file"] and filename is not None:
                try:
                    save_file = open(
                        os.path.join(self.config["torrentfiles_location"], filename),
                        "wb")
                    save_file.write(filedump)
                    save_file.close()
                except IOError, e:
                    log.warning("Unable to save torrent file: %s", e)

        if save_state:
            # Save the session state
            self.save_state()
        
        # Emit the torrent_added signal
        self.signals.emit("torrent_added", torrent.torrent_id)
                 
        return torrent.torrent_id

    def load_torrent(self, torrent_id):
        """Load a torrent file from state and return it's torrent info"""
        filedump = None
        # Get the torrent data from the torrent file
        try:
            log.debug("Attempting to open %s for add.", torrent_id)
            _file = open(
                os.path.join(
                    self.config["state_location"], torrent_id + ".torrent"), 
                        "rb")
            filedump = lt.bdecode(_file.read())
            _file.close()
        except (IOError, RuntimeError), e:
            log.warning("Unable to open %s: %s", torrent_id, e)
            return False
        
        return filedump
        
    def remove(self, torrent_id, remove_torrent=False, remove_data=False):
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
        
        # Remove the .torrent file in the state
        self.torrents[torrent_id].delete_torrentfile()
        
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
        
    def load_state(self):
        """Load the state of the TorrentManager from the torrents.state file"""
        state = TorrentManagerState()

        try:
            log.debug("Opening torrent state file for load.")
            state_file = open(
                os.path.join(self.config["state_location"], "torrents.state"), "rb")
            state = cPickle.load(state_file)
            state_file.close()
        except (EOFError, IOError, Exception), e:
            log.warning("Unable to load state file: %s", e)
            
        # Try to use an old state
        try:
            if dir(state.torrents[0]) != dir(TorrentState()):
                for attr in (set(dir(TorrentState())) - set(dir(state.torrents[0]))):
                    for s in state.torrents:
                        setattr(s, attr, getattr(TorrentState(), attr, None))
        except Exception, e:
            log.warning("Unable to update state file to a compatible version: %s", e)
                            
        # Reorder the state.torrents list to add torrents in the correct queue
        # order.
        ordered_state = []
        for torrent_state in state.torrents:
            for t in ordered_state:
                if torrent_state.queue < t.queue:
                    ordered_state.insert(0, torrent_state)
                    break
            ordered_state.append(torrent_state)
                   
        for torrent_state in ordered_state:
            try:
                self.add(state=torrent_state, save_state=False)
            except AttributeError, e:
                log.error("Torrent state file is either corrupt or incompatible!")
                break
       
        # Run the post_session_load plugin hooks
        self.plugins.run_post_session_load()

    def save_state(self):
        """Save the state of the TorrentManager to the torrents.state file"""
        state = TorrentManagerState()
        # Create the state for each Torrent and append to the list
        for torrent in self.torrents.values():
            paused = False
            if torrent.state == "Paused":
                paused = True
            
            torrent_state = TorrentState(
                torrent.torrent_id,
                torrent.filename,
                torrent.get_status(["total_uploaded"])["total_uploaded"], 
                torrent.trackers,
                torrent.compact, 
                paused, 
                torrent.save_path,
                torrent.max_connections,
                torrent.max_upload_slots,
                torrent.max_upload_speed,
                torrent.max_download_speed,
                torrent.prioritize_first_last,
                torrent.file_priorities,
                torrent.get_queue_position(),
                torrent.auto_managed,
                torrent.is_finished
            )
            state.torrents.append(torrent_state)
        
        # Pickle the TorrentManagerState object
        try:
            log.debug("Saving torrent state file.")
            state_file = open(
                os.path.join(self.config["state_location"], "torrents.state"), 
                                                                        "wb")
            cPickle.dump(state, state_file)
            state_file.close()
        except IOError:
            log.warning("Unable to save state file.")
            
        # We return True so that the timer thread will continue
        return True

    def queue_top(self, torrent_id):
        """Queue torrent to top"""
        if self.torrents[torrent_id].get_queue_position() == 0:
            return False

        self.torrents[torrent_id].handle.queue_position_top()
        return True

    def queue_up(self, torrent_id):
        """Queue torrent up one position"""
        if self.torrents[torrent_id].get_queue_position() == 0:
            return False

        self.torrents[torrent_id].handle.queue_position_up()
        return True

    def queue_down(self, torrent_id):
        """Queue torrent down one position"""
        if self.torrents[torrent_id].get_queue_position() == (len(self.torrents) - 1):
            return False
            
        self.torrents[torrent_id].handle.queue_position_down()
        return True

    def queue_bottom(self, torrent_id):
        """Queue torrent to bottom"""
        if self.torrents[torrent_id].get_queue_position() == (len(self.torrents) - 1):
            return False

        self.torrents[torrent_id].handle.queue_position_bottom()
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
        torrent = self.torrents[torrent_id]
        log.debug("%s is finished..", torrent_id)
        # Move completed download to completed folder if needed
        if self.config["move_completed"] and not torrent.is_finished:
            if torrent.save_path != self.config["move_completed_path"]:
                torrent.move_storage(self.config["move_completed_path"])

        torrent.is_finished = True
        torrent.update_state()
        torrent.write_fastresume()
        
    def on_alert_torrent_paused(self, alert):
        log.debug("on_alert_torrent_paused")
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        # Set the torrent state
        self.torrents[torrent_id].update_state()
        component.get("SignalManager").emit("torrent_paused", torrent_id)
            
        # Write the fastresume file
        self.torrents[torrent_id].write_fastresume()
    
    def on_alert_torrent_checked(self, alert):
        log.debug("on_alert_torrent_checked")
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        # Set the torrent state
        self.torrents[torrent_id].update_state()
        
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
        try:
            torrent_id = str(alert.handle.info_hash())
        except RuntimeError:
            log.debug("Invalid torrent handle.")
            return
            
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
        log.debug("save_path: %s", alert.handle.save_path())
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        try:
            log.debug("save_path2: %s", self.torrents[torrent_id].handle.save_path())
            self.torrents[torrent_id].set_save_path(alert.handle.save_path())
        except KeyError:
            log.debug("torrent_id doesn't exist.")

    def on_alert_torrent_resumed(self, alert):
        log.debug("on_alert_torrent_resumed")
        torrent = self.torrents[str(alert.handle.info_hash())]
        torrent.is_finished = torrent.handle.is_seed()
        torrent.update_state()
