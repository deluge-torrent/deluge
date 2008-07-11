#
# blocklist/gtkui.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
# Copyright (C) 2008 Mark Stahler ('kramed') <markstahler@gmail.com>
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

import os
import pkg_resources    # access plugin egg
from deluge.log import LOG as log
from deluge import component    # for systray
import ui
import gtk, gobject
from deluge.ui.client import aclient

from deluge.configmanager import ConfigManager
config  = ConfigManager("label.conf")
GTK_ALFA = config.get("gtk_alfa")


class GtkUI(ui.UI):
    def __init__(self, plugin_api, plugin_name):
        log.debug("Calling UI init")
        # Call UI constructor
        ui.UI.__init__(self, plugin_api, plugin_name)
        log.debug("Label GtkUI plugin initalized..")

    def enable(self):
        self.plugin.register_hook("on_apply_prefs", self.apply_prefs)
        self.load_interface()

    def disable(self):
        #deluge.component.get("StatusBar").remove_item(self.blocklist_status)
        self.plugin.deregister_hook("on_apply_prefs", self.apply_prefs)
        self.plugin.remove_preferences_page("Label")

    def get_pixmap(self, fname):
        """Returns a pixmap file included with plugin"""
        return pkg_resources.resource_filename("blocklist", os.path.join("data", fname))

    def unload_interface(self):
        self.plugin.remove_preferences_page("Label")

    def load_interface(self):
        if not GTK_ALFA:
            self.plugin.add_preferences_page("Label", gtk.Label(
                "Sorry, the Gtk UI for the Label-plugin is still in development."))
            return

        log.debug("add items to torrentview-popup menu.")


        torrentmenu = component.get("MenuBar").torrentmenu


        self.label_menu = LabelMenu()
        torrentmenu.append(self.label_menu)
        self.label_menu.show_all()

        log.debug("add label column")
        #TODO!
        log.debug("Beginning gtk pane initialization")
        self.config_frame = LabelConfigFrame()

        self.blocklist_pref_page = gtk.VBox()
        self.blocklist_pref_page.set_spacing(6)

        self.blocklist_pref_page.pack_start(self.config_frame,True,True)

        # Add preferences page to preferences page
        log.debug('Adding Label Preferences page')
        self.plugin.add_preferences_page("Label", self.blocklist_pref_page)

        # Load settings from config and fill widgets with settings
        self.fetch_prefs()
        #log.debug('Finished loading Label preferences')


    def fetch_prefs(self):    # Fetch settings dictionary from plugin core and pass it to GTK ui settings
        log.info('LABEL: Fetching and loading Preferences via GTK ui')
        #aclient.block_list_get_options(self.callback_load_prefs)
        self.config_frame.load_settings()

    def apply_prefs(self):
        log.info('Blocklist: Preferences saved via Gtk ui')
        """settings_dict = {
                         "url": self.url.get_text(),
                         "listtype": self.get_ltype(),
                         "check_after_days": self.check_after_days.get_value_as_int(),
                         "load_on_start":self.load_on_start.get_active(),
                         "try_times": self.try_times.get_value_as_int(),
                         "timeout": self.timeout.get_value_as_int()
                         }
        aclient.block_list_set_options(None, settings_dict)
        # Needs to go in another thread or wait until window is closed
        #gobject.idle_add(self.call_critical_setting)
        """

    # GTK Gui Callback functions
    def callback_load_prefs(self, dict):
        self.config_frame.load_settings()
        log.info('Blocklist: Callback Load Prefs GTK ui')
        """self.settings_url(dict['url'])
        self.settings_listtype(dict['listtype'])
        self.settings_load(dict['load_on_start'])
        self.settings_check_after_days(dict['check_after_days'])
        self.settings_timeout(dict['timeout'])
        self.settings_try_times(dict['try_times'])
        """

def cb_none(args):
    "hack for empty callbacks."
    pass

"""
class LabelList(gtk.TreeView):
    "a simple listbox is way too hard in gtk :(."
    def __init__(self):
        pass
"""

class LabelMenu(gtk.MenuItem):
    def __init__(self):
        gtk.MenuItem.__init__(self, "Label (wip)")
        self.show_all()

        #attach..
        torrentmenu = component.get("MenuBar").torrentmenu
        torrentmenu.connect("show", self.on_show, None)

    def get_torrent_ids(self):
        return component.get("TorrentView").get_selected_torrents()

    def on_show(self, widget=None, data=None):
        log.debug("label-on-show")
        aclient.label_get_labels(self.cb_labels)
        aclient.force_call(block=True)

    def cb_labels(self , labels):
        log.debug("cb_labels-start")
        self.sub_menu = gtk.Menu()
        for label in labels:
            item = gtk.MenuItem(label)
            item.connect("activate", self.on_select_label, label)
            self.sub_menu.append(item)
        self.set_submenu(self.sub_menu)
        self.show_all()
        log.debug("cb_labels-end")

    def on_select_label(self, widget=None, label_id = None):
        log.debug("select label:%s,%s" % (label_id ,self.get_torrent_ids()) )
        for torrent_id in self.get_torrent_ids():
            aclient.label_set_torrent(cb_none, torrent_id, label_id)
        #aclient.force_call(block=True)

class LabelConfigFrame(gtk.Frame):
    def __init__(self):
        gtk.Frame.__init__(self)
        self.build_label_view()
        self.build_label_options()
        self.build_ui()
        self.labels = []

    def load_settings(self ,widget=None ,data=None):
        aclient.label_get_labels(self.cb_update_labels)

    def cb_update_labels(self, labels):
        self.labels = labels
        self.label_store.clear()
        for label in labels:
            self.label_store.append([label])

    def on_add(self, widget, data=None):
        label = self.txt_add.get_text()
        self.txt_add.set_text("")
        if label in self.labels:
            return
        aclient.label_add(cb_none, label)
        aclient.label_get_labels(self.cb_update_labels)
        self.select_label(label)

        #aclient.force_call(block=True)

    def on_remove(self, widget, data=None):
        label = self.get_selected_label()
        aclient.label_remove(cb_none, label)
        aclient.label_get_labels(self.cb_update_labels)
        self.select_label(0)

    def get_selected_label(self):
        model , iter = self.label_view.get_selection().get_selected()
        return self.label_store.get_value(iter,0)

    def select_label(self, label):
        aclient.force_call(block=True) #sync..
        if label:
            it = self.label_store.iter_nth_child(None,self.labels.index(label))
        else:
            it = self.label_store.iter_nth_child(None,0)
        self.label_view.get_selection().select_iter(it)

    def build_label_view(self):
        "gtk should have a simple listbox widget..."
        self.label_store = gtk.ListStore(str)

        column = gtk.TreeViewColumn(_("Label"))
        renderer = gtk.CellRendererText()
        column.pack_start(renderer)
        column.set_attributes(renderer, text = 0)

        self.label_view = gtk.TreeView(self.label_store)
        self.label_view.append_column(column)
        self.label_view.set_headers_visible(False)

        #self.label_scroll = gtk.ScrolledWindow()
        #self.label_scroll.add_with_viewport(self.label_view)


    def build_label_options(self):
        self.label_options = gtk.Label("Per label options")

    def build_ui(self):
        #vbox
        #general
        #[x] stuff
        #labels:
        #hpaned : left-right
        #right: listbox with labels
        #left: label-options
        #---
        #label-add
        #--

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
        vb.add(self.btn_load)
        vb.add(gtk.Label("Label is in developent, you're testing pre-alfa!!!"))


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










