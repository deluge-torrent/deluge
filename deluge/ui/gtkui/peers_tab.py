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

from deluge.ui.client import aclient as client
import deluge.component as component
import deluge.common

def cell_data_country(column, cell, model, row, data):
    pass
    
class PeersTab:
    def __init__(self):
        glade = component.get("MainWindow").get_glade()
        self.listview = glade.get_widget("peers_listview")
        # country, filename, size, priority
        self.liststore = gtk.ListStore(str, str, str, str, int, int, int)
        
        # Country column        
        column = gtk.TreeViewColumn()
        render = gtk.CellRendererPixbuf()
        column.pack_start(render, False)
        column.set_cell_data_func(render, cell_data_country, 0)
        self.listview.append_column(column)
        
        # Address column        
        column = gtk.TreeViewColumn(_("Address"))
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.add_attribute(render, "text", 1)
        self.listview.append_column(column)

        # Client column        
        column = gtk.TreeViewColumn(_("Client"))
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.add_attribute(render, "text", 2)
        self.listview.append_column(column)

        # Progress column        
        column = gtk.TreeViewColumn(_("Progress"))
        render = gtk.CellRendererProgress()
        column.pack_start(render, False)
        column.add_attribute(render, "text", 3)
        column.add_attribute(render, "value", 4)
        self.listview.append_column(column)
        
        # Down Speed column
        column = gtk.TreeViewColumn(_("Down Speed"))
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.set_cell_data_func(render, deluge.common.fspeed, 5)
        self.listview.append_column(column)        
        
        # Up Speed column
        column = gtk.TreeViewColumn(_("Up Speed"))
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.set_cell_data_func(render, deluge.common.fspeed, 6)
        self.listview.append_column(column)        

        self.listview.set_model(self.liststore)
        
    def update(self):
        pass
    
    def clear(self):
        pass
