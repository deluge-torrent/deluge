#
# toolbar.py
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

import deluge.ui.component as component
from deluge.log import LOG as log

class ToolBar(component.Component):
    def __init__(self):
        component.Component.__init__(self, "ToolBar")
        log.debug("ToolBar Init..")
        self.window = component.get("MainWindow")
        self.toolbar = self.window.main_glade.get_widget("toolbar")
        ### Connect Signals ###
        self.window.main_glade.signal_autoconnect({
            "on_toolbutton_add_clicked": self.on_toolbutton_add_clicked,
            "on_toolbutton_remove_clicked": self.on_toolbutton_remove_clicked,
            "on_toolbutton_clear_clicked": self.on_toolbutton_clear_clicked,
            "on_toolbutton_pause_clicked": self.on_toolbutton_pause_clicked,
            "on_toolbutton_resume_clicked": self.on_toolbutton_resume_clicked,
            "on_toolbutton_preferences_clicked": \
                self.on_toolbutton_preferences_clicked,
            "on_toolbutton_connectionmanager_clicked": \
                self.on_toolbutton_connectionmanager_clicked
        })
    
    def add_toolbutton(self, callback, label=None, image=None, stock=None,
                                                         tooltip=None):
        """Adds a toolbutton to the toolbar"""
        # Create the button
        toolbutton = gtk.ToolButton(stock)
        if label is not None:
            toolbutton.set_label(label)
        if image is not None:
            toolbutton.set_icon_widget(image)
        # Set the tooltip
        if tooltip is not None:
            tip = gtk.Tooltips()
            tip.set_tip(toolbutton, tooltip)
        
        # Connect the 'clicked' event callback
        toolbutton.connect("clicked", callback)
        
        # Append the button to the toolbar
        self.toolbar.insert(toolbutton, -1)
        
        # Show the new toolbutton
        toolbutton.show()
        
        return
    
    def add_separator(self, position=None):
        """Adds a separator toolitem"""
        sep = gtk.SeparatorToolItem()
        if position is not None:
            self.toolbar.insert(sep, position)
        else:
            # Append the separator
            self.toolbar.insert(sep, -1)
        return
        
    ### Callbacks ###
    def on_toolbutton_add_clicked(self, data):
        log.debug("on_toolbutton_add_clicked")
        # Use the menubar's callback
        component.get("MenuBar").on_menuitem_addtorrent_activate(data)

    def on_toolbutton_remove_clicked(self, data):
        log.debug("on_toolbutton_remove_clicked")
        # Use the menubar's callbacks
        component.get("MenuBar").on_menuitem_remove_activate(data)

    def on_toolbutton_clear_clicked(self, data):
        log.debug("on_toolbutton_clear_clicked")
        # Use the menubar's callbacks
        component.get("MenuBar").on_menuitem_clear_activate(data)
        
    def on_toolbutton_pause_clicked(self, data):
        log.debug("on_toolbutton_pause_clicked")
        # Use the menubar's callbacks
        component.get("MenuBar").on_menuitem_pause_activate(data)
     
    def on_toolbutton_resume_clicked(self, data):
        log.debug("on_toolbutton_resume_clicked")
        # Use the menubar's calbacks
        component.get("MenuBar").on_menuitem_resume_activate(data)

    def on_toolbutton_preferences_clicked(self, data):
        log.debug("on_toolbutton_preferences_clicked")
        # Use the menubar's callbacks
        component.get("MenuBar").on_menuitem_preferences_activate(data)

    def on_toolbutton_connectionmanager_clicked(self, data):
        log.debug("on_toolbutton_connectionmanager_clicked")
        # Use the menubar's callbacks
        component.get("MenuBar").on_menuitem_connectionmanager_activate(data)
