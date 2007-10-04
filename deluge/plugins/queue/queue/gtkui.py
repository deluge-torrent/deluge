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

import dbus
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import pkg_resources
import gtk.glade
import gettext
import locale
from deluge.log import LOG as log

class GtkUI:
    def __init__(self, plugin_manager):
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
        log.debug("Queue GtkUI plugin initalized..")
        self.plugin = plugin_manager
        # Get a reference to the core portion of the plugin
        bus = dbus.SessionBus()
        proxy = bus.get_object("org.deluge_torrent.Deluge", 
                               "/org/deluge_torrent/Plugin/Queue")
        self.core = dbus.Interface(proxy, "org.deluge_torrent.Deluge.Queue")
        
        # Get the queue menu from the glade file
        menu_glade = gtk.glade.XML(pkg_resources.resource_filename("queue", 
                                                    "glade/queuemenu.glade"))
        
        menu_glade.signal_autoconnect({
            "on_menuitem_queuetop_activate": \
                                            self.on_menuitem_queuetop_activate,
            "on_menuitem_queueup_activate": self.on_menuitem_queueup_activate,
            "on_menuitem_queuedown_activate": \
                                        self.on_menuitem_queuedown_activate,
            "on_menuitem_queuebottom_activate": \
                                        self.on_menuitem_queuebottom_activate
        })
        
        menu = menu_glade.get_widget("menu_queue")
        
        # Connect to the 'torrent_queue_changed' signal
        self.core.connect_to_signal("torrent_queue_changed", 
                                        self.torrent_queue_changed_signal)
        
        # Get the torrentview component from the plugin manager
        self.torrentview = self.plugin.get_torrentview()
        # Add the '#' column at the first position
        self.torrentview.add_text_column("#", 
                                        col_type=int,
                                        position=0, 
                                        status_field=["queue"])
        # Update the new column right away
        self.torrentview.update(["#"])
        
        # Add a toolbar buttons
        self.plugin.get_toolbar().add_separator()
        self.plugin.get_toolbar().add_toolbutton(stock="gtk-go-up", 
                                    label=_("Queue Up"), 
                                    tooltip=_("Queue selected torrents up"),
                                    callback=self.on_toolbutton_queueup_clicked)

        self.plugin.get_toolbar().add_toolbutton(stock="gtk-go-down", 
                                label=_("Queue Down"), 
                                tooltip=_("Queue selected torrents down"),
                                callback=self.on_toolbutton_queuedown_clicked)
                                
        # Add the queue menu to the torrent menu
        queue_menuitem = gtk.ImageMenuItem("Queue")
        queue_image = gtk.Image()
        queue_image.set_from_stock(gtk.STOCK_SORT_ASCENDING, gtk.ICON_SIZE_MENU)
        queue_menuitem.set_image(queue_image)
        queue_menuitem.set_submenu(menu)
        queue_menuitem.show_all()
        self.plugin.get_torrentmenu().append(queue_menuitem)
        
    ## Menu callbacks ##
    def on_menuitem_queuetop_activate(self, data=None):
        log.debug("on_menuitem_queuetop_activate")
        # Get the selected torrents
        torrent_ids = self.plugin.get_selected_torrents()
        for torrent_id in torrent_ids:
            self.core.queue_top(torrent_id)
        return
                
    def on_menuitem_queueup_activate(self, data=None):
        log.debug("on_menuitem_queueup_activate")
        # Get the selected torrents
        torrent_ids = self.plugin.get_selected_torrents()
        for torrent_id in torrent_ids:
            self.core.queue_up(torrent_id)
        return
        
    def on_menuitem_queuedown_activate(self, data=None):
        log.debug("on_menuitem_queuedown_activate")
        # Get the selected torrents
        torrent_ids = self.plugin.get_selected_torrents()
        for torrent_id in torrent_ids:
            self.core.queue_down(torrent_id)
        return
                
    def on_menuitem_queuebottom_activate(self, data=None):
        log.debug("on_menuitem_queuebottom_activate")
        # Get the selected torrents
        torrent_ids = self.plugin.get_selected_torrents()
        for torrent_id in torrent_ids:
            self.core.queue_bottom(torrent_id)
        return
        
    ## Toolbutton callbacks ##
    def on_toolbutton_queuedown_clicked(self, widget):
        log.debug("on_toolbutton_queuedown_clicked")
        # Get the selected torrents
        torrent_ids = self.plugin.get_selected_torrents()
        for torrent_id in torrent_ids:
            self.core.queue_down(torrent_id)
        return
        
    def on_toolbutton_queueup_clicked(self, widget):
        log.debug("on_toolbutton_queueup_clicked")    
        # Get the selected torrents
        torrent_ids = self.plugin.get_selected_torrents()
        for torrent_id in torrent_ids:
            self.core.queue_up(torrent_id)
        return
    
    ## Signals ##
    def torrent_queue_changed_signal(self):
        """This function is called whenever we receive a 'torrent_queue_changed'
        signal from the core plugin.
        """
        log.debug("torrent_queue_changed signal received..")
        # We only need to update the queue column
        self.torrentview.update(["#"])
        return

