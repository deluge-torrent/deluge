# Copyright (C) 2007
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

### Initialization ###

plugin_name = _("Torrent Peers")
plugin_author = "Deluge"
plugin_version = "0.2"
plugin_description = _("""
This shows you the peers associated with each torrent and shows you their ip, \
country, client, percent complete and upload and download speeds.
""")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return TorrentPeers(path, core, interface)

### The Plugin ###
import gtk

import deluge
from TorrentPeers.tab_peers import PeersTabManager

class TorrentPeers:

    def __init__(self, path, core, interface):
        print "Loading TorrentPeers plugin..."
        self.parent = interface
        self.manager = core
        self.config_file = deluge.common.CONFIG_DIR + "/peers.conf"
        self.config = deluge.pref.Preferences(self.config_file, False,
                        defaults={'enable_flags' : True,
                                    'size_18' : True})
        try:
            self.config.load()
        except IOError:
            # File does not exist
            pass
        self.dialog_initialize = True
        self.glade = gtk.glade.XML(path + "/peers_preferences.glade")
        self.dialog = self.glade.get_widget("dialog")
        self.glade.signal_autoconnect({
                                        'toggle_ui': self.toggle_ui,
                                        'on_button_cancel_clicked': self.cancel_clicked,
                                        'on_button_ok_clicked': self.ok_clicked
                                      })
        tree_view = gtk.TreeView()
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.add(tree_view)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.top_widget = scrolled_window

        self.parent_notebook = self.parent.notebook
        self.parent_notebook.append_page(self.top_widget, 
                                         gtk.Label(_("Peers")))
        
        tree_view.show()
        scrolled_window.show()
        
        self.tab_peers = PeersTabManager(tree_view, core)
        self.tab_peers.build_peers_view()
        
        self.config_updated()

    def unload(self):
        self.tab_peers.clear_peer_store()
        tab_page = self.parent_notebook.page_num(self.top_widget)
        self.parent_notebook.remove_page(tab_page)
        self.config.save(self.config_file)

    def configure(self, window):
        self.dialog_initialize = True
        try:
            if self.config.get("enable_flags"):
                self.glade.get_widget("chk_flags").set_active(True)
                self.glade.get_widget("radio_18").set_sensitive(True)
                self.glade.get_widget("radio_25").set_sensitive(True)
                if self.config.get("size_18"):
                    self.glade.get_widget("radio_18").set_active(True)
                    self.glade.get_widget("radio_25").set_active(False)
                else:
                    self.glade.get_widget("radio_18").set_active(False)
                    self.glade.get_widget("radio_25").set_active(True)
            else:
                self.glade.get_widget("chk_flags").set_active(False)
                self.glade.get_widget("radio_18").set_sensitive(False)
                self.glade.get_widget("radio_25").set_sensitive(False)

        self.dialog_initialize = False
        self.dialog.set_transient_for(window)
        self.dialog.show()

    def config_updated(self):
        if self.config.get("enable_flags"):
            self.tab_peers.enable_flags()
            if self.config.get("size_18"):
                if self.tab_peers.flag_size == "25x15":
                    self.tab_peers.clear_flag_cache()
                self.tab_peers.set_flag_size("18x12")
            else:
                if self.tab_peers.flag_size == "18x12":
                    self.tab_peers.clear_flag_cache()
                self.tab_peers.set_flag_size("25x15")
        else:
            self.tab_peers.clear_flag_cache()
            self.tab_peers.disable_flags()            

    def toggle_ui(self, widget):
        if not self.dialog_initialize:
            value = widget.get_active()
            if widget == self.glade.get_widget("chk_flags"):
                if value:
                    self.glade.get_widget("radio_18").set_sensitive(True)
                    self.glade.get_widget("radio_25").set_sensitive(True)
                else:
                    self.glade.get_widget("radio_18").set_sensitive(False)
                    self.glade.get_widget("radio_25").set_sensitive(False)

    def update(self):
        if not self.parent.update_interface:
            return
        
        tab_page = self.parent_notebook.page_num(self.top_widget)
        current_page = self.parent_notebook.get_current_page()
        
        if tab_page == current_page:
            unique_id = self.parent.get_selected_torrent()
            if unique_id is None or \
               unique_id in self.manager.removed_unique_ids:
            #if no torrents added or more than one torrent selected
                self.tab_peers.clear_peer_store()
                self.tab_peers.set_unique_id(None)
                return
            if self.tab_peers.peer_unique_id != unique_id:
                self.tab_peers.clear_peer_store()
                self.tab_peers.set_unique_id(unique_id)
                self.tab_peers.update_peer_store()
            else:
                self.tab_peers.update_peer_store()

    def ok_clicked(self, src):
        self.dialog.hide()
        
        needs_store_update = False
        if self.config.get("enable_flags") and not \
           self.glade.get_widget("chk_flags").get_active():
            needs_store_update = True
             
        self.config.set("enable_flags", 
                        self.glade.get_widget("chk_flags").get_active())
        self.config.set("size_18", 
                        self.glade.get_widget("radio_18").get_active())
        self.config_updated()

        if needs_store_update:
            self.tab_peers.update_peer_store()
            self.tab_peers.ip_column_queue_resize()

    def cancel_clicked(self, src):
        self.dialog.hide()
