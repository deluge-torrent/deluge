#
# peers_tab.py
#
# Copyright (C) 2008 Andrew Resch ('andar') <andrewresch@gmail.com>
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

import gtk, gtk.glade
import os.path
import cPickle

from deluge.ui.client import aclient as client
from deluge.configmanager import ConfigManager
import deluge.component as component
import deluge.common
from deluge.ui.gtkui.listview import cell_data_speed as cell_data_speed
from deluge.log import LOG as log

def cell_data_country(column, cell, model, row, data):
    pass

class ColumnState:
    def __init__(self, name, position, width, sort, sort_order):
        self.name = name
        self.position = position
        self.width = width
        self.sort = sort
        self.sort_order = sort_order
            
class PeersTab:
    def __init__(self):
        glade = component.get("MainWindow").get_glade()
        self.listview = glade.get_widget("peers_listview")
        # country, ip, client, progress, progress, downspeed, upspeed
        self.liststore = gtk.ListStore(str, str, str, str, int, int, int)
        
        # Country column        
        column = gtk.TreeViewColumn()
        render = gtk.CellRendererPixbuf()
        column.pack_start(render, False)
        column.set_cell_data_func(render, cell_data_country, 0)
        column.set_sort_column_id(0)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        self.listview.append_column(column)
        
        # Address column        
        column = gtk.TreeViewColumn(_("Address"))
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.add_attribute(render, "text", 1)
        column.set_sort_column_id(1)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        self.listview.append_column(column)

        # Client column        
        column = gtk.TreeViewColumn(_("Client"))
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.add_attribute(render, "text", 2)
        column.set_sort_column_id(2)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        self.listview.append_column(column)

        # Progress column        
        column = gtk.TreeViewColumn(_("Progress"))
        render = gtk.CellRendererProgress()
        column.pack_start(render)
        column.add_attribute(render, "text", 3)
        column.add_attribute(render, "value", 4)
        column.set_sort_column_id(4)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        self.listview.append_column(column)
        
        # Down Speed column
        column = gtk.TreeViewColumn(_("Down Speed"))
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.set_cell_data_func(render, cell_data_speed, 5)
        column.set_sort_column_id(5)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        self.listview.append_column(column)        
        
        # Up Speed column
        column = gtk.TreeViewColumn(_("Up Speed"))
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.set_cell_data_func(render, cell_data_speed, 6)
        column.set_sort_column_id(6)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        self.listview.append_column(column)        

        self.listview.set_model(self.liststore)
        
        self.load_state()
        
        self.torrent_id = None

    def save_state(self):
        filename = "peers_tab.state"
        state = []
        for index, column in enumerate(self.listview.get_columns()):
            state.append(ColumnState(column.get_title(), index, column.get_width(), 
                column.get_sort_indicator(), int(column.get_sort_order())))
        
        # Get the config location for saving the state file
        config_location = ConfigManager("gtkui.conf")["config_location"]

        try:
            log.debug("Saving FilesTab state file: %s", filename)
            state_file = open(os.path.join(config_location, filename), "wb")
            cPickle.dump(state, state_file)
            state_file.close()
        except IOError, e:
            log.warning("Unable to save state file: %s", e)
    
    def load_state(self):
        filename = "peers_tab.state"
        # Get the config location for loading the state file
        config_location = ConfigManager("gtkui.conf")["config_location"]
        state = None
        
        try:
            log.debug("Loading FilesTab state file: %s", filename)
            state_file = open(os.path.join(config_location, filename), "rb")
            state = cPickle.load(state_file)
            state_file.close()
        except IOError, e:
            log.warning("Unable to load state file: %s", e)
        
        if state == None:
            return
            
        for column_state in state:
            # Find matching columns in the listview
            for (index, column) in enumerate(self.listview.get_columns()):
                if column_state.name == column.get_title():
                    # We have a match, so set options that were saved in state
                    if column_state.width > 0:
                        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
                        column.set_fixed_width(column_state.width)
                        column.set_sort_indicator(column_state.sort)
                        column.set_sort_order(column_state.sort_order)
                    if column_state.position != index:
                        # Column is in wrong position
                        if column_state.position == 0:
                            self.listview.move_column_after(column, None)
                        else:
                            self.listview.move_column_after(column, self.listview.get_columns()[column_state.position - 1])
    
    def update(self):
        # Get the first selected torrent
        torrent_id = component.get("TorrentView").get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if len(torrent_id) != 0:
            torrent_id = torrent_id[0]
        else:
            # No torrent is selected in the torrentview
            self.liststore.clear()
            return
        
        if torrent_id != self.torrent_id:
            # We only want to do this if the torrent_id has changed
            self.liststore.clear()
            self.torrent_id = torrent_id
        log.debug("torrent_id: %s", torrent_id)
        client.get_torrent_status(self._on_get_torrent_status, torrent_id, ["peers"])

    def _on_get_torrent_status(self, status):
        self.liststore.clear()
        log.debug("status: %s", status)
        for peer in status["peers"]:
            self.liststore.append([
                peer["country"], 
                peer["ip"],
                peer["client"], 
                "%.2f%%" % peer["progress"], 
                peer["progress"], 
                peer["down_speed"], 
                peer["up_speed"]])
            
    def clear(self):
        self.liststore.clear()
