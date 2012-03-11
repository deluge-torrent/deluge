#
# sidebar_menu.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
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

import deluge.component as component
import deluge.common
from deluge.log import LOG as log
from deluge.ui.client import client

NO_LABEL = "No Label"

#helpers:
def get_resource(filename):
    import pkg_resources
    import os
    return pkg_resources.resource_filename("label", os.path.join("data", filename))

#menu
class LabelSidebarMenu(object):
    def __init__(self):

        self.treeview  = component.get("FilterTreeView")
        self.menu = self.treeview.menu
        self.items = []

        #add items, in reverse order, because they are prepended.
        sep = gtk.SeparatorMenuItem()
        self.items.append(sep)
        self.menu.prepend(sep)
        self._add_item("options", _("Label _Options"), gtk.STOCK_PREFERENCES)
        self._add_item("remove", _("_Remove Label"), gtk.STOCK_REMOVE)
        self._add_item("add", _("_Add Label"), gtk.STOCK_ADD)

        self.menu.show_all()
        #dialogs:
        self.add_dialog = AddDialog()
        self.options_dialog = OptionsDialog()
        #hooks:
        self.menu.connect("show", self.on_show, None)


    def _add_item(self, id, label ,stock):
        """I hate glade.
        id is automatically-added as self.item_<id>
        """
        func  = getattr(self,"on_%s" %  id)
        item = gtk.ImageMenuItem(stock)
        item.get_children()[0].set_label(label)
        item.connect("activate", func)
        self.menu.prepend(item)
        setattr(self,"item_%s" %  id, item)
        self.items.append(item)
        return item

    def on_add(self, event=None):
        self.add_dialog.show()

    def on_remove(self, event=None):
        client.label.remove(self.treeview.value)

    def on_options (self, event=None):
        self.options_dialog.show(self.treeview.value)

    def on_show(self, widget=None, data=None):
        "No Label:disable options/del"
        log.debug("label-sidebar-popup:on-show")

        cat = self.treeview.cat
        label = self.treeview.value
        if cat == "label" or (cat == "cat" and label == "label"):
            #is a label : show  menu-items
            for item in self.items:
                item.show()
            #default items
            sensitive = ((label not in (NO_LABEL, None, "", "All")) and (cat != "cat"))
            for item  in self.items:
                item.set_sensitive(sensitive)

            #add is allways enabled.
            self.item_add.set_sensitive(True)
        else:
            #not a label -->hide everything.
            for item in self.items:
                item.hide()

    def unload(self):
        log.debug("disable01")
        for item in list(self.items):
            item.hide()
            item.destroy()
            log.debug("disable02")
        self.items = []




#dialogs:
class AddDialog(object):
    def __init__(self):
        pass

    def show(self):
        self.glade = gtk.glade.XML(get_resource("label_options.glade"))
        self.dialog = self.glade.get_widget("dlg_label_add")
        self.dialog.set_transient_for(component.get("MainWindow").window)

        self.glade.signal_autoconnect({
            "on_add_ok":self.on_ok,
            "on_add_cancel":self.on_cancel,
        })
        self.dialog.run()

    def on_ok(self, event=None):
        value = self.glade.get_widget("txt_add").get_text()
        client.label.add(value)
        self.dialog.destroy()

    def on_cancel(self, event=None):
        self.dialog.destroy()


class OptionsDialog(object):
    spin_ids = ["max_download_speed", "max_upload_speed", "stop_ratio"]
    spin_int_ids = ["max_upload_slots", "max_connections"]
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

    def show(self, label):
        self.label = label
        self.glade = gtk.glade.XML(get_resource("label_options.glade"))
        self.dialog = self.glade.get_widget("dlg_label_options")
        self.dialog.set_transient_for(component.get("MainWindow").window)
        self.glade.signal_autoconnect({
            "on_options_ok":self.on_ok,
            "on_options_cancel":self.on_cancel,
        })

        # Show the label name in the header label
        self.glade.get_widget("label_header").set_markup("<b>%s:</b> %s" % (_("Label Options"), self.label))

        for chk_id, group in  self.sensitive_groups:
            chk = self.glade.get_widget(chk_id)
            chk.connect("toggled",self.apply_sensitivity)

        client.label.get_options(self.label).addCallback(self.load_options)

        self.dialog.run()

    def load_options(self, options):
        log.debug(options.keys())

        for id in self.spin_ids + self.spin_int_ids:
            self.glade.get_widget(id).set_value(options[id])
        for id in self.chk_ids:
            self.glade.get_widget(id).set_active(bool(options[id]))

        if client.is_localhost():
            self.glade.get_widget("move_completed_path").set_filename(options["move_completed_path"])
            self.glade.get_widget("move_completed_path").show()
            self.glade.get_widget("move_completed_path_entry").hide()
        else:
            self.glade.get_widget("move_completed_path_entry").set_text(options["move_completed_path"])
            self.glade.get_widget("move_completed_path_entry").show()
            self.glade.get_widget("move_completed_path").hide()

        self.glade.get_widget("auto_add_trackers").get_buffer().set_text("\n".join(options["auto_add_trackers"]))

        self.apply_sensitivity()

    def on_ok(self, event=None):
        "save options.."
        options = {}

        for id in self.spin_ids:
            options[id] = self.glade.get_widget(id).get_value()
        for id in self.spin_int_ids:
            options[id] = self.glade.get_widget(id).get_value_as_int()
        for id in self.chk_ids:
            options[id] = self.glade.get_widget(id).get_active()

        if client.is_localhost():
            options["move_completed_path"] = self.glade.get_widget("move_completed_path").get_filename()
        else:
            options["move_completed_path"] = self.glade.get_widget("move_completed_path_entry").get_text()

        buff = self.glade.get_widget("auto_add_trackers").get_buffer() #sometimes I hate gtk...
        tracker_lst =  buff.get_text(buff.get_start_iter(), buff.get_end_iter()).strip().split("\n")
        options["auto_add_trackers"] = [x for x in tracker_lst if x] #filter out empty lines.

        log.debug(options)
        client.label.set_options(self.label, options)
        self.dialog.destroy()

    def apply_sensitivity(self, event=None):
        for chk_id , sensitive_list in self.sensitive_groups:
            chk = self.glade.get_widget(chk_id)
            sens = chk.get_active() and chk.get_property("sensitive")
            for widget_id in sensitive_list:
                self.glade.get_widget(widget_id).set_sensitive(sens)

    def on_cancel(self, event=None):
        self.dialog.destroy()
