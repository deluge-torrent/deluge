#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# Deluge is free software.
#
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
import os
import pkg_resources    # access plugin egg
import deluge.component as component
import deluge.common
from deluge.log import LOG as log
from deluge.ui.client import aclient



class LabelConfig(object):
    def __init__(self, plugin):
        self.plugin = plugin
        self.labels = []

    def load(self):
        #self.glade = gtk.glade.XML(self.get_resource("label_pref.glade"))
        log.debug('Adding Label Preferences page')



        self.glade = gtk.glade.XML(self.get_resource("label_pref.glade"))
        self.prefs_box = self.glade.get_widget("label_prefs_box")
        self.label_view = self.glade.get_widget("label_view")
        self.txt_add = self.glade.get_widget("txt_add")
        self.btn_add = self.glade.get_widget("btn_add")
        self.btn_remove = self.glade.get_widget("btn_remove")
        self.label_view = self.glade.get_widget("label_view")


        self.btn_remove.connect("clicked", self.on_remove, None)
        self.btn_add.connect("clicked", self.on_add, None)

        self.build_label_view()

        self.plugin.add_preferences_page("Label", self.glade.get_widget("label_prefs_box"))
        self.plugin.register_hook("on_show_prefs", self.load_settings)
        self.plugin.register_hook("on_apply_prefs", self.on_apply_prefs)

        self.glade.get_widget("chk_move_completed").connect("clicked",self.on_chk_move_changed)
        self.glade.get_widget("apply_max").connect("clicked",self.on_apply_max_changed)
        self.glade.get_widget("btn_save").connect("clicked",self.on_save_label)
        self.glade.get_widget("btn_apply").connect("clicked",self.on_apply_label)


        self.load_settings()

    def unload(self):
        self.plugin.remove_preferences_page("Label")
        self.plugin.deregister_hook("on_show_prefs", self.load_settings)

    def get_resource(self, filename):
        return pkg_resources.resource_filename("label", os.path.join("data", filename))

    def load_settings(self ,widget = None , data = None):
        aclient.label_get_labels(self.cb_update_labels)
        aclient.label_get_global_options(self.cb_global_options)

    def cb_global_options(self, data):
        self.glade.get_widget("hide_zero_hits").set_active(data["hide_zero_hits"])

    def cb_update_labels(self, labels):
        log.debug("update labels")
        self.labels = labels
        self.label_store.clear()
        for label in labels:
            self.label_store.append([label])
        if labels:
            self.label_view.get_selection().select_iter(self.label_store.get_iter_first())

    def cb_label_options(self, data):
        for key in ["max_download_speed", "max_upload_speed", "max_connections" ,"max_upload_slots"]:
            spin = self.glade.get_widget(key)
            spin.set_value(data[key])

        self.glade.get_widget("apply_max").set_active(data["apply_max"])
        self.glade.get_widget("chk_move_completed").set_active(bool(data["move_completed_to"]))
        self.glade.get_widget("move_completed_to").set_filename(data["move_completed_to"] or  "")

        self.on_apply_max_changed()
        self.on_chk_move_changed()

    def on_apply_prefs(self):
        options = {"hide_zero_hits":self.glade.get_widget("hide_zero_hits").get_active()}
        aclient.label_set_global_options(None, options)

    def on_chk_move_changed(self, data = None):
        self.glade.get_widget("move_completed_to").set_sensitive(
            self.glade.get_widget("chk_move_completed").get_active())

    def on_apply_max_changed(self, data = None):
        active = self.glade.get_widget("apply_max").get_active()
        for key in ["max_download_speed", "max_upload_speed", "max_connections" ,"max_upload_slots","btn_apply"]:
            spin = self.glade.get_widget(key)
            spin.set_sensitive(active)


    def on_add(self, widget, data = None):
        label = self.txt_add.get_text()
        self.txt_add.set_text("")
        if label in self.labels:
            return
        aclient.label_add(None , label)
        aclient.label_get_labels(self.cb_update_labels)
        aclient.force_call(block=True)
        self.select_label(label)

    def on_remove(self, widget, data=None):
        label = self.get_selected_label()
        aclient.label_remove(None, label)
        aclient.label_get_labels(self.cb_update_labels)
        self.select_label(0)

    def on_save_label(self, arg = None, apply = False):
        options = {}
        for key in ["max_download_speed", "max_upload_speed", "max_connections" ,"max_upload_slots"]:
            options[key] = self.glade.get_widget(key).get_value()
        options["apply_max"] = self.glade.get_widget("apply_max").get_active()

        if self.glade.get_widget("chk_move_completed").get_active():
            options["move_completed_to"] = self.glade.get_widget("move_completed_to").get_filename()
        else:
            options["move_completed_to"] = None

        aclient.label_set_options(None, self.label, options , apply)

    def on_apply_label(self, arg = None):
        self.on_save_label(apply = True)

    def get_selected_label(self):
        model , iter = self.label_view.get_selection().get_selected()
        return self.label_store.get_value(iter,0)

    def select_label(self, label):
        aclient.force_call(block=True) #sync..
        if label:
            it = self.label_store.iter_nth_child(None,self.labels.index(label))
        elif self.labels:
            it = self.label_store.iter_nth_child(None,0)
        if self.labels:
            self.label_view.get_selection().select_iter(it)

    def build_label_view(self):
        "gtk should have a simple listbox widget..."
        self.label_store = gtk.ListStore(str)

        column = gtk.TreeViewColumn(_("Label"))
        renderer = gtk.CellRendererText()
        column.pack_start(renderer)
        column.set_attributes(renderer, text = 0)


        self.label_view.set_model(self.label_store)
        self.label_view.append_column(column)
        self.label_view.set_headers_visible(False)

        self.label_view.get_selection().connect("changed", self.on_label_changed)

    def on_label_changed(self, selection):
        try:
            (model, row) = self.label_view.get_selection().get_selected()
            self.label = model.get_value(row, 0)
            self.glade.get_widget("txt_label").set_markup("<b>%s</b>" % self.label)
            aclient.label_get_options(self.cb_label_options, self.label)
        except:
            log.debug("none selected")













