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

NO_LABEL = "No Label"

#helpers:
def get_resource(filename):
    import pkg_resources
    import os
    return pkg_resources.resource_filename("label", os.path.join("data", filename))

#menu
class LabelMenu(gtk.Menu):
    def __init__(self):
        gtk.Menu.__init__(self)
        self._add_item("add", _("_Add"), gtk.STOCK_ADD)
        self._add_item("options", _("_Options") ,gtk.STOCK_PREFERENCES)
        self._add_item("remove", _("Remove"), gtk.STOCK_REMOVE)
        self.show_all()
        self.label = None

        #dialogs:
        self.add_dialog = AddDialog()
        self.options_dialog = OptionsDialog()

    def _add_item(self, id, label , stock):
        "add a menu item, some magic here because i hate glade."
        method = getattr(self,"on_%s" %  id)
        item = gtk.ImageMenuItem(stock)
        item.connect("activate", method)
        self.append(item)
        setattr(self,"item_%s" %  id, item)

    def on_add(self, event=None):
        self.add_dialog.show(self.label)

    def on_remove(self, event=None):
        aclient.label_remove(None, self.label)

    def on_options (self, event=None):
        self.options_dialog.show(self.label, (200,250))

    def set_label(self,label):
        "No Label:disable options/del"
        self.label = label
        sensitive = (label != NO_LABEL)
        self.item_options.set_sensitive(sensitive)
        self.item_remove.set_sensitive(sensitive)

#dialogs:
class AddDialog(object):
    def __init__(self):
        pass

    def show(self, label ):
        self.glade = gtk.glade.XML(get_resource("label_options.glade"))
        self.dialog = self.glade.get_widget("dlg_label_add")
        self.glade.signal_autoconnect({
            "on_add_ok":self.on_ok,
            "on_add_cancel":self.on_cancel,
        })
        self.dialog.run()

    def on_ok(self, event=None):
        value = self.glade.get_widget("txt_add").get_text()
        aclient.label_add(None, value)
        self.dialog.destroy()

    def on_cancel(self, event=None):
        self.dialog.destroy()


class OptionsDialog(object):
    spin_ids = ["max_download_speed","max_upload_speed","max_upload_slots","max_connections","stop_ratio"]
    chk_ids = ["apply_max","apply_queue","stop_at_ratio","apply_queue","remove_at_ratio","move_completed","is_auto_managed"]
    sensitive_groups = { #keys must be checkboxes , value-list is to be enabled on checked.
        "apply_max": ["max_download_speed","max_upload_speed","max_upload_slots","max_connections"],
        "apply_queue":["is_auto_managed","remove_at_ratio","stop_at_ratio","stop_ratio"],
        #"stop_at_ratio":["stop_at_ratio","remove_at_ratio"], #nested from apply_queue, will probably cause bugs.
        "move_completed":["move_completed_path"]
    }

    def __init__(self):
        pass

    def show(self, label , position):
        self.label = label
        self.glade = gtk.glade.XML(get_resource("label_options.glade"))
        self.dialog = self.glade.get_widget("dlg_label_options")
        self.glade.signal_autoconnect({
            "on_options_ok":self.on_ok,
            "on_options_cancel":self.on_cancel,
        })

        for chk_id in  self.sensitive_groups:
            log.debug(chk_id)
            chk = self.glade.get_widget(chk_id)
            chk.connect("toggled",self.apply_sensitivity)

        aclient.label_get_options(self.load_options, self.label)
        self.dialog.move(*position)
        self.dialog.run()

    def load_options(self, options):
        log.debug(options.keys())

        for id in self.spin_ids:
            self.glade.get_widget(id).set_value(options[id])
        for id in self.chk_ids:
            self.glade.get_widget(id).set_active(bool(options[id]))
        self.glade.get_widget("move_completed_path").set_filename(options["move_completed_path"])

        self.apply_sensitivity()

    def on_ok(self, event=None):
        "save options.."
        options = {}

        for id in self.spin_ids:
            options[id] = self.glade.get_widget(id).get_value()
        for id in self.chk_ids:
            options[id] = self.glade.get_widget(id).get_active()
        options["move_completed_path"] = self.glade.get_widget("move_completed_path").get_filename()


        aclient.label_set_options(None, self.label, options)
        self.dialog.destroy()

    def apply_sensitivity(self, event=None):
        log.debug("apply-sensitivity")
        for chk_id , sensitive_list in self.sensitive_groups.iteritems():
            sens = self.glade.get_widget(chk_id).get_active()
            for widget_id in sensitive_list:
                self.glade.get_widget(widget_id).set_sensitive(sens)





    def on_cancel(self, event=None):
        self.dialog.destroy()

#sidebar-treeview
class LabelSideBar(component.Component):
    def __init__(self):
        component.Component.__init__(self, "LabelSideBar", interval=2000)
        self.window = component.get("MainWindow")
        glade = self.window.main_glade
        self.hpaned = glade.get_widget("hpaned")
        self.scrolled = glade.get_widget("scrolledwindow_sidebar")
        self.is_visible = True
        self.filters = {}
        self.first_expand = True
        self.label_view = gtk.TreeView()

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
        self.label_view.set_show_expanders(True)
        self.label_view.set_level_indentation(-35)
        self.label_view.set_headers_visible(False)

        self.label_view.set_model(self.treestore)

        self.label_view.get_selection().connect("changed",
                                    self.on_selection_changed)

        # Select the 'All' label on init
        #self.label_view.get_selection().select_iter(
        #    self.treestore.get_iter_first())

        self.create_model_filter()
        #init.....
        self._start()
        self.label_view.expand_all()
        self.hpaned.set_position(170)

        self.label_view.connect("button-press-event", self.on_button_press_event)

        self.label_menu = LabelMenu()


    def load(self):
        sidebar = component.get("SideBar")
        sidebar.add_tab(self.label_view, "filters", _("Filters"))

    def unload(self):
        log.debug("unload..")
        sidebar = component.get("SideBar")
        sidebar.remove_tab("filters")
        log.debug("unload-end")


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

        # kind of a hack.
        if self.first_expand:
            self.label_view.expand_all()
            self.first_expand = False

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

        if cat == "cat":
            txt = value
            col = gtk.gdk.color_parse('#EEEEEE')
            cell.set_property("ypad",1)
        else:
            txt = "%s (%s)"  % (value, count)
            col = gtk.gdk.color_parse('white')
            cell.set_property("ypad",1)

        cell.set_property('text', txt)
        cell.set_property("cell-background-gdk",col)
        self.renderpix.set_property("cell-background-gdk",col)

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
            if not row:
                log.debug("nothing selected")
                return

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
            elif (cat == "cat" and value == NO_LABEL):
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


    ### Callbacks ###
    def on_button_press_event(self, widget, event):
        """This is a callback for showing the right-click context menu."""

        # We only care about right-clicks
        if event.button == 3:
            x, y = event.get_coords()
            path = self.label_view.get_path_at_pos(int(x), int(y))
            if not path:
                return
            row = self.model_filter.get_iter(path[0])
            cat    = self.model_filter.get_value(row, 0)
            value = self.model_filter.get_value(row, 1)

            log.debug("right-click->cat='%s',value='%s'", cat ,value)

            if cat == "label":
                self.show_label_menu(value, event)
            elif (cat == "cat" and value == "Label"):
                self.show_label_menu(NO_LABEL, event)

    def show_label_menu(self, label, event):
        self.label_menu.set_label(label)
        self.label_menu.popup(None, None, None, event.button, event.time)

