# Copyright (C) 2007 - Marcos Pinto <markybob@gmail.com>
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

plugin_name = "Move Torrent"
plugin_author = "Marcos Pinto"
plugin_version = "0.2"
plugin_description = _("This plugin allows users to move the torrent to a \
different directory without having to remove and re-add the torrent.  This \
feature can be found by right-clicking on a torrent.\nFurthermore, it \
allows the user to automatically have finished torrents moved to a different \
folder.")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return movetorrentMenu(path, core, interface)


import deluge
from deluge import dialogs
import gtk
import os

DEFAULT_PREFS = {
    "default_finished_path": os.path.expanduser("~/"), 
    "enable_move_completed": False
}

class movetorrentMenu:
    
    def __init__(self, path, core, interface):
        print "Loading Move Torrent plugin..."
        self.path = path
        self.core = core
        self.interface = interface
        self.window = self.interface.window
        self.dialogs = deluge.dialogs
        self.core.connect_event(self.core.constants['EVENT_STORAGE_MOVED'], self.handle_event)
        self.core.connect_event(self.core.constants['EVENT_FINISHED'], self.handle_event)
        self.glade = gtk.glade.XML(path + "/movetorrent.glade")
        self.glade.signal_autoconnect({
                                        'dialog_ok': self.dialog_ok,
                                        'dialog_cancel': self.dialog_cancel
                                      })
        self.dialog = self.glade.get_widget("dialog")
        self.dialog.set_position(gtk.WIN_POS_CENTER)

        self.config_file = deluge.common.CONFIG_DIR + "/move_torrent.conf"
        self.config = deluge.pref.Preferences(self.config_file, global_defaults=False, defaults=DEFAULT_PREFS)
        try:
            self.config.load()
        except IOError:
            pass

        self.menuitem_image = gtk.Image()
        self.menuitem_image.set_from_stock(gtk.STOCK_SAVE_AS, gtk.ICON_SIZE_MENU)

        self.menuitem = gtk.ImageMenuItem(_("_Move Torrent"))
        self.menuitem.set_image(self.menuitem_image)
        self.menuitem.connect("activate", self.movetorrent_clicked)
        self.interface.torrent_menu.append(self.menuitem)
        self.menuitem.show_all()
        
    def update(self):
        pass
    
    def unload(self):
        self.interface.torrent_menu.remove(self.menuitem)
        self.core.disconnect_event(self.core.constants['EVENT_STORAGE_MOVED'], self.handle_event)
        self.core.disconnect_event(self.core.constants['EVENT_FINISHED'], self.handle_event)
        self.config.save(self.config_file)

    def movetorrent_clicked(self, widget):
        unique_ids = self.interface.get_selected_torrent_rows() 

        path = self.dialogs.show_directory_chooser_dialog(None, \
                _("Choose a directory to move files to"))
        if path: 
            self.paused_or_not = {}
            for unique_id in unique_ids:
                self.core.move_storage(unique_id, path)

    def configure(self, window):
        import os.path
        try:
            self.glade.get_widget("chk_move_completed").set_active(self.config.get("enable_move_completed"))
            self.glade.get_widget("finished_path_button").set_filename(self.config.get("default_finished_path"))

        except:
            self.glade.get_widget("chk_move_completed").set_active(False)
            self.glade.get_widget("default_finished_path").set_active(False)
        self.dialog.set_transient_for(window)
        self.dialog.show()

    def dialog_ok(self, source):
        self.dialog.hide()
        self.config.set("enable_move_completed", self.glade.get_widget("chk_move_completed").get_active())
        self.config.set("default_finished_path", self.glade.get_widget("finished_path_button").get_filename())

    def dialog_cancel(self, source):
        self.dialog.hide()

    def handle_event(self, event):
        if event['event_type'] is self.core.constants['EVENT_STORAGE_MOVED']:
            if event['message'] == self.core.unique_IDs[event['unique_ID']].save_dir:
                self.dialogs.show_popup_warning(self.window, _("You cannot move torrent to a different partition. Please check your preferences. Also, you cannot move a torrent's files to the same directory that they are already stored or move a torrent's files before any of its files have actually been created."))
            self.core.unique_IDs[event['unique_ID']].save_dir = event['message']
            self.core.pickle_state()
                    
        elif event['event_type'] is self.core.constants['EVENT_FINISHED']:
            if event['message'] == "torrent has finished downloading":
                if self.config.get('enable_move_completed') and \
                    self.config.get('default_finished_path') != \
                       self.core.get_pref('default_download_path') and \
                    self.core.unique_IDs[event['unique_ID']].save_dir != \
                       self.config.get('default_finished_path'):
                    self.core.move_storage(event['unique_ID'], 
                        self.config.get('default_finished_path'))
