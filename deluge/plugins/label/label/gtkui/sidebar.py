#
# gtk_sidebar.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
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
from deluge.ui.client import aclient

STATE_PIX = {
    "Downloading":"downloading",
    "Seeding":"seeding",
    "Paused":"inactive",
    "Checking":"checking",
    "Queued":"queued",
    "Error":"alert"
    }


class LabelSideBar(component.Component):
    def __init__(self):
        component.Component.__init__(self, "LabelSideBar", interval=2000)
        self.window = component.get("MainWindow")
        glade = self.window.main_glade
        self.label_view = glade.get_widget("label_view")
        self.hpaned = glade.get_widget("hpaned")
        self.scrolled = glade.get_widget("scrolledwindow_sidebar")
        self.is_visible = True
        self.filters = {}

        # Create the liststore
        #cat,value,count , pixmap , visible
        self.treestore = gtk.TreeStore(str, str, int, gtk.gdk.Pixbuf, bool)

        #add Cat nodes:
        self.cat_nodes = {}
        self.cat_nodes["state"] = self.treestore.append(None, ["cat", "State", 0, None, True])
        self.cat_nodes["tracker"] = self.treestore.append(None, ["cat","Tracker", 0,None, True])
        self.cat_nodes["label"] = self.treestore.append(None, ["cat", "Label", 0, None, True])

        #default node:
        self.filters[("state", "All")] = self.treestore.append(self.cat_nodes["state"],
            ["state", "All", 0, gtk.gdk.pixbuf_new_from_file(deluge.common.get_pixmap("dht16.png")), True])


        #remove all old columns:
        for c in self.label_view.get_columns():
            self.label_view.remove_column(c)

        # Create the column
        column = gtk.TreeViewColumn(_("Filters"))
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        render = gtk.CellRendererPixbuf()
        column.pack_start(render, expand=False)
        column.add_attribute(render, 'pixbuf', 3)
        render = gtk.CellRendererText()
        column.pack_start(render, expand=False)
        column.set_cell_data_func(render, self.render_cell_data,None)

        self.label_view.append_column(column)
        self.label_view.set_show_expanders(False)

        self.label_view.set_model(self.treestore)

        self.label_view.get_selection().connect("changed",
                                    self.on_selection_changed)

        # Select the 'All' label on init
        self.label_view.get_selection().select_iter(
            self.treestore.get_iter_first())

        self.create_model_filter()
        #init.....
        self._start()
        self.label_view.expand_all()
        self.hpaned.set_position(170)

    def load(self):
        self.label_view.set_model(self.model_filter)

    def unload(self):
        #hacks!
        old_sidebar = component.get("SideBar")
        del old_sidebar
        new_sidebar = deluge.ui.gtkui.sidebar.SideBar()


    def create_model_filter(self):
        self.model_filter = self.treestore.filter_new()
        self.model_filter.set_visible_column(4)
        self.label_view.set_model(self.model_filter)

    def cb_update_filter_items(self, filter_items):
        visible_filters = []
        for cat,filters in filter_items.iteritems():
            for value, count in filters:
                self.update_row(cat, value , count)
                visible_filters.append((cat, value))

        for f in self.filters:
            if not f in visible_filters:
                self.treestore.set_value(self.filters[f], 4, False)

        self.label_view.expand_all()

    def update_row(self, cat, value , count):
        if (cat, value) in self.filters:
            row = self.filters[(cat, value)]
            self.treestore.set_value(row, 2, count)
        else:
            pix = self.get_pixmap(cat, value)
            row = self.treestore.append(self.cat_nodes[cat],[cat, value, count , pix, True])
            self.filters[(cat, value)] = row
        self.treestore.set_value(row, 4, True)



    def render_cell_data(self, column, cell, model, row, data):
        "cell renderer"
        cat    = model.get_value(row, 0)
        value = model.get_value(row, 1)
        count = model.get_value(row, 2)
        if cat == "cat":
            txt = value
            col = gtk.gdk.color_parse('gray')
        else:
            txt = "%s (%s)"  % (value, count)
            col = gtk.gdk.color_parse('white')
        cell.set_property('text', txt)
        cell.set_property("cell-background-gdk",col)

    def get_pixmap(self, cat, value):
        if cat == "state":
            pix = STATE_PIX.get(value, "dht")
            return gtk.gdk.pixbuf_new_from_file(deluge.common.get_pixmap("%s16.png" % pix))
        return None


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

            cat    = model.get_value(row, 0)
            value = model.get_value(row, 1)

            #gtk-ui has it's own filtering logic on status-fields.
            #not using the label-backend for filtering. (for now)
            #just a few simple hacks to translate label-filters to gtk-filters.
            if cat == "tracker":
                cat = "tracker_host"

            filter = (cat, value)
            if value == "All" or cat == "cat":
                filter = (None, None)
            elif (cat == "label" and value == "No Label"):
                 filter = ("label","")

            component.get("TorrentView").set_filter(*filter)

        except Exception, e:
            log.debug(e)
            # paths is likely None .. so lets return None
            return None

    def update(self):
        try:
            aclient.label_filter_items(self.cb_update_filter_items)
        except Exception, e:
            log.debug(e)


