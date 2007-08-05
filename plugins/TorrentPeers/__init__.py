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
        self.tab_peers.build_peers_view()

    def unload(self):
        self.tab_peers.clear_peer_store()
        numPages = self.parentNotebook.get_n_pages()
        for page in xrange(numPages):
            if self.parentNotebook.get_nth_page(page) == self.topWidget:
                self.parentNotebook.remove_page(page)
                break

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
                    self.tab_peers.update_peer_store()
                break
