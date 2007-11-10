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

import pkg_resources
import gtk.glade
from deluge.log import LOG as log
import ui

class GtkUI(ui.UI):
    def __init__(self, plugin_api, plugin_name):
        log.debug("Calling UI init")
        # Call UI constructor
        ui.UI.__init__(self, plugin_api, plugin_name)
        log.debug("Queue GtkUI plugin initalized..")
    
    def load_interface(self):
        # Get the queue menu from the glade file
        menu_glade = gtk.glade.XML(pkg_resources.resource_filename("queue", 
                                                    "glade/queuemenu.glade"))
        
        prefs_glade = gtk.glade.XML(pkg_resources.resource_filename("queue",
            "glade/queueprefs.glade"))
            
        menu_glade.signal_autoconnect({
            "on_menuitem_queuetop_activate": \
                                            self.on_queuetop_activate,
            "on_menuitem_queueup_activate": self.on_queueup_activate,
            "on_menuitem_queuedown_activate": \
                                        self.on_queuedown_activate,
            "on_menuitem_queuebottom_activate": \
                                        self.on_queuebottom_activate
        })
        
        menu = menu_glade.get_widget("menu_queue")
        
        # Connect to the 'torrent_queue_changed' signal
        #self.core.connect_to_signal("torrent_queue_changed", 
        #                                self.torrent_queue_changed_signal)

        # Add the '#' column at the first position
        self.plugin.add_torrentview_text_column("#",
                                        col_type=int,
                                        position=0, 
                                        status_field=["queue"])
        # Update the new column right away
        self.update()
        
        # Add a toolbar buttons
        self.toolbar_sep = self.plugin.add_toolbar_separator()
        self.toolbutton_up = self.plugin.add_toolbar_button(
                                    stock="gtk-go-up", 
                                    label=_("Queue Up"), 
                                    tooltip=_("Queue selected torrents up"),
                                    callback=self.on_queueup_activate)

        self.toolbutton_down = self.plugin.add_toolbar_button(
                                stock="gtk-go-down", 
                                label=_("Queue Down"), 
                                tooltip=_("Queue selected torrents down"),
                                callback=self.on_queuedown_activate)
                                
        # Add a separator before menu
        self.menu_sep = self.plugin.add_torrentmenu_separator()
        
        # Add the queue menu to the torrent menu
        self.queue_menuitem = gtk.ImageMenuItem("Queue")
        queue_image = gtk.Image()
        queue_image.set_from_stock(gtk.STOCK_SORT_ASCENDING, gtk.ICON_SIZE_MENU)
        self.queue_menuitem.set_image(queue_image)
        self.queue_menuitem.set_submenu(menu)
        self.queue_menuitem.show_all()
        self.plugin.add_torrentmenu_menu(self.queue_menuitem)
        
        # Add preferences page
        self.queue_pref_page = \
            prefs_glade.get_widget("queue_prefs_box")
        self.plugin.add_preferences_page("Queue", self.queue_pref_page)
    
    def unload_interface(self):
        self.plugin.remove_torrentmenu_item(self.menu_sep)
        self.plugin.remove_torrentmenu_item(self.queue_menuitem)
        self.plugin.remove_toolbar_button(self.toolbar_sep)
        self.plugin.remove_toolbar_button(self.toolbutton_up)
        self.plugin.remove_toolbar_button(self.toolbutton_down)
        self.plugin.remove_torrentview_column("#")
        self.plugin.remove_preferences_page("Queue")
        
    def update(self):
        self.plugin.update_torrent_view(["#"])
