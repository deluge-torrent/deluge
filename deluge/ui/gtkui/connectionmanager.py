#
# connectionmanager.py
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
import gobject
import socket

import deluge.xmlrpclib as xmlrpclib
import deluge.common
import deluge.ui.client as client
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

DEFAULT_CONFIG = {
    "hosts": ["localhost:58846"]
}

class ConnectionManager:
    def __init__(self, window):
        # Get the glade file for the connection manager
        self.glade = gtk.glade.XML(
                    pkg_resources.resource_filename("deluge.ui.gtkui", 
                                            "glade/connection_manager.glade"))
    
        self.window = window
        self.config = ConfigManager("hostlist.conf", DEFAULT_CONFIG)
        self.connection_manager = self.glade.get_widget("connection_manager")
        self.hostlist = self.glade.get_widget("hostlist")
        self.connection_manager.set_icon(deluge.common.get_logo(16))
        
        self.glade.get_widget("image1").set_from_pixbuf(
            deluge.common.get_logo(32))
        
        self.liststore = gtk.ListStore(gtk.gdk.Pixbuf, str)

        # Fill in hosts from config file
        for host in self.config["hosts"]:
            row = self.liststore.append()
            self.liststore.set_value(row, 1, host)
        
        # Setup host list treeview
        self.hostlist.set_model(self.liststore)
        render = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn("Status", render, pixbuf=0)
        self.hostlist.append_column(column)
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Host", render, text=1)
        self.hostlist.append_column(column)
        
        self.glade.signal_autoconnect({
            "on_button_addhost_clicked": self.on_button_addhost_clicked,
            "on_button_removehost_clicked": self.on_button_removehost_clicked,
            "on_button_startdaemon_clicked": \
                self.on_button_startdaemon_clicked,
            "on_button_cancel_clicked": self.on_button_cancel_clicked,
            "on_button_connect_clicked": self.on_button_connect_clicked,
        })
        
        self.connection_manager.connect("delete-event", self.on_delete_event)
        
    def show(self):
        self.update_timer = gobject.timeout_add(5000, self.update)
        self.update()
        self.connection_manager.show_all()
        
    def hide(self):
        self.connection_manager.hide()
        gobject.source_remove(self.update_timer)

    def update(self):
        """Updates the host status"""
        def update_row(model=None, path=None, row=None, columns=None):
            uri = model.get_value(row, 1)
            uri = "http://" + uri
            online = True
            host = None
            try:
                host = xmlrpclib.ServerProxy(uri)
                host.ping()
            except socket.error:
                print "socket.error!"
                online = False
            
            print "online: ", online
            del host

            if online:
                image = gtk.STOCK_YES
            else:
                image = gtk.STOCK_NO

            pixbuf = self.connection_manager.render_icon(
                image, gtk.ICON_SIZE_MENU)
                
            model.set_value(row, 0, pixbuf)
            
        self.liststore.foreach(update_row)
        return True
        
    def save(self):
        """Save the current host list to file"""
        def append_row(model=None, path=None, row=None, columns=None):
            hostlist.append(model.get_value(row, 1))
        
        hostlist = []
        self.liststore.foreach(append_row, hostlist)
        self.config["hosts"] = hostlist
        self.config.save()
        
    ## Callbacks
    def on_delete_event(self, widget, event):
        self.hide()
        return True
        
    def on_button_addhost_clicked(self, widget):
        log.debug("on_button_addhost_clicked")
        dialog = self.glade.get_widget("addhost_dialog")
        dialog.set_icon(deluge.common.get_logo(16))
        hostname_entry = self.glade.get_widget("entry_hostname")
        port_spinbutton = self.glade.get_widget("spinbutton_port")
        response = dialog.run()
        if response == 1:
            # We add the host
            hostname = hostname_entry.get_text()
            if hostname.startswith("http://"):
                hostname = hostname[7:]

            # Check to make sure the hostname is at least 1 character long
            if len(hostname) < 1:
                dialog.hide()
                return
            
            # Get the port and concatenate the hostname string                
            port = port_spinbutton.get_value_as_int()
            hostname = hostname + ":" + str(port)
            row = self.liststore.append()
            self.liststore.set_value(row, 1, hostname)
            # Save the host list to file
            self.save()
                    
        dialog.hide()

    def on_button_removehost_clicked(self, widget):
        log.debug("on_button_removehost_clicked")
        # Get the selected rows
        paths = self.hostlist.get_selection().get_selected_rows()[1]
        for path in paths:
            self.liststore.remove(self.liststore.get_iter(path))
        
        # Save the host list
        self.save()
        
    def on_button_startdaemon_clicked(self, widget):
        log.debug("on_button_startdaemon_clicked")
        
    def on_button_cancel_clicked(self, widget):
        log.debug("on_button_cancel_clicked")
        self.hide()

    def on_button_connect_clicked(self, widget):
        log.debug("on_button_connect_clicked")
        paths = self.hostlist.get_selection().get_selected_rows()[1]
        row = self.liststore.get_iter(paths[0])
        uri = self.liststore.get_value(row, 1)
        uri = "http://" + uri
        client.set_core_uri(uri)
        self.window.start()
        self.hide()
