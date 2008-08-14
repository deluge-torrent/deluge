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
        self.default_items = []
        self.all_items = []
        self._add_default_item("add", _("_Add Label"), gtk.STOCK_ADD)
        self._add_default_item("remove", _("_Remove Label"), gtk.STOCK_REMOVE)
        self._add_default_item("options", _("Label _Options"), gtk.STOCK_PREFERENCES)


        self.append(gtk.SeparatorMenuItem())
        self._add_all_item(None, _("_Select All"), gtk.STOCK_JUSTIFY_FILL)
        self._add_all_item("pause", None, gtk.STOCK_MEDIA_PAUSE)
        self._add_all_item("resume", _("R_esume"), gtk.STOCK_MEDIA_PLAY)

        #self._add_all_item("move", _("Move _Storage"), gtk.STOCK_SAVE_AS)
        #self._add_all_item("recheck", _("_Force Re-check"), gtk.STOCK_REDO)

        self.show_all()
        self.label = None
        #dialogs:
        self.add_dialog = AddDialog()
        self.options_dialog = OptionsDialog()

    def _add_default_item(self, id, label ,stock):
        """attaches callback to self.on_<id>"""
        func  = getattr(self,"on_%s" %  id)
        self.default_items.append(self._add_item(id, label , stock, func))

    def _add_all_item(self, id, label , stock):
        """1:selects all in torrentview
        2:executes menubar.on_menuitem_<id>_activate
        """
        def on_all_activate(self, event = None):
            component.get("TorrentView").treeview.get_selection().select_all()
            if id: #for select-all method.
                func = getattr(component.get("MenuBar"), "on_menuitem_%s_activate" % id)
                func(event)

        self.all_items.append(self._add_item(id, label , stock, on_all_activate))

    def _add_item(self, id, label ,stock, func):
        """I hate glade.
        id is automatically-added as self.item_<id>
        """
        item = gtk.ImageMenuItem(stock)
        if label:
            item.get_children()[0].set_label(label)
        item.connect("activate", func)
        self.append(item)
        setattr(self,"item_%s" %  id, item)
        return item

    def on_add(self, event=None):
        self.add_dialog.show(self.label)

    def on_remove(self, event=None):
        aclient.label_remove(None, self.label)

    def on_options (self, event=None):
        self.options_dialog.show(self.label, (200,250))

    def set_label(self, label, count):
        "No Label:disable options/del"
        self.label = label
        #self.count = count

        #None:only enable Add.

        #default items
        sensitive = (label not in (NO_LABEL, None))
        for item  in self.default_items:
            item.set_sensitive(sensitive)

        #"all" items:
        sensitive = (count > 0)
        for item  in self.all_items:
            item.set_sensitive(sensitive)


        #add is allways enabled.
        self.item_add.set_sensitive(True)


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
    spin_ids = ["max_download_speed", "max_upload_speed", "max_upload_slots", "max_connections", "stop_ratio"]
    chk_ids = ["apply_max", "apply_queue", "stop_at_ratio", "apply_queue", "remove_at_ratio",
        "apply_move_completed", "move_completed", "is_auto_managed", "auto_add"]

    #list of tuples, because order matters when nesting.
    sensitive_groups = [
        ("apply_max", ["max_download_speed", "max_upload_speed", "max_upload_slots", "max_connections"]),
        ("apply_queue", ["is_auto_managed", "stop_at_ratio"]),
        ("stop_at_ratio", ["remove_at_ratio", "stop_ratio"]), #nested
        ("apply_move_completed", ["move_completed"]),
        ("move_completed", ["move_completed_path"]), #nested
        ("auto_add", ["auto_add_trackers"])
    ]

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

        for chk_id, group in  self.sensitive_groups:
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

        self.glade.get_widget("auto_add_trackers").get_buffer().set_text("\n".join(options["auto_add_trackers"]))

        self.apply_sensitivity()

    def on_ok(self, event=None):
        "save options.."
        options = {}

        for id in self.spin_ids:
            options[id] = self.glade.get_widget(id).get_value()
        for id in self.chk_ids:
            options[id] = self.glade.get_widget(id).get_active()

        options["move_completed_path"] = self.glade.get_widget("move_completed_path").get_filename()
        buff = self.glade.get_widget("auto_add_trackers").get_buffer() #sometimes I hate gtk...
        tracker_lst =  buff.get_text(buff.get_start_iter(), buff.get_end_iter()).strip().split("\n")
        options["auto_add_trackers"] = [x for x in tracker_lst if x] #filter out empty lines.

        log.debug(options)
        aclient.label_set_options(None, self.label, options)
        self.dialog.destroy()

    def apply_sensitivity(self, event=None):
        for chk_id , sensitive_list in self.sensitive_groups:
            chk = self.glade.get_widget(chk_id)
            sens = chk.get_active() and chk.get_property("sensitive")
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
        self.label_view = gtk.TreeView()

        # Create the liststore
        #cat,value,count , pixmap , visible
        self.treestore = gtk.TreeStore(str, str, int, gtk.gdk.Pixbuf, bool)

        #add Cat nodes:
        self.cat_nodes = {}
        self.cat_nodes["state"] = self.treestore.append(None, ["cat", "State", 0, None, False])
        self.cat_nodes["tracker"] = self.treestore.append(None, ["cat","Tracker", 0,None, False])
        self.cat_nodes["label"] = self.treestore.append(None, ["cat", "Label", 0, None, False])

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
        self.label_view.set_show_expanders(False)
        self.label_view.set_headers_visible(False)

        self.label_view.set_model(self.treestore)

        self.label_view.get_selection().connect("changed",
                                    self.on_selection_changed)

        self.create_model_filter()

        #init.....
        self._start()
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
            elif (cat == "label" and value == NO_LABEL):
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
            count = self.model_filter.get_value(row, 2)

            #log.debug("right-click->cat='%s',value='%s'", cat ,value)

            if cat == "label":
                self.show_label_menu(value, count, event)
            elif (cat == "cat" and value == "Label"): #add button on root node.
                self.show_label_menu(None, 0, event)



    def show_label_menu(self, label, count, event):
        self.label_menu.set_label(label, count)
        self.label_menu.popup(None, None, None, event.button, event.time)

