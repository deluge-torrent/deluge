#
# sidebar.py
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

import gtk
import gtk.glade

import deluge.component as component
import deluge.common
from deluge.log import LOG as log

class SideBar(component.Component):
    def __init__(self):
        component.Component.__init__(self, "SideBar")
        self.window = component.get("MainWindow")
        glade = self.window.main_glade
        self.label_view = glade.get_widget("label_view")
        self.hpaned = glade.get_widget("hpaned")
        self.scrolled = glade.get_widget("scrolledwindow_sidebar")
        self.is_visible = True

        # Create the liststore
        self.liststore = gtk.ListStore(str, gtk.gdk.Pixbuf)
        self.liststore.append([_("All"), None])
        self.liststore.append([_("Downloading"), 
            gtk.gdk.pixbuf_new_from_file(
                deluge.common.get_pixmap("downloading16.png"))])
        self.liststore.append([_("Seeding"),
            gtk.gdk.pixbuf_new_from_file(
                deluge.common.get_pixmap("seeding16.png"))])
        self.liststore.append([_("Paused"),
            gtk.gdk.pixbuf_new_from_file(
                deluge.common.get_pixmap("inactive16.png"))])
        # Create the column
        column = gtk.TreeViewColumn(_("Labels"))
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        render = gtk.CellRendererPixbuf()
        column.pack_start(render, expand=False)
        column.add_attribute(render, 'pixbuf', 1)
        render = gtk.CellRendererText()
        column.pack_start(render, expand=True)
        column.add_attribute(render, 'text', 0)        
        self.label_view.append_column(column)
        
        self.label_view.set_model(self.liststore)
        
        self.label_view.get_selection().connect("changed", 
                                    self.on_selection_changed)
        
        # Select the 'All' label on init
        self.label_view.get_selection().select_iter(
            self.liststore.get_iter_first())
        
    def visible(self, visible):
        if visible:
            self.scrolled.show()
        else:
            self.scrolled.hide()
            self.hpaned.set_position(-1)
        
        self.is_visible = visible

    def on_selection_changed(self, selection):
        try:
            (model, row) = self.label_view.get_selection().get_selected()
        except Exception, e:
            log.debug(e)
            # paths is likely None .. so lets return None
            return None
        
        value = model.get_value(row, 0)
        if value == "All":
            component.get("TorrentView").set_filter(None, None)
        if value == "Downloading":
            component.get("TorrentView").set_filter("state", 
                deluge.common.TORRENT_STATE.index("Downloading"))
           
        if value == "Seeding":
            component.get("TorrentView").set_filter("state", 
                deluge.common.TORRENT_STATE.index("Seeding"))

        if value == "Paused":
            component.get("TorrentView").set_filter("state", 
                deluge.common.TORRENT_STATE.index("Paused"))

