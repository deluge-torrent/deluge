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

plugin_name = _("Move Torrent")
plugin_author = "Marcos Pinto"
plugin_version = "0.1"
plugin_description = _("This plugin allows users to move the torrent to a \
    different directory without having to remove and re-add the torrent.  This \
    feature can be found by right-clicking on a torrent.")

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

class movetorrentMenu:
    
    def __init__(self, path, core, interface):
        print "Loading Move Torrent plugin..."
        self.path = path
        self.core = core
        self.interface = interface
        self.dialogs = deluge.dialogs

        # Add menu item to torrent context menu
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

    def movetorrent_clicked(self, widget):
        unique_ids = self.interface.get_selected_torrent_rows() 

        path = self.dialogs.show_directory_chooser_dialog(None, \
                _("Choose a directory to move files to"))
        if path: 
            for unique_id in unique_ids: 
                self.core.move_storage(unique_id, path) 
