#
# statusbar.py
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

import gtk

import deluge.ui.component as component
import deluge.common
import deluge.ui.client as client
from deluge.log import LOG as log

class StatusBar(component.Component):
    def __init__(self):
        component.Component.__init__(self, "StatusBar")
        self.window = component.get("MainWindow")
        self.statusbar = self.window.main_glade.get_widget("statusbar")
        
        # Add a HBox to the statusbar after removing the initial label widget
        self.hbox = gtk.HBox()
        self.hbox.set_spacing(5)
        frame = self.statusbar.get_children()[0]
        frame.remove(frame.get_children()[0])
        frame.add(self.hbox)
        # Show the not connected status bar
        self.show_not_connected()

    def start(self):
        log.debug("StatusBar start..")
        # Add in images and labels
        self.clear_statusbar()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_NETWORK, gtk.ICON_SIZE_MENU)
        self.hbox.pack_start(image, expand=False, fill=False)
        self.label_connections = gtk.Label()
        self.hbox.pack_start(self.label_connections, expand=False, fill=False)
        image = gtk.Image()
        image.set_from_file(deluge.common.get_pixmap("downloading16.png"))
        self.hbox.pack_start(image, expand=False, fill=False)
        self.label_download_speed = gtk.Label()
        self.hbox.pack_start(self.label_download_speed, 
            expand=False, fill=False)
        image = gtk.Image()
        image.set_from_file(deluge.common.get_pixmap("seeding16.png"))
        self.hbox.pack_start(image, expand=False, fill=False)
        self.label_upload_speed = gtk.Label()
        self.hbox.pack_start(self.label_upload_speed, 
            expand=False, fill=False)
        
        self.statusbar.show_all()
    
    def stop(self):
        # When stopped, we just show the not connected thingy
        self.show_not_connected()
        
    def show_not_connected(self):
        self.clear_statusbar()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_MENU)
        self.hbox.pack_start(image, expand=False, fill=False)
        label = gtk.Label(_("Not Connected"))
        self.hbox.pack_start(label, expand=False, fill=False)
        self.statusbar.show_all()
    
    def add_item(self, image=None, stock=None, text=None):
        """Adds an item to the status bar"""
        # The return tuple.. we return whatever widgets we add
        ret = []
        # Add image from file or stock
        if image != None or stock != None:
            _image = gtk.Image()
            if image != None:
                _image.set_from_file(image)
            if stock != None:
                _image.set_from_stock(stock, gtk.ICON_SIZE_MENU)
            self.hbox.pack_start(_image, expand=False, fill=False)
            ret.append(_image)
            
        # Add text
        if text != None:
            label = gtk.Label(text)
            self.hbox.pack_start(label, expand=False, fill=False)
            ret.append(label)
        
        # Show the widgets
        for widget in ret:
            widget.show()
            
        # Return the widgets
        return tuple(ret)
    
    def remove_item(self, widget):
        """Removes an item from the statusbar"""
        try:
            self.hbox.remove(widget)
        except Exception, e:
            log.debug("Unable to remove widget: %s", e)
            
    def clear_statusbar(self):
        def remove(child):
            self.hbox.remove(child)
        self.hbox.foreach(remove)
        
    def update(self):
        # Set the max connections label
        max_connections = client.get_config_value("max_connections_global")
        if max_connections < 0:
            max_connections = _("Unlimited")
            
        self.label_connections.set_text("%s (%s)" % (
            client.get_num_connections(), max_connections))
        
        # Set the download speed label
        max_download_speed = client.get_config_value("max_download_speed")
        if max_download_speed < 0:
            max_download_speed = _("Unlimited")
        else:
            max_download_speed = "%s %s" % (max_download_speed, _("KiB/s"))
                    
        self.label_download_speed.set_text("%s/s (%s)" % (
            deluge.common.fsize(client.get_download_rate()), 
            max_download_speed))
        
        # Set the upload speed label
        max_upload_speed = client.get_config_value("max_upload_speed")
        if max_upload_speed < 0:
            max_upload_speed = _("Unlimited")
        else:
            max_upload_speed = "%s %s" % (max_upload_speed, _("KiB/s"))
        
        self.label_upload_speed.set_text("%s/s (%s)" % (
            deluge.common.fsize(client.get_upload_rate()), 
            max_upload_speed))

