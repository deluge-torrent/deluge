#
# menubar.py
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

import functions

# Get the logger
log = logging.getLogger("deluge")

class MenuBar:
    def __init__(self, window):
        log.debug("MenuBar init..")
        self.window = window
        # Get the torrent menu from the glade file
        self.torrentmenu = gtk.glade.XML(
                    pkg_resources.resource_filename("deluge.ui.gtkui", 
                                                "glade/torrent_menu.glade"))

        # Attach the torrent_menu to the Torrent file menu
        self.window.main_glade.get_widget("menu_torrent").set_submenu(
                                self.torrentmenu.get_widget("torrent_menu"))

        ### Connect Signals ###
        self.window.main_glade.signal_autoconnect({
            ## File Menu
            "on_menuitem_addtorrent_activate": \
                                        self.on_menuitem_addtorrent_activate,
            "on_menuitem_addurl_activate": self.on_menuitem_addurl_activate,
            "on_menuitem_clear_activate": \
                                            self.on_menuitem_clear_activate,
            "on_menuitem_quit_activate": self.on_menuitem_quit_activate,

            ## Edit Menu
            "on_menuitem_preferences_activate": \
                                        self.on_menuitem_preferences_activate,
            "on_menuitem_plugins_activate": self.on_menuitem_plugins_activate,
            
            ## View Menu
            "on_menuitem_toolbar_toggled": self.on_menuitem_toolbar_toggled,
            "on_menuitem_infopane_toggled": self.on_menuitem_infopane_toggled,
            
            ## Help Menu
            "on_menuitem_about_activate": self.on_menuitem_about_activate
        })
        
        self.torrentmenu.signal_autoconnect({
            ## Torrent Menu
            "on_menuitem_pause_activate": self.on_menuitem_pause_activate,
            "on_menuitem_updatetracker_activate": \
                                    self.on_menuitem_updatetracker_activate,
            "on_menuitem_edittrackers_activate": \
                                    self.on_menuitem_edittrackers_activate,
            "on_menuitem_remove_activate": self.on_menuitem_remove_activate,
            "on_menuitem_queuetop_activate": \
                                            self.on_menuitem_queuetop_activate,
            "on_menuitem_queueup_activate": self.on_menuitem_queueup_activate,
            "on_menuitem_queuedown_activate": \
                                        self.on_menuitem_queuedown_activate,
            "on_menuitem_queuebottom_activate": \
                                        self.on_menuitem_queuebottom_activate
        })
        
    ### Callbacks ###
    
    ## File Menu ##
    def on_menuitem_addtorrent_activate(self, data=None):
        log.debug("on_menuitem_addtorrent_activate")
        functions.add_torrent_file()
    def on_menuitem_addurl_activate(self, data=None):
        log.debug("on_menuitem_addurl_activate")
    def on_menuitem_clear_activate(self, data=None):
        log.debug("on_menuitem_clear_activate")
    def on_menuitem_quit_activate(self, data=None):
        log.debug("on_menuitem_quit_activate")
        self.window.quit()
    
    ## Edit Menu ##
    def on_menuitem_preferences_activate(self, data=None):
        log.debug("on_menuitem_preferences_activate")
    def on_menuitem_plugins_activate(self, data=None):
        log.debug("on_menuitem_plugins_activate")

    ## Torrent Menu ##
    def on_menuitem_pause_activate(self, data=None):
        log.debug("on_menuitem_pause_activate")
    def on_menuitem_updatetracker_activate(self, data=None):
        log.debug("on_menuitem_updatetracker_activate")
    def on_menuitem_edittrackers_activate(self, data=None):
        log.debug("on_menuitem_edittrackers_activate")
    def on_menuitem_remove_activate(self, data=None):
        log.debug("on_menuitem_remove_activate")
    def on_menuitem_queuetop_activate(self, data=None):
        log.debug("on_menuitem_queuetop_activate")
    def on_menuitem_queueup_activate(self, data=None):
        log.debug("on_menuitem_queueup_activate")
    def on_menuitem_queuedown_activate(self, data=None):
        log.debug("on_menuitem_queuedown_activate")
    def on_menuitem_queuebottom_activate(self, data=None):
        log.debug("on_menuitem_queuebottom_activate")
        
    ## View Menu ##
    def on_menuitem_toolbar_toggled(self, data=None):
        log.debug("on_menuitem_toolbar_toggled")
    def on_menuitem_infopane_toggled(self, data=None):
        log.debug("on_menuitem_infopane_toggled")
    
    ## Help Menu ##
    def on_menuitem_about_activate(self, data=None):
        log.debug("on_menuitem_about_activate")

