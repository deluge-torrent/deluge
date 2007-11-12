#
# edittrackersdialog.py
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

import gtk, gtk.glade
import pkg_resources

import deluge.common
import deluge.ui.client as client
import deluge.ui.component as component
from deluge.log import LOG as log

class EditTrackersDialog:
    def __init__(self, torrent_id, parent=None):
        self.glade = gtk.glade.XML(
                    pkg_resources.resource_filename("deluge.ui.gtkui", 
                                            "glade/edit_trackers.glade"))
        
        self.dialog = self.glade.get_widget("edit_trackers_dialog")
        self.dialog.set_icon(deluge.common.get_logo(32))
        
        if parent != None:
            self.dialog.set_transient_for(parent)

        # Connect the signals
        self.glade.signal_autoconnect({
            "on_button_up_clicked": self.on_button_up_clicked,
            "on_button_add_clicked": self.on_button_add_clicked,
            "on_button_remove_clicked": self.on_button_remove_clicked,
            "on_button_down_clicked": self.on_button_down_clicked,
            "on_button_ok_clicked": self.on_button_ok_clicked,
            "on_button_cancel_clicked": self.on_button_cancel_clicked
        })

    def run(self):
        self.dialog.show()
        
    def on_button_up_clicked(self, widget):
        log.debug("on_button_up_clicked")
    def on_button_add_clicked(self, widget):
        log.debug("on_button_add_clicked")
    def on_button_remove_clicked(self, widget):
        log.debug("on_button_remove_clicked")
    def on_button_down_clicked(self, widget):
        log.debug("on_button_down_clicked")
    def on_button_ok_clicked(self, widget):
        log.debug("on_button_ok_clicked")
    def on_button_cancel_clicked(self, widget):
        log.debug("on_button_cancel_clicked")
