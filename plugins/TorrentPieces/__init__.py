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
plugin_version = "0.3"
plugin_description = _("""
Pieces tab now shows percentage instead
of progress bars.  There are no longer any tooltips.
Peer speed uses following symbols:
fast is +
medium is =
slow is -

monospace font is required for columns to be aligned.

Finished torrents do not show piece information, just
a message that the torrent is complete.
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
        self.config_file = deluge.common.CONFIG_DIR + "/pieces.conf"
        self.config = deluge.pref.Preferences(self.config_file)
        try:
            self.config.load()
        except IOError:
            # File does not exist
            pass
        self.glade = gtk.glade.XML(path + "/pieces_preferences.glade")
        widget = self.glade.get_widget("hbox_columns")
        self.combo_columns = gtk.combo_box_new_text()
        for x in xrange(100):
            self.combo_columns.append_text(str(x+1))
        widget.pack_start(self.combo_columns, expand=False)
        widget.show_all()
        widget = self.glade.get_widget("hbox_font_size")
        self.combo_font_size = gtk.combo_box_new_text()
        for x in xrange(100):
            self.combo_font_size.append_text(str(x+1))
        widget.pack_start(self.combo_font_size, expand=False)
        widget.show_all()
        self.dialog = self.glade.get_widget("dialog")
        self.glade.signal_autoconnect({
                                        'on_button_cancel_pressed': self.cancel_pressed,
                                        'on_button_ok_pressed': self.ok_pressed
                                      })
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        viewport = gtk.Viewport()
        scrolled_window.add(viewport)
        self.top_widget = scrolled_window

        self.parent_notebook = self.parent.notebook

        self.parent_notebook.append_page(self.top_widget, gtk.Label(_("Pieces")))
        self.top_widget.show_all()
        columns = self.config.get("columns")
        if columns is None:
            columns = 15
        font_size = self.config.get("font_size")
        if font_size is None:
            font_size = 9
        self.tab_pieces = PiecesTabManager(self.manager, viewport, columns, font_size)
        self.manager.connect_event(self.manager.constants['EVENT_FINISHED'], self.handle_event)

    def unload(self):
        self.tab_pieces.disconnect_handlers()
        self.manager.disconnect_event(self.manager.constants['EVENT_FINISHED'], self.handle_event)
        self.tab_pieces.clear_pieces_store()
        tab_page = self.parent_notebook.page_num(self.top_widget)
        self.parent_notebook.remove_page(tab_page)

    def configure(self, window):
        try:
            self.combo_columns.set_active(self.config.get("columns"))
        except:
            self.combo_columns.set_active(15)
        try:
            self.combo_font_size.set_active(self.config.get("font_size"))
        except:
            self.combo_font_size.set_active(9)
        self.dialog.set_transient_for(window)
        self.dialog.show()

    def handle_event(self, event):
        self.tab_pieces.disconnect_handlers()
        self.tab_pieces.clear_pieces_store()
        self.tab_pieces.set_unique_id(event['unique_ID'])
        self.tab_pieces.prepare_pieces_store()

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
            self.tab_pieces.set_unique_id(unique_id)
            self.tab_pieces.prepare_pieces_store()
            self.tab_pieces.connect_handlers()

    def ok_pressed(self, src):
        self.dialog.hide()
        
        needs_store_update = False
        if self.config.get("columns") !=\
                self.combo_columns.get_active()\
            or self.config.get("font_size") !=\
                self.combo_font_size.get_active():
            needs_store_update = True
            
        self.config.set("columns", 
                        self.combo_columns.get_active())
        self.config.set("font_size", 
                        self.combo_font_size.get_active())
        self.tab_pieces.set_columns(self.combo_columns.get_active())
        self.tab_pieces.set_font_size(self.combo_font_size.get_active())
        if needs_store_update:
            self.tab_pieces.clear_pieces_store(clear_unique_id=False)
            self.tab_pieces.prepare_pieces_store()

    def cancel_pressed(self, src):
        self.dialog.hide()
