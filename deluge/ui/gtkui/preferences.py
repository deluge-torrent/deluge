#
# preferences.py
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
import pkg_resources

from deluge.log import LOG as log

class Preferences:
    def __init__(self, window):
        self.window = window
        self.pref_glade = gtk.glade.XML(
                    pkg_resources.resource_filename("deluge.ui.gtkui",
                                            "glade/preferences_dialog.glade"))
        self.pref_dialog = self.pref_glade.get_widget("pref_dialog")
        self.treeview = self.pref_glade.get_widget("treeview")
        self.notebook = self.pref_glade.get_widget("notebook")
        # Setup the liststore for the categories (tab pages)
        self.liststore = gtk.ListStore(int, str)
        self.treeview.set_model(self.liststore)
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Categories", render, text=1)
        self.treeview.append_column(column)
        # Add the default categories
        self.liststore.append([0, "Downloads"])
        self.liststore.append([1, "Network"])
        self.liststore.append([2, "Bandwidth"])
        self.liststore.append([3, "Other"])
        self.liststore.append([4, "Plugins"])
        
        # Connect to the 'changed' event of TreeViewSelection to get selection
        # changes.
        self.treeview.get_selection().connect("changed", 
                                    self.on_selection_changed)
        
        self.pref_glade.signal_autoconnect({
            "on_pref_dialog_delete_event": self.on_pref_dialog_delete_event,
            "on_button_ok_clicked": self.on_button_ok_clicked,
            "on_button_apply_clicked": self.on_button_apply_clicked,
            "on_button_cancel_clicked": self.on_button_cancel_clicked
        })
        
    def show(self):
        self.pref_dialog.show()
        
    def hide(self):
        self.pref_dialog.hide()
    
    def on_pref_dialog_delete_event(self, widget, event):
        self.hide()
        return True
    
    def on_button_ok_clicked(self, data):
        log.debug("on_button_ok_clicked")

    def on_button_apply_clicked(self, data):
        log.debug("on_button_apply_clicked")

    def on_button_cancel_clicked(self, data):
        log.debug("on_button_cancel_clicked")
        
    def on_selection_changed(self, treeselection):
        # Show the correct notebook page based on what row is selected.
        (model, row) = treeselection.get_selected()
        self.notebook.set_current_page(model.get_value(row, 0))

