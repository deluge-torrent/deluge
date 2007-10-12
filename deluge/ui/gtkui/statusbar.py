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

import deluge.common
import deluge.ui.functions as functions

class StatusBar:
    def __init__(self, window):
        self.window = window
        self.statusbar = self.window.main_glade.get_widget("statusbar")
        self.core = functions.get_core()
        
        # Add a HBox to the statusbar after removing the initial label widget
        self.hbox = gtk.HBox()
        self.hbox.set_spacing(5)
        frame = self.statusbar.get_children()[0]
        frame.remove(frame.get_children()[0])
        frame.add(self.hbox)
        
        # Add in images and labels
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
        
        # Update once before showing
        self.update()
        self.statusbar.show_all()

    def update(self):
        # Set the max connections label
        max_connections = functions.get_config_value("max_connections_global")
        if max_connections < 0:
            max_connections = _("Unlimited")
            
        self.label_connections.set_text("%s (%s)" % (
            self.core.get_num_connections(), max_connections))
        
        # Set the download speed label
        max_download_speed = functions.get_config_value("max_download_speed")
        if max_download_speed < 0:
            max_download_speed = _("Unlimited")
        else:
            max_download_speed = "%s %s" % (max_download_speed, _("KiB/s"))
                    
        self.label_download_speed.set_text("%s/s (%s)" % (
            deluge.common.fsize(self.core.get_download_rate()), 
            max_download_speed))
        
        # Set the upload speed label
        max_upload_speed = functions.get_config_value("max_upload_speed")
        if max_upload_speed < 0:
            max_upload_speed = _("Unlimited")
        else:
            max_upload_speed = "%s %s" % (max_upload_speed, _("KiB/s"))
        
        self.label_upload_speed.set_text("%s/s (%s)" % (
            deluge.common.fsize(self.core.get_upload_rate()), 
            max_upload_speed))
