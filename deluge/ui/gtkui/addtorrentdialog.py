#
# addtorrentdialog.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
# any later version.
# 
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
import gettext

from deluge.configmanager import ConfigManager
from deluge.log import LOG as log
import deluge.common

class AddTorrentDialog:
    def __init__(self, parent=None):
        # Setup the filechooserdialog
        self.chooser = gtk.FileChooserDialog(_("Choose a .torrent file"),
            parent,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, 
                        gtk.RESPONSE_OK))

        self.chooser.set_icon(deluge.common.get_logo(32))
        self.chooser.set_select_multiple(True)
        self.chooser.set_property("skip-taskbar-hint", True)
        
        # Add .torrent and * file filters
        file_filter = gtk.FileFilter()
        file_filter.set_name(_("Torrent files"))
        file_filter.add_pattern("*." + "torrent")
        self.chooser.add_filter(file_filter)
        file_filter = gtk.FileFilter()
        file_filter.set_name(_("All files"))
        file_filter.add_pattern("*")
        self.chooser.add_filter(file_filter)

        # Load the 'default_load_path' from the config
        self.config = ConfigManager("gtkui.conf")
        if self.config.get("default_load_path") is not None:
            self.chooser.set_current_folder(
                                        self.config.get("default_load_path"))

    def run(self):
        """Returns a list of selected files or None if no files were selected.
        """
        # Run the dialog
        response = self.chooser.run()

        if response == gtk.RESPONSE_OK:
            result = self.chooser.get_filenames()
            self.config.set("default_load_path", 
                                self.chooser.get_current_folder())
        else:
            result = None

        self.chooser.destroy()
        del self.config
        return result
