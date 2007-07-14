#
# toolbar.py
#
# Copyright (C) Andrew Resch    2007 <andrewresch@gmail.com> 
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

# Get the logger
log = logging.getLogger("deluge")

class ToolBar:
    def __init__(self, window):
        log.debug("ToolBar Init..")
        self.window = window
        
        ### Connect Signals ###
        self.window.main_glade.signal_autoconnect({
            "on_toolbutton_add_clicked": self.on_toolbutton_add_clicked,
            "on_toolbutton_remove_clicked": self.on_toolbutton_remove_clicked,
            "on_toolbutton_clear_clicked": self.on_toolbutton_clear_clicked,
            "on_toolbutton_pause_clicked": self.on_toolbutton_pause_clicked,
            "on_toolbutton_queueup_clicked": \
                                        self.on_toolbutton_queueup_clicked,
            "on_toolbutton_queuedown_clicked": \
                                        self.on_toolbutton_queuedown_clicked,
            "on_toolbutton_preferences_clicked": \
                                        self.on_toolbutton_preferences_clicked,
            "on_toolbutton_plugins_clicked": \
                                        self.on_toolbutton_plugins_clicked,            
        })
        
    ### Callbacks ###
    def on_toolbutton_add_clicked(self, data):
        log.debug("on_toolbutton_add_clicked")
    def on_toolbutton_remove_clicked(self, data):
        log.debug("on_toolbutton_remove_clicked")
    def on_toolbutton_clear_clicked(self, data):
        log.debug("on_toolbutton_clear_clicked")
    def on_toolbutton_pause_clicked(self, data):
        log.debug("on_toolbutton_pause_clicked")
    def on_toolbutton_queueup_clicked(self, data):
        log.debug("on_toolbutton_queueup_clicked")
    def on_toolbutton_queuedown_clicked(self, data):
        log.debug("on_toolbutton_queuedown_clicked")
    def on_toolbutton_preferences_clicked(self, data):
        log.debug("on_toolbutton_preferences_clicked")
    def on_toolbutton_plugins_clicked(self, data):
        log.debug("on_toolbutton_plugins_clicked")

