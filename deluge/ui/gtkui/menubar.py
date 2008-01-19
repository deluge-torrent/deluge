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

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
import pkg_resources

import deluge.component as component
import deluge.ui.client as client
import deluge.common as common

from deluge.log import LOG as log

class MenuBar(component.Component):
    def __init__(self):
        log.debug("MenuBar init..")
        component.Component.__init__(self, "MenuBar")
        self.window = component.get("MainWindow")
        # Get the torrent menu from the glade file
        self.torrentmenu_glade = gtk.glade.XML(
                    pkg_resources.resource_filename("deluge.ui.gtkui", 
                                                "glade/torrent_menu.glade"))

        self.torrentmenu = self.torrentmenu_glade.get_widget("torrent_menu")
        self.menu_torrent = self.window.main_glade.get_widget("menu_torrent")
        
        # Attach the torrent_menu to the Torrent file menu
        self.menu_torrent.set_submenu(self.torrentmenu)

        ### Connect Signals ###
        self.window.main_glade.signal_autoconnect({
            ## File Menu
            "on_menuitem_addtorrent_activate": \
                                        self.on_menuitem_addtorrent_activate,
            "on_menuitem_quitdaemon_activate": \
                                        self.on_menuitem_quitdaemon_activate,
            "on_menuitem_quit_activate": self.on_menuitem_quit_activate,

            ## Edit Menu
            "on_menuitem_preferences_activate": \
                                        self.on_menuitem_preferences_activate,
            "on_menuitem_connectionmanager_activate": \
                self.on_menuitem_connectionmanager_activate,
            
            ## View Menu
            "on_menuitem_toolbar_toggled": self.on_menuitem_toolbar_toggled,
            "on_menuitem_sidebar_toggled": self.on_menuitem_sidebar_toggled,
            "on_menuitem_infopane_toggled": self.on_menuitem_infopane_toggled,
            
            ## Help Menu
            "on_menuitem_homepage_activate": self.on_menuitem_homepage_activate,
            "on_menuitem_faq_activate": self.on_menuitem_faq_activate,
            "on_menuitem_community_activate": \
                self.on_menuitem_community_activate,
            "on_menuitem_about_activate": self.on_menuitem_about_activate
        })
        
        self.torrentmenu_glade.signal_autoconnect({
            ## Torrent Menu
            "on_menuitem_pause_activate": self.on_menuitem_pause_activate,
            "on_menuitem_resume_activate": self.on_menuitem_resume_activate,
            "on_menuitem_updatetracker_activate": \
                                    self.on_menuitem_updatetracker_activate,
            "on_menuitem_edittrackers_activate": \
                                    self.on_menuitem_edittrackers_activate,
            "on_menuitem_remove_activate": self.on_menuitem_remove_activate,
            "on_menuitem_recheck_activate": self.on_menuitem_recheck_activate,
            "on_menuitem_open_folder": self.on_menuitem_open_folder_activate
        })
        
        self.change_sensitivity = [
            "menuitem_addtorrent"
        ]
    
    def start(self):
        for widget in self.change_sensitivity:
            self.window.main_glade.get_widget(widget).set_sensitive(True)

        # Hide the Open Folder menuitem and separator if not connected to a 
        # localhost.
        non_remote_items = [
            "menuitem_open_folder",
            "separator4"
        ]
        if not client.is_localhost():
            for widget in non_remote_items:
                self.torrentmenu_glade.get_widget(widget).hide()
                self.torrentmenu_glade.get_widget(widget).set_no_show_all(True)
        else:
            for widget in non_remote_items:
                self.torrentmenu_glade.get_widget(widget).set_no_show_all(False)
            
        # Show the Torrent menu because we're connected to a host
        self.menu_torrent.show()

        self.window.main_glade.get_widget("separatormenuitem").show()
        self.window.main_glade.get_widget("menuitem_quitdaemon").show()
        
    def stop(self):
        for widget in self.change_sensitivity:
            self.window.main_glade.get_widget(widget).set_sensitive(False)

        # Hide the Torrent menu
        self.menu_torrent.hide()

        self.window.main_glade.get_widget("separatormenuitem").hide()
        self.window.main_glade.get_widget("menuitem_quitdaemon").hide()

    def add_torrentmenu_separator(self):
        sep = gtk.SeparatorMenuItem()
        self.torrentmenu.append(sep)
        sep.show()
        return sep
    
    ### Callbacks ###
    
    ## File Menu ##
    def on_menuitem_addtorrent_activate(self, data=None):
        log.debug("on_menuitem_addtorrent_activate")
        from addtorrentdialog import AddTorrentDialog
        #client.add_torrent_file(AddTorrentDialog().run())
        AddTorrentDialog().show()
        
    def on_menuitem_quitdaemon_activate(self, data=None):
        log.debug("on_menuitem_quitdaemon_activate")
        # Tell the core to shutdown
        self.window.quit()
        client.shutdown()
        
    def on_menuitem_quit_activate(self, data=None):
        log.debug("on_menuitem_quit_activate")
        self.window.quit()
    
    ## Edit Menu ##
    def on_menuitem_preferences_activate(self, data=None):
        log.debug("on_menuitem_preferences_activate")
        component.get("Preferences").show()

    def on_menuitem_connectionmanager_activate(self, data=None):
        log.debug("on_menuitem_connectionmanager_activate")
        component.get("ConnectionManager").show()
        
    ## Torrent Menu ##
    def on_menuitem_pause_activate(self, data=None):
        log.debug("on_menuitem_pause_activate")
        client.pause_torrent(
            component.get("TorrentView").get_selected_torrents())
    
    def on_menuitem_resume_activate(self, data=None):
        log.debug("on_menuitem_resume_activate")
        client.resume_torrent(
            component.get("TorrentView").get_selected_torrents())
        
    def on_menuitem_updatetracker_activate(self, data=None):
        log.debug("on_menuitem_updatetracker_activate")
        client.force_reannounce(
            component.get("TorrentView").get_selected_torrents())    
        
    def on_menuitem_edittrackers_activate(self, data=None):
        log.debug("on_menuitem_edittrackers_activate")
        from edittrackersdialog import EditTrackersDialog
        dialog = EditTrackersDialog(
            component.get("TorrentView").get_selected_torrent(), 
            component.get("MainWindow").window)
        dialog.run()
        
    def on_menuitem_remove_activate(self, data=None):
        log.debug("on_menuitem_remove_activate")
        from removetorrentdialog import RemoveTorrentDialog
        RemoveTorrentDialog(
            component.get("TorrentView").get_selected_torrents()).run()
        #client.remove_torrent(
         #   component.get("TorrentView").get_selected_torrents())

    def on_menuitem_recheck_activate(self, data=None):
        log.debug("on_menuitem_recheck_activate")
        client.force_recheck(
            component.get("TorrentView").get_selected_torrents())
    
    def on_menuitem_open_folder_activate(self, data=None):
        log.debug("on_menuitem_open_folder")

    ## View Menu ##
    def on_menuitem_toolbar_toggled(self, value):
        log.debug("on_menuitem_toolbar_toggled")
        component.get("ToolBar").visible(value.get_active())

    def on_menuitem_sidebar_toggled(self, value):
        log.debug("on_menuitem_sidebar_toggled")
        component.get("SideBar").visible(value.get_active())
                
    def on_menuitem_infopane_toggled(self, value):
        log.debug("on_menuitem_infopane_toggled")
        component.get("TorrentDetails").visible(value.get_active())
    
    ## Help Menu ##
    def on_menuitem_homepage_activate(self, data=None):
        log.debug("on_menuitem_homepage_activate")
        common.open_url_in_browser("http://deluge-torrent.org")

    def on_menuitem_faq_activate(self, data=None):
        log.debug("on_menuitem_faq_activate")
        common.open_url_in_browser("http://deluge-torrent.org/faq.php")

    def on_menuitem_community_activate(self, data=None):
        log.debug("on_menuitem_community_activate")
        common.open_url_in_browser("http://forum.deluge-torrent.org/")

    def on_menuitem_about_activate(self, data=None):
        log.debug("on_menuitem_about_activate")
        from aboutdialog import AboutDialog
        AboutDialog().run()

