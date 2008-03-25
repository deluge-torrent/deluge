#
# torrentdetails.py
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

"""The torrent details component shows info about the selected torrent."""

import gtk, gtk.glade

import deluge.component as component
from deluge.ui.client import aclient as client
from statistics_tab import StatisticsTab
from details_tab import DetailsTab
from files_tab import FilesTab
from peers_tab import PeersTab

from deluge.log import LOG as log

class TorrentDetails(component.Component):
    def __init__(self):
        component.Component.__init__(self, "TorrentDetails", interval=2000)
        self.window = component.get("MainWindow")
        glade = self.window.main_glade
        
        self.notebook = glade.get_widget("torrent_info")
        self.details_tab = glade.get_widget("torrentdetails_tab")
        
        self.notebook.connect("switch-page", self._on_switch_page)

        statistics_tab = StatisticsTab()
        details_tab = DetailsTab()
        files_tab = FilesTab()
        peers_tab = PeersTab()
        
        self.tabs = []
        self.tabs.insert(0, statistics_tab)
        self.tabs.insert(1, details_tab)
        self.tabs.insert(2, files_tab)
        self.tabs.insert(3, peers_tab)
    
    def visible(self, visible):
        if visible:
            self.notebook.show()
        else:
            self.notebook.hide()
            self.window.vpaned.set_position(-1)
        
    def stop(self):
        # Save the state of the tabs
        for tab in self.tabs:
            try:
                tab.save_state()
            except AttributeError:
                pass
            
        self.clear()

    def update(self):
        if self.notebook.get_property("visible"):
            # Update the tab that is in view
            self.tabs[self.notebook.get_current_page()].update()
                    
    def clear(self):
        self.tabs[self.notebook.get_current_page()].clear()

    def _on_switch_page(self, notebook, page, page_num):
        self.tabs[page_num].update()
        client.force_call(False)

