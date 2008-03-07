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

import os

import deluge.libtorrent as lt
import deluge.common
import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

TORRENT_STATE = deluge.common.TORRENT_STATE

class Torrent:
    """Torrent holds information about torrents added to the libtorrent session.
    """
    def __init__(self, filename, handle, compact, save_path, total_uploaded=0,
        trackers=None):
        # Get the core config
        self.config = ConfigManager("core.conf")
        
        # Get a reference to the TorrentQueue
        self.torrentqueue = component.get("TorrentQueue")
        
        # Set the filename
        self.filename = filename
        # Set the libtorrent handle
        self.handle = handle
        # Set the torrent_id for this torrent
        self.torrent_id = str(handle.info_hash())
        # This is for saving the total uploaded between sessions
        self.total_uploaded = total_uploaded
        # Set the allocation mode
        self.compact = compact
        # Where the torrent is being saved to
        self.save_path = save_path
        # The state of the torrent
        self.state = "Paused"
        
        # Holds status info so that we don't need to keep getting it from lt
        self.status = self.handle.status()
        self.torrent_info = self.handle.torrent_info()
        
        # Set the initial state
        if self.status.state == deluge.common.LT_TORRENT_STATE["Allocating"]:
            self.set_state("Allocating")
        elif self.status.state == deluge.common.LT_TORRENT_STATE["Checking"]:
            self.set_state("Checking")
        else:
            self.set_state("Paused")
        
        # Various torrent options
        self.max_connections = -1
        self.max_upload_slots = -1
        self.max_upload_speed = -1
        self.max_download_speed = -1
        self.private = False
        self.prioritize_first_last = False
        
        # The tracker status
        self.tracker_status = ""
        # Tracker list
        if trackers == None:
            self.trackers = []
            # Create a list of trackers
            for value in self.handle.trackers():
                tracker = {}
                tracker["url"] = value.url
                tracker["tier"] = value.tier
                self.trackers.append(tracker)
        else:
            self.trackers = trackers
            self.set_trackers(self.trackers)
            
        # Files dictionary
        self.files = self.get_files()
        # Set the default file priorities to normal
        self.file_priorities = [1]* len(self.files)
        
    def set_tracker_status(self, status):
        """Sets the tracker status"""
        self.tracker_status = status
    
    def set_max_connections(self, max_connections):
        self.max_connections = int(max_connections)
        self.handle.set_max_connections(self.max_connections)
    
    def set_max_upload_slots(self, max_slots):
        self.max_upload_slots = int(max_slots)
        self.handle.set_max_uploads(self.max_upload_slots)
        
    def set_max_upload_speed(self, m_up_speed):
        self.max_upload_speed = m_up_speed
        self.handle.set_upload_limit(int(m_up_speed * 1024))
    
    def set_max_download_speed(self, m_down_speed):
        self.max_download_speed = m_down_speed
        self.handle.set_download_limit(int(m_down_speed * 1024))
    
    def set_private_flag(self, private):
        self.private = private
        self.handle.torrent_info().set_priv(private)
    
    def set_prioritize_first_last(self, prioritize):
        self.prioritize_first_last = prioritize
            
    def set_save_path(self, save_path):
        self.save_path = save_path
    
    def set_file_priorities(self, file_priorities):
        self.file_priorities = file_priorities
        self.handle.prioritize_files(file_priorities)
    
    def set_state(self, state):
        """Accepts state strings, ie, "Paused", "Seeding", etc."""

        if state not in TORRENT_STATE:
            log.debug("Trying to set an invalid state %s", state)
            return
            
        # Only set 'Downloading' or 'Seeding' state if not paused
        if state == "Downloading" or state == "Seeding":
            if self.handle.is_paused():
                state = "Paused"
        
        if state == "Queued":
            component.get("TorrentManager").append_not_state_paused(self.torrent_id)
            self.pause()
                   
        self.state = state
        
    def get_eta(self):
        """Returns the ETA in seconds for this torrent"""
        if self.status == None:
            status = self.handle.status()
        else:
            status = self.status
        
        left = status.total_wanted - status.total_done
        
        if left == 0 or status.download_payload_rate == 0:
            return 0
        
        try:
            eta = left / status.download_payload_rate
        except ZeroDivisionError:
            eta = 0
            
        return eta

    def get_ratio(self):
        """Returns the ratio for this torrent"""
        if self.status == None:
            status = self.handle.status()
        else:
            status = self.status
            
        up = self.total_uploaded + status.total_payload_upload
        down = status.total_done
        
        # Convert 'up' and 'down' to floats for proper calculation
        up = float(up)
        down = float(down)
        
        try:
            ratio = up / down
        except ZeroDivisionError:
            return 0.0

        return ratio

    def get_files(self):
        """Returns a list of files this torrent contains"""
        if self.torrent_info == None:
            torrent_info = self.handle.torrent_info()
        else:
            torrent_info = self.torrent_info
            
        ret = []
        files = torrent_info.files()
        for file in files:
            ret.append({
                'path': file.path,
                'size': file.size,
                'offset': file.offset
            })
        return ret

    def get_queue_position(self):
        # We augment the queue position + 1 so that the user sees a 1 indexed
        # list.
        
        return self.torrentqueue[self.torrent_id] + 1
        
    def get_status(self, keys):
        """Returns the status of the torrent based on the keys provided"""
        # Create the full dictionary
        self.status = self.handle.status()
        self.torrent_info = self.handle.torrent_info()
        
        # Adjust progress to be 0-100 value
        progress = self.status.progress * 100
        
        # Adjust status.distributed_copies to return a non-negative value
        distributed_copies = self.status.distributed_copies
        if distributed_copies < 0:
            distributed_copies = 0.0
            
        full_status = {
            "distributed_copies": distributed_copies,
            "total_done": self.status.total_done,
            "total_uploaded": self.total_uploaded + self.status.total_payload_upload,
            "state": self.state,
            "paused": self.status.paused,
            "progress": progress,
            "next_announce": self.status.next_announce.seconds,
            "total_payload_download": self.status.total_payload_download,
            "total_payload_upload": self.status.total_payload_upload,
            "download_payload_rate": self.status.download_payload_rate,
            "upload_payload_rate": self.status.upload_payload_rate,
            "num_peers": self.status.num_peers - self.status.num_seeds,
            "num_seeds": self.status.num_seeds,
            "total_peers": self.status.num_incomplete,
            "total_seeds":  self.status.num_complete,
            "total_wanted": self.status.total_wanted,
            "tracker": self.status.current_tracker,
            "trackers": self.trackers,
            "tracker_status": self.tracker_status,
            "save_path": self.save_path,
            "files": self.files,
            "file_priorities": self.file_priorities,
            "compact": self.compact,
            "max_connections": self.max_connections,
            "max_upload_slots": self.max_upload_slots,
            "max_upload_speed": self.max_upload_speed,
            "max_download_speed": self.max_download_speed,
            "prioritize_first_last": self.prioritize_first_last,
            "private": self.private
        }
        
        fns = {
            "name": self.torrent_info.name,
            "total_size": self.torrent_info.total_size,
            "num_files": self.torrent_info.num_files,
            "num_pieces": self.torrent_info.num_pieces,
            "piece_length": self.torrent_info.piece_length,
            "eta": self.get_eta,
            "ratio": self.get_ratio,
            "file_progress": self.handle.file_progress,
            "queue": self.get_queue_position,
            "is_seed": self.handle.is_seed,
        }

        self.status = None
        self.torrent_info = None
        
        # Create the desired status dictionary and return it
        status_dict = {}
        
        if len(keys) == 0:
            status_dict = full_status
            for key in fns:
                status_dict[key] = fns[key]()
        else:
            for key in keys:
                if key in full_status:
                    status_dict[key] = full_status[key]
                elif key in fns:
                    status_dict[key] = fns[key]()

        return status_dict
        
    def pause(self):
        """Pause this torrent"""
        if self.state == "Queued":
            self.set_state("Paused")
            return True
            
        try:
            self.handle.pause()
        except Exception, e:
            log.debug("Unable to pause torrent: %s", e)
            return False
        
        return True
    
    def resume(self):
        """Resumes this torrent"""
        #if not self.status.paused:
        #    return False
        
        try:
            self.handle.resume()
        except:
            return False
        
        # Set the state
        if self.handle.is_seed():
            self.set_state("Seeding")
        else:
            self.set_state("Downloading")
        
        status = self.get_status(["total_done", "total_wanted"])
        
        # Only delete the .fastresume file if we're still downloading stuff
        if status["total_done"] < status["total_wanted"]:
            self.delete_fastresume()
        return True
        
    def move_storage(self, dest):
        """Move a torrent's storage location"""
        try:
            self.handle.move_storage(dest)
        except:
            return False

        return True

    def write_fastresume(self):
        """Writes the .fastresume file for the torrent"""
        resume_data = lt.bencode(self.handle.write_resume_data())
        path = "%s/%s.fastresume" % (
            self.config["torrentfiles_location"], 
            self.filename)
        log.debug("Saving fastresume file: %s", path)
        try:
            fastresume = open(path, "wb")
            fastresume.write(resume_data)
            fastresume.close()
        except IOError:
            log.warning("Error trying to save fastresume file")        

    def delete_fastresume(self):
        """Deletes the .fastresume file"""
        path = "%s/%s.fastresume" % (
            self.config["torrentfiles_location"], 
            self.filename)
        log.debug("Deleting fastresume file: %s", path)
        try:
            os.remove(path)
        except Exception, e:
            log.warning("Unable to delete the fastresume file: %s", e)

    def force_reannounce(self):
        """Force a tracker reannounce"""
        try:
            self.handle.force_reannounce()
        except Exception, e:
            log.debug("Unable to force reannounce: %s", e)
            return False
        
        return True
    
    def scrape_tracker(self):
        """Scrape the tracker"""
        try:
            self.handle.scrape_tracker()
        except Exception, e:
            log.debug("Unable to scrape tracker: %s", e)
            return False
        
        return True
        
    def set_trackers(self, trackers):
        """Sets trackers"""
        if trackers == None:
            trackers = []
            
        log.debug("Setting trackers for %s: %s", self.torrent_id, trackers)
        tracker_list = []

        for tracker in trackers:
            new_entry = lt.announce_entry(tracker["url"])
            new_entry.tier = tracker["tier"]
            tracker_list.append(new_entry)
            
        self.handle.replace_trackers(tracker_list)
        
        # Print out the trackers
        for t in self.handle.trackers():
            log.debug("tier: %s tracker: %s", t.tier, t.url)
        # Set the tracker list in the torrent object
        self.trackers = trackers
        if len(trackers) > 0:
            # Force a reannounce if there is at least 1 tracker
            self.force_reannounce()

    def save_torrent_file(self, filedump=None):
        """Saves a torrent file"""
        log.debug("Attempting to save torrent file: %s", self.filename)
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
                    self.filename),
                    "wb")
            if filedump == None:
                filedump = self.handle.torrent_info().create_torrent()
            save_file.write(lt.bencode(filedump))
            save_file.close()
        except IOError, e:
            log.warning("Unable to save torrent file: %s", e)
