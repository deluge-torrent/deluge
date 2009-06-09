#
# torrentmanager.py
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
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
# 	Boston, MA  02110-1301, USA.
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
#

#


"""TorrentManager handles Torrent objects"""

import cPickle
import os.path
import os
import time
import shutil

import gobject

try:
    import deluge.libtorrent as lt
except ImportError:
    import libtorrent as lt
    if not (lt.version_major == 0 and lt.version_minor == 14):
        raise ImportError("This version of Deluge requires libtorrent 0.14!")


import deluge.common
import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.core.torrent import Torrent
from deluge.core.torrent import TorrentOptions
import deluge.core.oldstateupgrader

from deluge.log import LOG as log

class TorrentState:
    def __init__(self,
            torrent_id=None,
            filename=None,
            total_uploaded=0,
            trackers=None,
            compact=False,
            paused=False,
            save_path=None,
            max_connections=-1,
            max_upload_slots=-1,
            max_upload_speed=-1.0,
            max_download_speed=-1.0,
            prioritize_first_last=False,
            file_priorities=None,
            queue=None,
            auto_managed=True,
            is_finished=False,
            stop_ratio=2.00,
            stop_at_ratio=False,
            remove_at_ratio=False,
            magnet=None,
            time_added=-1
        ):
        self.torrent_id = torrent_id
        self.filename = filename
        self.total_uploaded = total_uploaded
        self.trackers = trackers
        self.queue = queue
        self.is_finished = is_finished
        self.magnet = magnet
        self.time_added = time_added

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
        self.stop_ratio = stop_ratio
        self.stop_at_ratio = stop_at_ratio
        self.remove_at_ratio = remove_at_ratio

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

        # This is a list of torrent_id when we shutdown the torrentmanager.
        # We use this list to determine if all active torrents have been paused
        # and that their resume data has been written.
        self.shutdown_torrent_pause_list = []

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
        self.alerts.register_handler("tracker_error_alert",
            self.on_alert_tracker_error)
        self.alerts.register_handler("storage_moved_alert",
            self.on_alert_storage_moved)
        self.alerts.register_handler("torrent_resumed_alert",
            self.on_alert_torrent_resumed)
        self.alerts.register_handler("state_changed_alert",
            self.on_alert_state_changed)
        self.alerts.register_handler("save_resume_data_alert",
            self.on_alert_save_resume_data)
        self.alerts.register_handler("save_resume_data_failed_alert",
            self.on_alert_save_resume_data_failed)
        self.alerts.register_handler("file_renamed_alert",
            self.on_alert_file_renamed)
        self.alerts.register_handler("metadata_received_alert",
            self.on_alert_metadata_received)
        self.alerts.register_handler("file_error_alert",
            self.on_alert_file_error)

    def start(self):
        # Get the pluginmanager reference
        self.plugins = component.get("PluginManager")

        self.signals = component.get("SignalManager")

        # Run the old state upgrader before loading state
        deluge.core.oldstateupgrader.OldStateUpgrader()

        # Try to load the state from file
        self.load_state()

        # Save the state every 5 minutes
        self.save_state_timer = gobject.timeout_add(300000, self.save_state)
        self.save_resume_data_timer = gobject.timeout_add(290000, self.save_resume_data)

    def stop(self):
        # Save state on shutdown
        self.save_state()

        for key in self.torrents.keys():
            if not self.torrents[key].handle.is_paused():
                # We set auto_managed false to prevent lt from resuming the torrent
                self.torrents[key].handle.auto_managed(False)
                self.torrents[key].handle.pause()
                self.shutdown_torrent_pause_list.append(key)
        # We have to wait for all torrents to pause and write their resume data
        wait = True
        while wait:
            if self.shutdown_torrent_pause_list:
                wait = True
            else:
                wait = False
                for torrent in self.torrents.values():
                    if torrent.waiting_on_resume_data:
                        wait = True
                        break

            time.sleep(0.01)
            # Wait for all alerts
            self.alerts.handle_alerts(True)

    def update(self):
        for torrent_id, torrent in self.torrents.items():
            if self.config["stop_seed_at_ratio"] or torrent.options["stop_at_ratio"] and torrent.state not in ("Checking", "Allocating"):
                stop_ratio = self.config["stop_seed_ratio"]
                if torrent.options["stop_at_ratio"]:
                    stop_ratio = torrent.options["stop_ratio"]
                if torrent.get_ratio() >= stop_ratio and torrent.is_finished:
                    if self.config["remove_seed_at_ratio"] or torrent.options["remove_at_ratio"]:
                        self.remove(torrent_id)
                        break
                    if not torrent.handle.is_paused():
                        torrent.pause()

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
        fastresume = ""
        try:
            _file = open(
                os.path.join(
                    self.config["state_location"],
                    torrent_id + ".fastresume"),
                    "rb")
            fastresume = _file.read()
            _file.close()
        except IOError, e:
            log.debug("Unable to load .fastresume: %s", e)

        return str(fastresume)

    def add(self, torrent_info=None, state=None, options=None, save_state=True,
            filedump=None, filename=None, magnet=None):
        """Add a torrent to the manager and returns it's torrent_id"""

        if torrent_info is None and state is None and filedump is None and magnet is None:
            log.debug("You must specify a valid torrent_info, torrent state or magnet.")
            return

        log.debug("torrentmanager.add")
        add_torrent_params = {}

        if filedump is not None:
            try:
                torrent_info = lt.torrent_info(lt.bdecode(filedump))
            except Exception, e:
                log.error("Unable to decode torrent file!: %s", e)

        if torrent_info is None and state:
            # We have no torrent_info so we need to add the torrent with information
            # from the state object.

            # Populate the options dict from state
            options = TorrentOptions()
            options["max_connections"] = state.max_connections
            options["max_upload_slots"] = state.max_upload_slots
            options["max_upload_speed"] = state.max_upload_speed
            options["max_download_speed"] = state.max_download_speed
            options["prioritize_first_last_pieces"] = state.prioritize_first_last
            options["file_priorities"] = state.file_priorities
            options["compact_allocation"] = state.compact
            options["download_location"] = state.save_path
            options["auto_managed"] = state.auto_managed
            options["add_paused"] = state.paused

            if not state.magnet:
                add_torrent_params["ti"] =\
                    self.get_torrent_info_from_file(
                        os.path.join(self.config["state_location"], state.torrent_id + ".torrent"))

                if not add_torrent_params["ti"]:
                    log.error("Unable to add torrent!")
                    return
            else:
                magnet = state.magnet

            add_torrent_params["resume_data"] = self.get_resume_data_from_file(state.torrent_id)
        else:
            # We have a torrent_info object so we're not loading from state.
            # Check if options is None and load defaults
            if options == None:
                options = TorrentOptions()
            else:
                o = TorrentOptions()
                o.update(options)
                options = o

            add_torrent_params["ti"] = torrent_info
            add_torrent_params["resume_data"] = ""

        #log.info("Adding torrent: %s", filename)
        log.debug("options: %s", options)

        # Set the right storage_mode
        if options["compact_allocation"]:
            storage_mode = lt.storage_mode_t(2)
        else:
            storage_mode = lt.storage_mode_t(1)

        try:
            # Try to encode this as utf8 if needed
            options["download_location"] = options["download_location"].encode("utf8")
        except UnicodeDecodeError:
            pass

        # Fill in the rest of the add_torrent_params dictionary
        add_torrent_params["save_path"] = options["download_location"]
        add_torrent_params["storage_mode"] = storage_mode
        add_torrent_params["paused"] = True
        add_torrent_params["auto_managed"] = False
        add_torrent_params["duplicate_is_error"] = True

        # We need to pause the AlertManager momentarily to prevent alerts
        # for this torrent being generated before a Torrent object is created.
        component.pause("AlertManager")

        handle = None
        try:
            if magnet:
                handle = lt.add_magnet_uri(self.session, magnet, add_torrent_params)
            else:
                handle = self.session.add_torrent(add_torrent_params)
        except RuntimeError, e:
            log.warning("Error adding torrent: %s", e)

        if not handle or not handle.is_valid():
            log.debug("torrent handle is invalid!")
            # The torrent was not added to the session
            component.resume("AlertManager")
            return

        log.debug("handle id: %s", str(handle.info_hash()))
        # Set auto_managed to False because the torrent is paused
        handle.auto_managed(False)
        # Create a Torrent object
        torrent = Torrent(handle, options, state, filename, magnet)
        # Add the torrent object to the dictionary
        self.torrents[torrent.torrent_id] = torrent
        if self.config["queue_new_to_top"]:
            handle.queue_position_top()

        component.resume("AlertManager")

        # Resume the torrent if needed
        if not options["add_paused"]:
            torrent.resume()

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

    def remove(self, torrent_id, remove_data=False):
        """Remove a torrent from the manager"""
        try:
            self.session.remove_torrent(self.torrents[torrent_id].handle,
                1 if remove_data else 0)
        except (RuntimeError, KeyError), e:
            log.warning("Error removing torrent: %s", e)
            return False

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

        # Emit the signal to the clients
        self.signals.emit("torrent_removed", torrent_id)

        return True

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
                    ordered_state.insert(ordered_state.index(t), torrent_state)
                    break
            if torrent_state not in ordered_state:
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
                torrent.options["compact_allocation"],
                paused,
                torrent.options["download_location"],
                torrent.options["max_connections"],
                torrent.options["max_upload_slots"],
                torrent.options["max_upload_speed"],
                torrent.options["max_download_speed"],
                torrent.options["prioritize_first_last_pieces"],
                torrent.options["file_priorities"],
                torrent.get_queue_position(),
                torrent.options["auto_managed"],
                torrent.is_finished,
                torrent.options["stop_ratio"],
                torrent.options["stop_at_ratio"],
                torrent.options["remove_at_ratio"],
                torrent.magnet,
                torrent.time_added
            )
            state.torrents.append(torrent_state)

        # Pickle the TorrentManagerState object
        try:
            log.debug("Saving torrent state file.")
            state_file = open(
                os.path.join(self.config["state_location"], "torrents.state.new"),
                                                                        "wb")
            cPickle.dump(state, state_file)
            state_file.flush()
            os.fsync(state_file.fileno())
            state_file.close()
        except IOError:
            log.warning("Unable to save state file.")
            return True

        # We have to move the 'torrents.state.new' file to 'torrents.state'
        try:
            shutil.move(
                os.path.join(self.config["state_location"], "torrents.state.new"),
                os.path.join(self.config["state_location"], "torrents.state"))
        except IOError:
            log.warning("Unable to save state file.")
            return True

        # We return True so that the timer thread will continue
        return True

    def save_resume_data(self):
        """Saves resume data for all the torrents"""
        for torrent in self.torrents.values():
            torrent.save_resume_data()

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
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return
        torrent_id = str(alert.handle.info_hash())
        log.debug("%s is finished..", torrent_id)
        # Move completed download to completed folder if needed
        if not torrent.is_finished:
            move_path = None
            if torrent.options["move_completed"]:
                move_path = torrent.options["move_completed_path"]
            elif self.config["move_completed"]:
                move_path = self.config["move_completed_path"]
            # Get the total_download and if it's 0, do not move.. It's likely
            # that the torrent wasn't downloaded, but just added.
            total_download = torrent.get_status(["total_payload_download"])["total_payload_download"]
            if move_path and total_download:
                if torrent.options["download_location"] != move_path:
                    torrent.move_storage(move_path)
            torrent.is_finished = True
            component.get("SignalManager").emit("torrent_finished", torrent_id)

        torrent.update_state()
        torrent.save_resume_data()

    def on_alert_torrent_paused(self, alert):
        log.debug("on_alert_torrent_paused")
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return
        # Get the torrent_id
        torrent_id = str(alert.handle.info_hash())
        # Set the torrent state
        torrent.update_state()
        component.get("SignalManager").emit("torrent_paused", torrent_id)

        # Write the fastresume file
        torrent.save_resume_data()

        if torrent_id in self.shutdown_torrent_pause_list:
            self.shutdown_torrent_pause_list.remove(torrent_id)

    def on_alert_torrent_checked(self, alert):
        log.debug("on_alert_torrent_checked")
        # Get the torrent_id
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return
        # Set the torrent state
        torrent.update_state()

    def on_alert_tracker_reply(self, alert):
        log.debug("on_alert_tracker_reply: %s", alert.message().decode("utf8"))
        # Get the torrent_id
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return
        # Set the tracker status for the torrent
        if alert.message() != "Got peers from DHT":
            torrent.set_tracker_status(_("Announce OK"))

        # Check to see if we got any peer information from the tracker
        if alert.handle.status().num_complete == -1 or \
            alert.handle.status().num_incomplete == -1:
            # We didn't get peer information, so lets send a scrape request
            torrent.scrape_tracker()

    def on_alert_tracker_announce(self, alert):
        log.debug("on_alert_tracker_announce")
        # Get the torrent_id
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return

        # Set the tracker status for the torrent
        torrent.set_tracker_status(_("Announce Sent"))

    def on_alert_tracker(self, alert):
        log.debug("on_alert_tracker")
        # Get the torrent_id
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return

        tracker_status = "%s: %s" % \
            (_("Alert"), str(alert.message()).strip('"')[8:])
        # Set the tracker status for the torrent
        torrent.set_tracker_status(tracker_status)

    def on_alert_tracker_warning(self, alert):
        log.debug("on_alert_tracker_warning")
        # Get the torrent_id
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return
        tracker_status = '%s: %s' % (_("Warning"), str(alert.message()))
        # Set the tracker status for the torrent
        torrent.set_tracker_status(tracker_status)

    def on_alert_tracker_error(self, alert):
        log.debug("on_alert_tracker_error")
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return
        tracker_status = "%s: %s" % (_("Error"), alert.msg)
        torrent.set_tracker_status(tracker_status)

    def on_alert_storage_moved(self, alert):
        log.debug("on_alert_storage_moved")
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return
        torrent.set_save_path(alert.handle.save_path())

    def on_alert_torrent_resumed(self, alert):
        log.debug("on_alert_torrent_resumed")
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return
        torrent.is_finished = torrent.handle.is_seed()
        torrent.update_state()

    def on_alert_state_changed(self, alert):
        log.debug("on_alert_state_changed")
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return
        torrent_id = str(alert.handle.info_hash())
        torrent.update_state()
        component.get("SignalManager").emit("torrent_state_changed", torrent_id)

    def on_alert_save_resume_data(self, alert):
        log.debug("on_alert_save_resume_data")
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return
        torrent.write_resume_data(alert.resume_data)

    def on_alert_save_resume_data_failed(self, alert):
        log.debug("on_alert_save_resume_data_failed: %s", alert.message())
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return
        torrent.waiting_on_resume_data = False

    def on_alert_file_renamed(self, alert):
        log.debug("on_alert_file_renamed")
        log.debug("index: %s name: %s", alert.index, alert.name.decode("utf8"))
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return
        torrent_id = str(alert.handle.info_hash())

        torrent.files[alert.index]["path"] = alert.name

        # We need to see if this file index is in a waiting_on_folder list
        folder_rename = False
        for i, wait_on_folder in enumerate(torrent.waiting_on_folder_rename):
            if alert.index in wait_on_folder[2]:
                folder_rename = True
                if len(wait_on_folder[2]) == 1:
                    # This is the last alert we were waiting for, time to send signal
                    component.get("SignalManager").emit("torrent_folder_renamed", torrent_id, wait_on_folder[0], wait_on_folder[1])
                    del torrent.waiting_on_folder_rename[i]
                    break
                # This isn't the last file to be renamed in this folder, so just
                # remove the index and continue
                torrent.waiting_on_folder_rename[i][2].remove(alert.index)

        if not folder_rename:
            # This is just a regular file rename so send the signal
            component.get("SignalManager").emit("torrent_file_renamed", torrent_id, alert.index, alert.name)

    def on_alert_metadata_received(self, alert):
        log.debug("on_alert_metadata_received")
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return
        torrent.write_torrentfile()

    def on_alert_file_error(self, alert):
        log.debug("on_alert_file_error: %s", alert.message())
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except:
            return
        torrent.update_state()
