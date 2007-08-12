#
# torrentview.py
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

import logging

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
import gobject
import gettext

import deluge.ui.functions as functions
import listview

# Get the logger
log = logging.getLogger("deluge")

class TorrentView:
    def __init__(self, window):
        log.debug("TorrentView Init..")
        self.window = window
        self.core = functions.get_core()
        # Create a ListView object using the torrent_view from the mainwindow
        self.torrent_view = listview.ListView(
                            self.window.main_glade.get_widget("torrent_view"))

        self.torrent_view.add_text_column("torrent_id", visible=False)
        self.torrent_view.add_texticon_column("Name")
        self.torrent_view.add_func_column("Size", 
                                            listview.cell_data_size, 
                                            [long])
        self.torrent_view.add_progress_column("Progress")
        self.torrent_view.add_func_column("Seeders",
                                            listview.cell_data_peer,
                                            [int, int])
        self.torrent_view.add_func_column("Peers",
                                            listview.cell_data_peer,
                                            [int, int])
        self.torrent_view.add_func_column("Down Speed",
                                            listview.cell_data_speed,
                                            [int])
        self.torrent_view.add_func_column("Up Speed",
                                            listview.cell_data_speed,
                                            [int])
        self.torrent_view.add_func_column("ETA",
                                            listview.cell_data_time,
                                            [int])
        self.torrent_view.add_func_column("Ratio",
                                            listview.cell_data_ratio,
                                            [float])
       
        ### Connect Signals ###
        # Connect to the 'button-press-event' to know when to bring up the
        # torrent menu popup.
        self.torrent_view.treeview.connect("button-press-event",
                                    self.on_button_press_event)
        # Connect to the 'changed' event of TreeViewSelection to get selection
        # changes.
        self.torrent_view.treeview.get_selection().connect("changed", 
                                    self.on_selection_changed)
    
    def update(self):
        pass
    
    def add_row(self, torrent_id):
        pass
    
    def remove_row(self, torrent_id):
        pass
                    
    def get_selected_torrents(self):
        pass
                
    ### Callbacks ###                             
    def on_button_press_event(self, widget, event):
        log.debug("on_button_press_event")
        # We only care about right-clicks
        if event.button == 3:
            # Show the Torrent menu from the MenuBar
            torrentmenu = self.window.menubar.torrentmenu.get_widget(
                                                                "torrent_menu")
            torrentmenu.popup(None, None, None, event.button, event.time)
    
    def on_selection_changed(self, treeselection):
        log.debug("on_selection_changed")
        
