#
# core.py
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

from torrentqueue import TorrentQueue
from deluge.log import LOG as log
from deluge.plugins.corepluginbase import CorePluginBase

class Core(CorePluginBase):
    def enable(self):
        # Instantiate the TorrentQueue object
        self.queue = TorrentQueue()
        
        # Register core hooks
        self.plugin.register_hook("post_torrent_add", self._post_torrent_add)
        self.plugin.register_hook("post_torrent_remove", 
                                                    self._post_torrent_remove)

        # Register the 'queue' status field
        self.plugin.register_status_field("queue", self._status_field_queue)
        
        log.debug("Queue Core plugin enabled..")
    
    def disable(self):
        # Save queue state
        self.queue.save_state()
        # Delete the queue
        del self.queue
        self.queue = None
        # De-register hooks
        self.plugin.deregister_hook("post_torrent_add", self._post_torrent_add)
        self.plugin.deregister_hook("post_torrent_remove",
            self._post_torrent_remove)
        
        # De-register status fields
        self.plugin.deregister_status_field("queue")

    ## Hooks for core ##
    def _post_torrent_add(self, torrent_id):
        if torrent_id is not None:
            self.queue.append(torrent_id)
    
    def _post_torrent_remove(self, torrent_id):
        if torrent_id is not None:
            self.queue.remove(torrent_id)
    
    ## Status field function ##
    def _status_field_queue(self, torrent_id):
        try:
            return self.queue[torrent_id]+1
        except TypeError:
            return None
        
    ## Queueing functions ##
    def export_queue_top(self, torrent_id):
        log.debug("Attempting to queue %s to top", torrent_id)
        try:
            # If the queue method returns True, then we should emit a signal
            if self.queue.top(torrent_id):
                self._torrent_queue_changed()
        except KeyError:
            log.warning("torrent_id: %s does not exist in the queue", 
                                                                    torrent_id)

    def export_queue_up(self, torrent_id):
        log.debug("Attempting to queue %s to up", torrent_id)
        try:
            # If the queue method returns True, then we should emit a signal
            if self.queue.up(torrent_id):
                self._torrent_queue_changed()
        except KeyError:
            log.warning("torrent_id: %s does not exist in the queue", 
                                                                    torrent_id)

    def export_queue_down(self, torrent_id):
        log.debug("Attempting to queue %s to down", torrent_id)
        try:
            # If the queue method returns True, then we should emit a signal
            if self.queue.down(torrent_id):
                self._torrent_queue_changed()
        except KeyError:
            log.warning("torrent_id: %s does not exist in the queue", 
                                                                    torrent_id)

    def export_queue_bottom(self, torrent_id):
        log.debug("Attempting to queue %s to bottom", torrent_id)
        try:
            # If the queue method returns True, then we should emit a signal
            if self.queue.bottom(torrent_id):
                self._torrent_queue_changed()
        except KeyError:
            log.warning("torrent_id: %s does not exist in the queue", 
                                                                    torrent_id)
    
    def export_get_queue_list(self):
        """Returns the queue list.
        """
        log.debug("Getting queue list")
        return self.queue.queue
    
    def export_get_position(self, torrent_id):
        """Returns the queue position of torrent_id"""
        log.debug("Getting queue position for %s", torrent_id)
        return self.queue[torrent_id]
       
    ## Signals ##
    def _torrent_queue_changed(self):
        """Emitted when a torrent queue position is changed"""
        log.debug("torrent_queue_changed signal emitted")
