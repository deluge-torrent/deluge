# Copyright (C) 2007 - Micah Bucy <eternalsword@gmail.com>
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

plugin_name = _("Torrent Pieces")
plugin_author = "Micah Bucy"
plugin_version = "0.2"
plugin_description = _("""
Adds a pieces tab which gives piece by piece progress for a torrent.
Each piece is represented by a small progress bar.

Pieces currently downloading show up as partially filled progress bars,
but this does not represent percentage done.  

More information is provided as a tooltip for each piece.
For currently downloading pieces, the tooltip contains the number
of blocks finished as well as the peer speed for that piece.

When the plugin initializes, such as when enabling the plugin or
when a different torrent is selected, the cpu will spike.  This is normal,
as initialization must get information on every piece from libtorrent,
and the cpu will normalize once all of the information is retrieved.

This plugin supports multifile torrents.  If a file is skipped, it does not
show up in the pieces tab.
""")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return TorrentPieces(path, core, interface)

### The Plugin ###
import deluge
import gtk
from TorrentPieces.tab_pieces import PiecesTabManager

class TorrentPieces:

    def __init__(self, path, core, interface):
        print "Loading TorrentPieces plugin..."
        self.manager = core
        self.parent = interface
        scrolledWindow = gtk.ScrolledWindow()
        scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.topWidget = scrolledWindow

        self.parentNotebook = self.parent.notebook

        self.parentNotebook.append_page(self.topWidget, gtk.Label(_("Pieces")))
        self.topWidget.show_all()
        self.tab_pieces = PiecesTabManager(self.manager)

    def unload(self):
        self.tab_pieces.disconnect_handlers()
        self.tab_pieces.clear_pieces_store()
        numPages = self.parentNotebook.get_n_pages()
        for page in xrange(numPages):
            if self.parentNotebook.get_nth_page(page) == self.topWidget:
                self.parentNotebook.remove_page(page)
                break

    def update(self):
        update_files_removed = self.manager.update_files_removed
        unique_id = self.parent.get_selected_torrent()
        if unique_id is None:
        #if no torrents added or more than one torrent selected
            self.tab_pieces.disconnect_handlers()
            self.tab_pieces.clear_pieces_store()
            return
        if unique_id != self.tab_pieces.unique_id or unique_id in update_files_removed.keys():
        #if different torrent was selected or file priorities were changed.
            self.tab_pieces.disconnect_handlers()
            self.tab_pieces.clear_pieces_store()
            numPages = self.parentNotebook.get_n_pages()
            for page in xrange(numPages):
                if self.parentNotebook.get_nth_page(page) == self.topWidget:
                    break
            switch_page = False
            if self.parentNotebook.get_current_page() == page:
                switch_page = True
            self.parentNotebook.remove_page(page)
            viewport = gtk.Viewport()
            scrolledWindow = gtk.ScrolledWindow()
            scrolledWindow.add(viewport)
            scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            label = gtk.Label(_("""
This is a temporary page used while the pieces tab gets built.
When operations are complete this will automatically become the
pieces tab.
"""))
            label.set_alignment(0,0)
            viewport.add(label)
            self.parentNotebook.insert_page(scrolledWindow,gtk.Label(_("Pieces")),page)
            scrolledWindow.show_all()
            if switch_page:
                self.parentNotebook.set_current_page(page)
            self.tab_pieces.set_unique_id(unique_id)
            self.topWidget = self.tab_pieces.prepare_pieces_store()
            switch_page = False
            if self.parentNotebook.get_current_page() == page:
                switch_page = True
            self.parentNotebook.remove_page(page)
            self.parentNotebook = self.parent.notebook
            self.parentNotebook.insert_page(self.topWidget, gtk.Label(_("Pieces")), page)
            self.topWidget.show_all()
            if switch_page:
                self.parentNotebook.set_current_page(page)
            self.tab_pieces.connect_handlers()
