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

plugin_name = "Torrent Creator"
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
      print "Loading TorrentCreator plugin..."
      self.path = path
      self.core = core
      self.interface = interface
      self.glade = None
      
      # Add 'New Torrent' menu item to the File menu
      self.menuitem_image = gtk.Image()
      self.menuitem_image.set_from_stock(gtk.STOCK_NEW, gtk.ICON_SIZE_MENU)

      self.menuitem = gtk.ImageMenuItem(_("_New Torrent"))
      self.menuitem.set_image(self.menuitem_image)
      self.menuitem.connect("activate", self.new_torrent_clicked)
      self.interface.wtree.get_widget("menu_file").get_submenu().prepend(self.menuitem)
      self.menuitem.show_all()

      # Add a 'New Torrent' button to the toolbar
      self.toolbutton_image = gtk.Image()
      self.toolbutton_image.set_from_stock(gtk.STOCK_NEW, gtk.ICON_SIZE_MENU)
      
      self.toolbutton = gtk.ToolButton(self.toolbutton_image, _("New Torrent"))
      self.toolbutton_tip = gtk.Tooltips()
      self.toolbutton.set_tooltip(self.toolbutton_tip, _("Create New Torrent"))
      self.toolbutton.connect("clicked", self.new_torrent_clicked)
      self.interface.wtree.get_widget("tb_left").insert(self.toolbutton, 0)
      self.toolbutton.show_all()

    def destroy(self, data=None):
      self.dialog.hide()
      self.dialog.destroy()

    def update(self):
      pass
      
    def unload(self):
      print "Unloading TorrentCreator plugin..."
      self.interface.wtree.get_widget("menu_file").get_submenu().remove(self.menuitem)
      self.interface.wtree.get_widget("tb_left").remove(self.toolbutton)
      

    def new_torrent_clicked(self, widget, data=None):
      # Show the torrent creator dialog
      self.glade = gtk.glade.XML(self.path + "/torrentcreator.glade")
  
      self.dialog = self.glade.get_widget("torrentcreator")
      self.glade.get_widget("piece_size_combobox").set_active(3)
      self.glade.get_widget("torrent_chooserbutton").connect("clicked", self.torrent_chooserbutton_clicked)
      self.glade.get_widget("ok_button").connect("clicked", self.create_torrent)
      self.glade.get_widget("close_button").connect("clicked", self.destroy)
      self.dialog.show_all()
      response = self.dialog.run()
      
      if response == 0:
        self.destroy()
        
      return
    
    def torrent_chooserbutton_clicked(self, widget):
      filechooser = gtk.FileChooserDialog(title=_("Save file as..."), 
                        parent=None, action=gtk.FILE_CHOOSER_ACTION_SAVE, 
                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
                                 gtk.STOCK_OK, gtk.RESPONSE_OK), backend=None)
      response = filechooser.run()
      # Update the torrentfile entry widget if a file was selected.
      if response == gtk.RESPONSE_OK:
        torrent = filechooser.get_filename()
        if not torrent.endswith(".torrent"):
          torrent += ".torrent"
        self.glade.get_widget("torrentfile_entry").set_text(torrent)
      
      filechooser.destroy()
    
    def create_torrent(self, widget):
      # Create a torrent from the information provided in the torrentcreator dialog
      if self.glade.get_widget("folder_radiobutton").get_active():
        source = self.glade.get_widget("folder_chooserbutton").get_filename()
      else:
        source = self.glade.get_widget("file_chooserbutton").get_filename()
      
      if source == "" or source == None:
        deluge.dialogs.show_popup_warning(self.dialog, _("You must select a source for the torrent."))
        return False
        
      torrent = self.glade.get_widget("torrentfile_entry").get_text()
      
      if torrent == "" or torrent == None:
        # Send alert to the user that we need a torrent filename to save to
        deluge.dialogs.show_popup_warning(self.dialog, _("You must select a file to save the torrent as."))
        return False
    
      piece_size = self.glade.get_widget("piece_size_combobox")
      piece_size = int(piece_size.get_model().get_value(piece_size.get_active_iter(), 0).split(" ")[0])
            
      trackers = self.glade.get_widget("trackers_textview").get_buffer()
      (start, end) = trackers.get_bounds()
      trackers = trackers.get_text(start, end).strip()
      
      comments = self.glade.get_widget("comments_textview").get_buffer()
      (start, end) = comments.get_bounds()
      comments = comments.get_text(start, end).strip()
      
      author = self.glade.get_widget("author_entry").get_text()
      
      if author == "" or author == None:
        author = _("Deluge")
      
      add_torrent = self.glade.get_widget("add_torrent_checkbox").get_active()
      set_private = self.glade.get_widget("chk_set_priv").get_active()
      # Destroy the dialog.. we don't need it anymore
      self.destroy()

      # Create the torrent and add it to the queue if necessary
      if self.core.create_torrent(torrent, source, trackers, comments, 
                                  piece_size, author, set_private) == 1:
        # Torrent was created successfully
        if add_torrent:
          # We need to add this torrent to the queue
          self.interface.interactive_add_torrent(torrent)
        return True
      else:
        return False
