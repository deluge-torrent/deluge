#
# removetorrentdialog.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
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

import gtk, gtk.glade
import pkg_resources

import deluge.common
from deluge.ui.client import aclient as client
import deluge.component as component
from deluge.log import LOG as log

class RemoveTorrentDialog:
    def __init__(self, torrent_ids, remove_torrentfile=False, remove_data=False):
        self.torrent_ids = torrent_ids
        self.remove_torrentfile = remove_torrentfile
        self.remove_data = remove_data
        
        self.glade = gtk.glade.XML(
            pkg_resources.resource_filename("deluge.ui.gtkui", 
                "glade/remove_torrent_dialog.glade"))
        
        self.dialog = self.glade.get_widget("remove_torrent_dialog")
        self.dialog.set_icon(deluge.common.get_logo(32))
        self.dialog.set_transient_for(component.get("MainWindow").window)
        
        self.glade.signal_autoconnect({
            "on_button_ok_clicked": self.on_button_ok_clicked,
            "on_button_cancel_clicked": self.on_button_cancel_clicked
        })
        
        if len(self.torrent_ids) > 1:
            # We need to pluralize the dialog
            self.dialog.set_title("Remove Torrents?")
            self.glade.get_widget("label_title").set_markup(
                _("<big><b>Are you sure you want to remove the selected torrents?</b></big>"))
            self.glade.get_widget("button_ok").set_label(_("Remove Selected Torrents"))
        
        if self.remove_torrentfile or self.remove_data:
            self.glade.get_widget("hseparator1").show()
        if self.remove_torrentfile:
            self.glade.get_widget("hbox_torrentfile").show()
        if self.remove_data:
            self.glade.get_widget("hbox_data").show()

    def run(self):
        if self.torrent_ids == None or self.torrent_ids == []:
            self.dialog.destroy()
            return
        self.dialog.show()
    
    def on_button_ok_clicked(self, widget):
        client.remove_torrent(
            self.torrent_ids, self.remove_torrentfile, self.remove_data)
        # Unselect all to avoid issues with the selection changed event
        component.get("TorrentView").treeview.get_selection().unselect_all()
        self.dialog.destroy()
        
    def on_button_cancel_clicked(self, widget):
        self.dialog.destroy()
        
