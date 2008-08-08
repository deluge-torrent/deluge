#
# createtorrentdialog.py
#
# Copyright (C) 2008 Andrew Resch ('andar') <andrewresch@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
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

import gtk
import pkg_resources

import deluge.component as component
import deluge.common
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

class CreateTorrentDialog:
    def __init__(self):
        pass
        
    def show(self):
        self.config = ConfigManager("gtkui.conf")
        glade = gtk.glade.XML(
            pkg_resources.resource_filename(
                "deluge.ui.gtkui", 
                "glade/create_torrent_dialog.glade"))
        
        self.dialog = glade.get_widget("create_torrent_dialog")
        self.dialog.set_transient_for(component.get("MainWindow").window)
        
        glade.signal_autoconnect({
            "on_button_file_clicked": self._on_button_file_clicked,
            "on_button_folder_clicked": self._on_button_folder_clicked,
            "on_button_remote_path_clicked": self._on_button_remote_path_clicked,
            "on_button_cancel_clicked": self._on_button_cancel_clicked,
            "on_button_create_clicked": self._on_button_create_clicked,
            "on_button_up_clicked": self._on_button_up_clicked,
            "on_button_add_clicked": self._on_button_add_clicked,
            "on_button_remove_clicked": self._on_button_remove_clicked,
            "on_button_down_clicked": self._on_button_down_clicked
        })
        

        self.dialog.show_all()
        
    def _on_button_file_clicked(self, widget):
        log.debug("_on_button_file_clicked")
        
    def _on_button_folder_clicked(self, widget):
        log.debug("_on_button_folder_clicked")
    
    def _on_button_remote_path_clicked(self, widget):
        log.debug("_on_button_remote_path_clicked")
    
    def _on_button_cancel_clicked(self, widget):
        log.debug("_on_button_cancel_clicked")
        self.dialog.destroy()
    
    def _on_button_create_clicked(self, widget):
        log.debug("_on_button_create_clicked")
        self.dialog.destroy()
        
    def _on_button_up_clicked(self, widget):
        log.debug("_on_button_up_clicked")
    
    def _on_button_add_clicked(self, widget):
        log.debug("_on_button_add_clicked")
    
    def _on_button_remove_clicked(self, widget):
        log.debug("_on_button_remove_clicked")
    
    def _on_button_down_clicked(self, widget):
        log.debug("_on_button_down_clicked")