"""

        label = gtk.Label()
        label.set_markup('<b>' + _('General')        + '</b>')


        self.set_shadow_type(gtk.SHADOW_NONE)
        self.set_label_widget(label)

        self.btn_load = gtk.Button("Load Settings")
        self.btn_load.connect("clicked", self.load_settings, None)

        self.btn_remove = gtk.Button("Remove")
        self.btn_remove.connect("clicked", self.on_remove, None)

        vb = gtk.VBox()
        self.add(vb)
        #vb.add(self.btn_load)
        #vb.add(gtk.Label("Label is in developent, you're testing pre-alfa!!!"))


        self.hide_zero_hits = gtk.CheckButton(_('Hide Zero Hits'))
        vb.add(self.hide_zero_hits)

        label = gtk.Label()
        label.set_markup('<b>' + _('Labels') + '</b>')
        vb.add(label)

        hp = gtk.HPaned()
        hp.add1(self.label_view)


        hp.add2(self.label_options)

        hp.set_position(100)

        hp.set_size_request(400, 200) #bug..


        hbAdd = gtk.HBox()
        hbAdd.add(gtk.Label("Label:"))
        self.txt_add = gtk.Entry()
        hbAdd.add(self.txt_add)
        btn_add = gtk.Button("Add")
        hbAdd.add(btn_add)
        btn_add.connect("clicked", self.on_add, None)

        vb.pack_end(hbAdd)

        label = gtk.Label()
        label.set_markup('<b>' + _('Add') + '</b>')



        vb.pack_end(label)

        vb.pack_end(self.btn_remove, True , True)

        vb.pack_end(hp,True , True)

"""
