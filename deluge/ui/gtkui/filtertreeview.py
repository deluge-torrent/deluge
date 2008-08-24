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

#sidebar-treeview
class FilterTreeView(component.Component):
    def __init__(self):
        component.Component.__init__(self, "FilterTreeView", interval=2000)
        self.window = component.get("MainWindow")
        glade = self.window.main_glade
        self.hpaned = glade.get_widget("hpaned")
        self.scrolled = glade.get_widget("scrolledwindow_sidebar")
        self.sidebar = component.get("SideBar")
        self.is_visible = True
        self.filters = {}
        self.label_view = gtk.TreeView()
        self.sidebar.add_tab(self.label_view, "filters", _("Filters"))


        # Create the liststore
        #cat,value,count , pixmap , visible
        self.treestore = gtk.TreeStore(str, str, int, gtk.gdk.Pixbuf, bool)

        #add Cat nodes:
        self.cat_nodes = {}

        # Create the column
        column = gtk.TreeViewColumn(_("Filters"))
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        render = gtk.CellRendererPixbuf()
        self.renderpix = render
        column.pack_start(render, expand=False)
        column.add_attribute(render, 'pixbuf', 3)
        render = gtk.CellRendererText()
        column.pack_start(render, expand=False)
        column.set_cell_data_func(render, self.render_cell_data,None)

        self.label_view.append_column(column)

        #style:
        self.label_view.set_show_expanders(False)
        self.label_view.set_headers_visible(False)

        self.label_view.set_model(self.treestore)
        self.label_view.get_selection().connect("changed", self.on_selection_changed)
        self.create_model_filter()

        #init.....
        self._start()
        self.hpaned.set_position(170)
        self.label_view.connect("button-press-event", self.on_button_press_event)

    def create_model_filter(self):
        self.model_filter = self.treestore.filter_new()
        self.model_filter.set_visible_column(4)
        self.label_view.set_model(self.model_filter)

    def cb_update_filter_tree(self, filter_items):
        #create missing cat_nodes
        for cat in filter_items:
            if not cat in self.cat_nodes:
                self.cat_nodes[cat] = self.treestore.append(None, ["cat", _(cat), 0, None, False])

        #update rows
        visible_filters = []
        for cat,filters in filter_items.iteritems():
            for value, count in filters:
                self.update_row(cat, value , count)
                visible_filters.append((cat, value))

        # hide root-categories not returned by core-part of the plugin.
        for cat in self.cat_nodes:
            if cat in filter_items:
                self.treestore.set_value(self.cat_nodes[cat], 4, True)
            else:
                self.treestore.set_value(self.cat_nodes[cat], 4, False)

        # hide items not returned by core-plugin.
        for f in self.filters:
            if not f in visible_filters:
                self.treestore.set_value(self.filters[f], 4, False)

        # obsolete?
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

        if cat == "state":
            self.renderpix.set_property("visible", True)
        else:
            self.renderpix.set_property("visible", False)

        cell.set_property('editable', False)
        if cat == "cat":
            txt = value
            col = gtk.gdk.color_parse('#EEEEEE')
        else:
            txt = "%s (%s)"  % (value, count)
            col = gtk.gdk.color_parse('white')

        cell.set_property('text', txt)
        cell.set_property("cell-background-gdk",col)
        self.renderpix.set_property("cell-background-gdk",col)

    def get_pixmap(self, cat, value):
        if cat == "state":
            pix = STATE_PIX.get(value, "dht")
            return gtk.gdk.pixbuf_new_from_file(deluge.common.get_pixmap("%s16.png" % pix))
        return None

    def on_selection_changed(self, selection):
        try:
            (model, row) = self.label_view.get_selection().get_selected()
            if not row:
                log.debug("nothing selected")
                return

            cat    = model.get_value(row, 0)
            value = model.get_value(row, 1)

            filter_dict = {cat: [value]}
            if value == "All" or cat == "cat":
                filter_dict = {}

            component.get("TorrentView").set_filter(filter_dict)

        except Exception, e:
            log.debug(e)
            # paths is likely None .. so lets return None
            return None

    def update(self):
        try:
            aclient.get_filter_tree(self.cb_update_filter_tree)
        except Exception, e:
            log.debug(e)


    ### Callbacks ###
    def on_button_press_event(self, widget, event):
        """This is a callback for showing the right-click context menu.
        NOT YET!
        """
        x, y = event.get_coords()
        path = self.label_view.get_path_at_pos(int(x), int(y))
        if not path:
            return
        path = path[0]
        cat = self.model_filter[path][0]
        
        if event.button == 1:
            # Prevent selecting a category label
            if cat == "cat":
                return True
        
        elif event.button == 3:
            if cat == "cat":
                # XXX: Show the pop-up menu
                # Do not select the row
                return True
        """
        
        # We only care about right-clicks
        if event.button == 3:
            x, y = event.get_coords()
            path = self.label_view.get_path_at_pos(int(x), int(y))
            if not path:
                return
            row = self.model_filter.get_iter(path[0])
            cat    = self.model_filter.get_value(row, 0)
            value = self.model_filter.get_value(row, 1)
            count = self.model_filter.get_value(row, 2)

            #log.debug("right-click->cat='%s',value='%s'", cat ,value)

            if cat == "label":
                self.show_label_menu(value, count, event)
            elif (cat == "cat" and value == "Label"): #add button on root node.
                self.show_label_menu(None, 0, event)
        """
