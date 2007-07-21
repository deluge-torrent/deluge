#
# mainwindow.py
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

import logging

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
import pkg_resources

from menubar import MenuBar
from toolbar import ToolBar
from torrentview import TorrentView

# Get the logger
log = logging.getLogger("deluge")

class MainWindow:
    def __init__(self):
        # Get the glade file for the main window
        self.main_glade = gtk.glade.XML(
                    pkg_resources.resource_filename("deluge.ui.gtkui", 
                                                    "glade/main_window.glade"))

        self.window = self.main_glade.get_widget("main_window")
        
        # Initialize various components of the gtkui
        self.menubar = MenuBar(self)
        self.toolbar = ToolBar(self)
        self.torrentview = TorrentView(self)
    
    def show(self):
        self.window.show_all()
    
    def hide(self):
        self.window.hide()
        
    def quit(self):
        self.hide()
        gtk.main_quit()
