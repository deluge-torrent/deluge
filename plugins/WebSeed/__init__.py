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

plugin_name = _("Web Seed")
plugin_author = "Marcos Pinto"
plugin_version = "0.1"
plugin_description = _("This plugin allows users to add web seeds to their torrents")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return webseedMenu(path, core, interface)


import deluge
import gtk
import os

class webseedMenu:
    
    def __init__(self, path, core, interface):
        print "Loading Web Seed plugin..."
        self.path = path
        self.core = core
        self.interface = interface
        self.glade = gtk.glade.XML(path + "/webseed.glade")
        self.dialog = self.glade.get_widget("dialog")
        # Add menu item to torrent context menu
        self.menuitem_image = gtk.Image()
        self.menuitem_image.set_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)

        self.menuitem = gtk.ImageMenuItem(_("_Add Web Seed"))
        self.menuitem.set_image(self.menuitem_image)
        self.menuitem.connect("activate", self.webseed_clicked)
        self.interface.torrent_menu.append(self.menuitem)
        self.menuitem.show_all()

        self.config_file = deluge.common.CONFIG_DIR + "/web_seed.conf"
        self.config = deluge.pref.Preferences(self.config_file, global_defaults=False)
        try:
            self.config.load()
        except IOError:
            pass
        
    def update(self):
        pass
    
    def unload(self):
        self.interface.torrent_menu.remove(self.menuitem)        

    def webseed_clicked(self, widget):
        self.unique_ID = self.interface.get_selected_torrent()
        self.dialog.show()
        response = self.dialog.run()
        self.dialog.hide()
        if response:
            text = self.glade.get_widget("txt_url").get_text().strip()
            if common.is_url(text):
                self.core.add_url_seed(self.unique_ID, text)
