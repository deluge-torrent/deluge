#
# filtertreeview.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
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
# 	Boston, MA  02110-1301, USA.
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
#
#


import gtk
import gtk.glade
import pkg_resources
import warnings
from gobject import GError

import deluge.component as component
import deluge.common
from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.configmanager import ConfigManager

STATE_PIX = {
    "All": "all",
    "Downloading": "downloading",
    "Seeding": "seeding",
    "Paused": "inactive",
    "Checking": "checking",
    "Queued": "queued",
    "Error": "alert",
    "Active": "active"
    }

TRACKER_PIX = {
    "All": "tracker_all",
    "Error": "tracker_warning",
}

def _(message): return message

TRANSLATE = {
    "state": _("States"),
    "tracker_host": _("Trackers"),
    "label": _("Labels"),
    "All": _("All"),
    "Downloading": _("Downloading"),
    "Seeding": _("Seeding"),
    "Paused": _("Paused"),
    "Checking": _("Checking"),
    "Queued": _("Queued"),
    "Error": _("Error"),
    "Active": _("Active"),
    "none": _("None"),
    "no_label": _("No Label"),
}

del _

def _t(text):
    if text in TRANSLATE:
        text = TRANSLATE[text]
    return _(text)

FILTER_COLUMN = 5

#sidebar-treeview
class FilterTreeView(component.Component):
    def __init__(self):
        component.Component.__init__(self, "FilterTreeView", interval=2)
        self.window = component.get("MainWindow")
        glade = self.window.main_glade
        self.hpaned = glade.get_widget("hpaned")
        self.scrolled = glade.get_widget("scrolledwindow_sidebar")
        self.sidebar = component.get("SideBar")
        self.config = ConfigManager("gtkui.conf")
        self.tracker_icons = component.get("TrackerIcons")

        self.label_view = gtk.TreeView()
        self.sidebar.add_tab(self.label_view, "filters", "Filters")

        #set filter to all when hidden:
        self.sidebar.notebook.connect("hide", self._on_hide)

        #menu
        glade_menu = gtk.glade.XML(pkg_resources.resource_filename("deluge.ui.gtkui",
            "glade/filtertree_menu.glade"))
        self.menu = glade_menu.get_widget("filtertree_menu")
        glade_menu.signal_autoconnect({
            "select_all": self.on_select_all,
            "pause_all": self.on_pause_all,
            "resume_all": self.on_resume_all
        })

        self.default_menu_items = self.menu.get_children()

        # Create the liststore
        #cat, value, label, count, pixmap, visible
        self.treestore = gtk.TreeStore(str, str, str, int, gtk.gdk.Pixbuf, bool)

        # Create the column
        column = gtk.TreeViewColumn("Filters")
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        render = gtk.CellRendererPixbuf()
        self.renderpix = render
        column.pack_start(render, expand=False)
        column.add_attribute(render, 'pixbuf', 4)
        render = gtk.CellRendererText()
        column.pack_start(render, expand=False)
        column.set_cell_data_func(render, self.render_cell_data,None)

        self.label_view.append_column(column)

        #style:
        self.label_view.set_show_expanders(True)
        self.label_view.set_headers_visible(False)
        self.label_view.set_level_indentation(-35)
        # Force the theme to use an expander-size of 15 so that we don't cut out
        # entries due to our indentation hack.
        gtk.rc_parse_string('style "treeview-style" { GtkTreeView::expander-size = 15 } class "GtkTreeView" style "treeview-style"')

        self.label_view.set_model(self.treestore)
        self.label_view.get_selection().connect("changed", self.on_selection_changed)
        self.create_model_filter()

        #init.....
        self.label_view.connect("button-press-event", self.on_button_press_event)

        #colors using current theme.
        style = self.window.window.get_style()
        self.colour_background = style.bg[gtk.STATE_NORMAL]
        self.colour_foreground = style.fg[gtk.STATE_NORMAL]

    def start(self):
        #add Cat nodes:
        self.cat_nodes = {}
        self.filters = {}

        #initial order of state filter:
        self.cat_nodes["state"] = self.treestore.append(None, ["cat", "state", _t("state"), 0, None, False])
        self.update_row("state", "All" , 0)
        self.update_row("state", "Downloading" , 0)
        self.update_row("state", "Seeding" , 0)
        self.update_row("state", "Active" , 0)
        self.update_row("state", "Paused" , 0)
        self.update_row("state", "Queued" , 0)

        self.cat_nodes["tracker_host"] = self.treestore.append(None, ["cat", "tracker_host", _t("tracker_host"), 0, None, False])
        self.update_row("tracker_host", "All" , 0)
        self.update_row("tracker_host", "Error" , 0)
        self.update_row("tracker_host", "" , 0)

        # We set to this expand the rows on start-up
        self.expand_rows = True

        self.selected_path = None

    def stop(self):
        self.treestore.clear()

    def create_model_filter(self):
        self.model_filter = self.treestore.filter_new()
        self.model_filter.set_visible_column(FILTER_COLUMN)
        self.label_view.set_model(self.model_filter)

    def cb_update_filter_tree(self, filter_items):
        #create missing cat_nodes
        for cat in filter_items:
            if not cat in self.cat_nodes:
                self.cat_nodes[cat] = self.treestore.append(None, ["cat", cat, _t(cat), 0, None, False])

        #update rows
        visible_filters = []
        for cat,filters in filter_items.iteritems():
            for value, count in filters:
                self.update_row(cat, value , count)
                visible_filters.append((cat, value))

        # hide root-categories not returned by core-part of the plugin.
        for cat in self.cat_nodes:
            if cat in filter_items:
                self.treestore.set_value(self.cat_nodes[cat], FILTER_COLUMN, True)
            else:
                self.treestore.set_value(self.cat_nodes[cat], FILTER_COLUMN, False)

        # hide items not returned by core-plugin.
        for f in self.filters:
            if not f in visible_filters:
                self.treestore.set_value(self.filters[f], FILTER_COLUMN, False)

        if self.expand_rows:
            self.label_view.expand_all()
            self.expand_rows = False

        if not self.selected_path:
            self.select_default_filter()

    def update_row(self, cat, value , count):
        def on_get_icon(icon):
            if icon:
                self.set_row_image(cat, value, icon.get_filename())

        if (cat, value) in self.filters:
            row = self.filters[(cat, value)]
            self.treestore.set_value(row, 3, count)
        else:
            pix = self.get_pixmap(cat, value)
            label = value

            if label == "":
                if cat == "tracker_host":
                    label = _t("none")
                elif cat == "label":
                    label = _t("no_label")
            elif cat in ["state", "tracker_host", "label"]:
                label = _t(value)

            row = self.treestore.append(self.cat_nodes[cat],[cat, value, label, count , pix, True])
            self.filters[(cat, value)] = row

            if cat == "tracker_host" and value not in ("All", "Error") and value:
                d = self.tracker_icons.get(value)
                d.addCallback(on_get_icon)

        self.treestore.set_value(row, FILTER_COLUMN, True)
        return row

    def render_cell_data(self, column, cell, model, row, data):
        "cell renderer"
        cat = model.get_value(row, 0)
        value = model.get_value(row, 1)
        label = model.get_value(row, 2)
        count = model.get_value(row, 3)

        #Supress Warning: g_object_set_qdata: assertion `G_IS_OBJECT (object)' failed
        original_filters = warnings.filters[:]
        warnings.simplefilter("ignore")
        try:
            pix = model.get_value(row, 4)
        finally:
            warnings.filters = original_filters

        if pix:
            self.renderpix.set_property("visible", True)
        else:
            self.renderpix.set_property("visible", False)

        if cat == "cat":
            txt = label
            cell.set_property("cell-background-gdk", self.colour_background)
            cell.set_property("foreground-gdk", self.colour_foreground)
        else:
            txt = "%s (%s)"  % (label, count)
            cell.set_property("cell-background", None)
            cell.set_property("foreground", None)

        cell.set_property('text', txt)

    def get_pixmap(self, cat, value):
        pix = None
        if cat == "state":
            pix = STATE_PIX.get(value, None)
        elif cat == "tracker_host":
            pix = TRACKER_PIX.get(value, None)

        if pix:
            try:
                return gtk.gdk.pixbuf_new_from_file(deluge.common.get_pixmap("%s16.png" % pix))
            except GError, e:
                log.warning(e)
        return self.get_transparent_pix(16, 16)

    def get_transparent_pix(self,  width, height):
        pix = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, width, height)
        pix.fill(0x0000000)
        return pix

    def set_row_image(self, cat, value, filename):
        pix = None
        try: #assume we could get trashed images here..
            pix = gtk.gdk.pixbuf_new_from_file_at_size(filename, 16, 16)
        except Exception, e:
            log.debug(e)

        if not pix:
            pix = self.get_transparent_pix(16, 16)
        row = self.filters[(cat, value)]
        self.treestore.set_value(row, 4, pix)
        return False


    def on_selection_changed(self, selection):
        try:
            (model, row) = self.label_view.get_selection().get_selected()
            if not row:
                log.debug("nothing selected")
                return

            cat = model.get_value(row, 0)
            value = model.get_value(row, 1)

            filter_dict = {cat: [value]}
            if value == "All" or cat == "cat":
                filter_dict = {}

            component.get("TorrentView").set_filter(filter_dict)

            self.selected_path = model.get_path(row)

        except Exception, e:
            log.debug(e)
            # paths is likely None .. so lets return None
            return None

    def update(self):
        try:
            hide_cat = []
            if not self.config["sidebar_show_trackers"]:
                hide_cat = ["tracker_host"]
            client.core.get_filter_tree(self.config["sidebar_show_zero"], hide_cat).addCallback(self.cb_update_filter_tree)
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
                if self.label_view.row_expanded(path):
                    self.label_view.collapse_row(path)
                else:
                    self.label_view.expand_row(path, False)
                    if not self.selected_path:
                        self.select_default_filter()
                    else:
                        self.label_view.get_selection().select_path(self.selected_path)
                return True

        elif event.button == 3:
            #assign current cat, value to self:
            x, y = event.get_coords()
            path = self.label_view.get_path_at_pos(int(x), int(y))
            if not path:
                return
            row = self.model_filter.get_iter(path[0])
            self.cat = self.model_filter.get_value(row, 0)
            self.value = self.model_filter.get_value(row, 1)
            self.count = self.model_filter.get_value(row, 3)

            #Show the pop-up menu
            self.set_menu_sensitivity()
            self.menu.hide()
            self.menu.popup(None, None, None, event.button, event.time)
            self.menu.show()

            if cat == "cat":
                # Do not select the row
                return True

    def set_menu_sensitivity(self):
        #select-all/pause/resume
        sensitive = (self.cat != "cat" and self.count <> 0)
        for item in self.default_menu_items:
            item.set_sensitive(sensitive)

    def select_all(self):
        "for use in popup menu"
        component.get("TorrentView").treeview.get_selection().select_all()

    def on_select_all(self, event):
        self.select_all()

    def on_pause_all(self, event):
        self.select_all()
        func = getattr(component.get("MenuBar"), "on_menuitem_%s_activate" % "pause")
        func(event)

    def on_resume_all(self, event):
        self.select_all()
        func = getattr(component.get("MenuBar"), "on_menuitem_%s_activate" % "resume")
        func(event)

    def _on_hide(self, *args):
        self.select_default_filter()

    def select_default_filter(self):
        row = self.filters[("state", "All")]
        path = self.treestore.get_path(row)
        self.label_view.get_selection().select_path(path)
