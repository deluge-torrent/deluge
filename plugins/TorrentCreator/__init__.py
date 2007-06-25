# Copyright (C) 2007 - Andrew Resch <andrewresch@gmail.com>
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

plugin_name = _("Torrent Creator")
plugin_author = "Andrew Resch"
plugin_version = "0.1"
plugin_description = _("A torrent creator plugin")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return TorrentCreator(path, core, interface)

### The Plugin ###

import deluge
import gtk, gtk.glade

class TorrentCreator:

    def __init__(self, path, core, interface):
      print "Loading torrent creator plugin..."
      self.path = path
      self.core = core
      self.interface = interface
      self.glade = None
      
      # Add 'New Torrent' menu item to the File menu
      self.menuitem_image = gtk.Image()
      self.menuitem_image.set_from_stock(gtk.STOCK_NEW, gtk.ICON_SIZE_MENU)

      self.menuitem = gtk.ImageMenuItem(_("New Torrent"))
      self.menuitem.set_image(self.menuitem_image)
      self.menuitem.connect("activate", self.new_torrent_clicked)
      self.interface.wtree.get_widget("menu_file").get_submenu().prepend(self.menuitem)
      self.menuitem.show_all()

      # Add a 'New Torrent' button to the toolbar
      self.toolbutton_image = gtk.Image()
      self.toolbutton_image.set_from_stock(gtk.STOCK_NEW, gtk.ICON_SIZE_MENU)
      
      self.toolbutton = gtk.ToolButton(self.toolbutton_image, _("New Torrent"))
      self.toolbutton.connect("clicked", self.new_torrent_clicked)
      self.interface.wtree.get_widget("tb_left").insert(self.toolbutton, 0)
      self.toolbutton.show_all()

    def destroy(self):
      self.dialog.hide()
      self.dialog = None

    def update(self):
      pass
      
    def unload(self):
      pass

    def new_torrent_clicked(self, widget, data=None):
      # Show the torrent creator dialog
      if self.glade == None:
        self.glade = gtk.glade.XML(self.path + "/torrentcreator.glade")
  
      self.dialog = self.glade.get_widget("torrentcreator")
      self.glade.get_widget("piece_size_combobox").set_active(0)
      self.dialog.connect("destroy", self.destroy)
      self.dialog.show_all()
      response = self.dialog.run()
      
      # If the user clicks OK then we need to call create_torrent()
      if response == 1:
        self.create_torrent()
      
      self.destroy()
      return
      
    def create_torrent(self):
      # Create a torrent from the information provided in the torrentcreator dialog
      if self.glade.get_widget("folder_radiobutton").get_active():
        source = self.glade.get_widget("folder_chooserbutton").get_filename()
      else:
        source = self.glade.get_widget("file_chooserbutton").get_filename()
        
      torrent = self.glade.get_widget("torrent_chooserbutton").get_filename()
      
      piece_size = self.glade.get_widget("piece_size_combobox")
      piece_size = piece_size.get_model().get_value(piece_size.get_active_iter(), 0).split(" ")[0]
            
      trackers = self.glade.get_widget("trackers_textview").get_buffer()
      (start, end) = trackers.get_bounds()
      trackers = trackers.get_text(start, end).strip()

      comments = self.glade.get_widget("comments_textview").get_buffer()
      (start, end) = comments.get_bounds()
      comments = comments.get_text(start, end).strip()
      
      author = self.glade.get_widget("author_entry").get_text()
      
      print "create_torrent: ", torrent, source, trackers, comments, piece_size, author
      #return self.core.create_torrent(torrent, source, trackers, comments, piece_size, author)
      return
