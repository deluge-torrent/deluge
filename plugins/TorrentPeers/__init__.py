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
This is just the peers tab as a plugin.
""")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return TorrentPeers(path, core, interface)

### The Plugin ###
import deluge
import gtk
from TorrentPeers.tab_peers import PeersTabManager

class TorrentPeers:

    def __init__(self, path, core, interface):
        print "Loading TorrentPeers plugin..."
        self.manager = core
        self.parent = interface
        self.config_file = deluge.common.CONFIG_DIR + "/peers.conf"
        self.config = deluge.pref.Preferences(self.config_file)
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
                                        'on_button_cancel_pressed': self.cancel_pressed,
                                        'on_button_ok_pressed': self.ok_pressed
                                      })
        treeView = gtk.TreeView()
        scrolledWindow = gtk.ScrolledWindow()
        scrolledWindow.add(treeView)
        scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.topWidget = scrolledWindow

        self.parentNotebook = self.parent.notebook

        self.parentNotebook.append_page(self.topWidget, gtk.Label(_("Peers")))
        treeView.show()
        scrolledWindow.show()
        self.tab_peers = PeersTabManager(treeView, self.manager)
        self.rebuild_view = False
        self.update_config()
        self.tab_peers.build_peers_view()

    def unload(self):
        self.tab_peers.clear_peer_store()
        numPages = self.parentNotebook.get_n_pages()
        for page in xrange(numPages):
            if self.parentNotebook.get_nth_page(page) == self.topWidget:
                self.parentNotebook.remove_page(page)
                break
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
        except:
            self.glade.get_widget("chk_finished").set_active(False)
            self.glade.get_widget("radio_18").set_sensitive(False)
            self.glade.get_widget("radio_25").set_sensitive(False)
        self.dialog_initialize = False
        self.dialog.set_transient_for(window)
        self.dialog.show()

    def update_config(self, rebuild_view=False):
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
            self.tab_peers.disable_flags()
            self.rebuild_view = rebuild_view
            

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
        numPages = self.parentNotebook.get_n_pages()
        for page in xrange(numPages):
            if self.parentNotebook.get_nth_page(page) == self.topWidget:
                unique_id = self.parent.get_selected_torrent()
                if unique_id is None:
                #if no torrents added or more than one torrent selected
                    self.tab_peers.clear_peer_store()
                    return
                if self.tab_peers.peer_unique_id != unique_id:
                    self.tab_peers.clear_peer_store()
                    self.tab_peers.set_unique_id(unique_id)
                    self.tab_peers.update_peer_store()
                else:
                    if self.rebuild_view:
                        self.tab_peers.clear_peer_store()
                        self.tab_peers.set_unique_id(unique_id)
                        self.tab_peers.rebuild_peer_view(self.topWidget)
                        self.tab_peers.update_peer_store()
                        self.rebuild_view = False
                    self.tab_peers.update_peer_store()
                break

    def ok_pressed(self, src):
        self.dialog.hide()
        if self.config.get("enable_flags") and not self.glade.get_widget("chk_flags").get_active():
            rebuild_view = True
        else:
            rebuild_view = False
        self.config.set("enable_flags", self.glade.get_widget("chk_flags").get_active())
        self.config.set("size_18", self.glade.get_widget("radio_18").get_active())
        self.update_config(rebuild_view)

    def cancel_pressed(self, src):
        self.dialog.hide()
