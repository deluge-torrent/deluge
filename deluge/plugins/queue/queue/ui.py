#
# ui.py
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

import gettext
import locale
import pkg_resources
from deluge.ui.client import aclient as client
from deluge.log import LOG as log

class UI:
    def __init__(self, plugin_api, plugin_name):
        self.plugin = plugin_api
        # Initialize gettext
        locale.setlocale(locale.LC_MESSAGES, '')
        locale.bindtextdomain("deluge", 
                    pkg_resources.resource_filename(
                                            "deluge", "i18n"))
        locale.textdomain("deluge")
        gettext.bindtextdomain("deluge",
                    pkg_resources.resource_filename(
                                            "deluge", "i18n"))
        gettext.textdomain("deluge")
        gettext.install("deluge",
                    pkg_resources.resource_filename(
                                            "deluge", "i18n"))

    def enable(self):
        log.debug("Enabling UI plugin")
        # Load the interface and connect the callbacks
        self.load_interface()
        
    def disable(self):
        self.unload_interface()
        
    def load_interface(self):
        pass
    
    def unload_interface(self):
        pass
        
    def update(self):
        pass
        
    ## Menu callbacks ##
    def on_queuetop_activate(self, data=None):
        log.debug("on_menuitem_queuetop_activate")
        # Get the selected torrents
        torrent_ids = self.plugin.get_selected_torrents()
        for torrent_id in torrent_ids:
            try:
                client.queue_queue_top(torrent_id)
            except Exception, e:
                log.debug("Unable to queue top torrent: %s", e)
        return
                
    def on_queueup_activate(self, data=None):
        log.debug("on_menuitem_queueup_activate")
        # Get the selected torrents
        torrent_ids = self.plugin.get_selected_torrents()
        for torrent_id in torrent_ids:
            try:
                client.queue_queue_up(torrent_id)
            except Exception, e:
                log.debug("Unable to queue up torrent: %s", e)
        return
        
    def on_queuedown_activate(self, data=None):
        log.debug("on_menuitem_queuedown_activate")
        # Get the selected torrents
        torrent_ids = self.plugin.get_selected_torrents()
        for torrent_id in torrent_ids:
            try:
                client.queue_queue_down(torrent_id)
            except Exception, e:
                log.debug("Unable to queue down torrent: %s", e)
        return
                
    def on_queuebottom_activate(self, data=None):
        log.debug("on_menuitem_queuebottom_activate")
        # Get the selected torrents
        torrent_ids = self.plugin.get_selected_torrents()
        for torrent_id in torrent_ids:
            try:
                client.queue_queue_bottom(torrent_id)
            except Exception, e:
                log.debug("Unable to queue bottom torrent: %s", e)
        return
    
    ## Signals ##
    def torrent_queue_changed_signal(self):
        """This function is called whenever we receive a 'torrent_queue_changed'
        signal from the core plugin.
        """
        log.debug("torrent_queue_changed signal received..")
        # We only need to update the queue column
        self.update()
        return

