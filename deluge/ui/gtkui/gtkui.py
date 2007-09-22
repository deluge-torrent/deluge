#
# gtkui.py
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
import locale
import pkg_resources

from mainwindow import MainWindow
from signals import Signals
from pluginmanager import PluginManager
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log
import deluge.configmanager

DEFAULT_PREFS = {
    "interactive_add": False,
    "enable_files_dialog": False,
    "enable_system_tray": True,
    "close_to_tray": True,
    "start_in_tray": False,
    "lock_tray": False,
    "tray_password": "",
    "open_folder_stock": True,
    "stock_file_manager": 0,
    "open_folder_location": "",
    "check_new_releases": False,
    "send_info": False,
    "default_load_path": None,
    "window_maximized": False,
    "window_x_pos": -1,
    "window_y_pos": -1,
    "window_width": -1,
    "window_height": -1
}

class GtkUI:
    def __init__(self):
        # Initialize gettext
        locale.setlocale(locale.LC_MESSAGES, '')
        locale.bindtextdomain("deluge", 
                    pkg_resources.resource_filename(
                                            "deluge", "i18n"))
        locale.textdomain("deluge")
        gettext.bindtextdomain("deluge",
                    pkg_resources.resource_filename(
                                            "deluge", "i18n"))
        gettext.textdomain("deluge")
        gettext.install("deluge",
                    pkg_resources.resource_filename(
                                            "deluge", "i18n"))
        
        # Make sure gtkui.conf has at least the defaults set
        config = ConfigManager("gtkui.conf", DEFAULT_PREFS)
        del config
        
        # Initialize the main window
        self.mainwindow = MainWindow()
        
        # Start the signal receiver
        self.signal_receiver = Signals(self)
        
        # Initalize the plugins
        self.plugins = PluginManager(self)
        
        # Show the main window
        self.mainwindow.show()
        
        # Start the gtk main loop
        gtk.main()

        # Clean-up
        del self.mainwindow
        del self.signal_receiver
        del self.plugins
        del deluge.configmanager
