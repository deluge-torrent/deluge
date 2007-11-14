#
# dbusinterface.py
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

import sys
import os

import gtk
import gobject
# Import DBUS
import dbus, dbus.service

if dbus.version >= (0,41,0) and dbus.version < (0,80,0):
    import dbus.glib
elif dbus.version >= (0,80,0):
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)

import deluge.ui.component as component
import deluge.ui.client as client
import deluge.common
from deluge.log import LOG as log
    
class DbusInterface(dbus.service.Object, component.Component):
    def __init__(self, args, path="/org/deluge_torrent/Deluge"):
        component.Component.__init__(self, "DbusInterface", ["StatusBar"])
        self.queue = []
        self.widgets = None
        # Check to see if the daemon is already running and if not, start it
        bus = dbus.SessionBus()
        obj = bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus")
        iface = dbus.Interface(obj, "org.freedesktop.DBus")
        if iface.NameHasOwner("org.deluge_torrent.Deluge"):
            # Deluge client already running.. Lets exit.
            log.info("Deluge already running..")
            log.debug("args: %s", args)
            # Convert the paths to absolutes
            new_args = []
            for arg in args:
                if not deluge.common.is_url(arg):
                    new_args.append(os.path.abspath(arg))
            args = new_args
            
            # Send the args to the running session
            if args != [] and args != None:
                bus = dbus.SessionBus()
                proxy = bus.get_object("org.deluge_torrent.Deluge", 
                                   "/org/deluge_torrent/Deluge")
                ui = dbus.Interface(proxy, "org.deluge_torrent.Deluge")
                ui.process_args(args)
            # Exit
            log.debug("Exiting..")
            sys.exit(0)

        # Process the args if any
        self.process_args(args)
        # Register Deluge with Dbus
        log.info("Registering with DBUS..")
        bus_name = dbus.service.BusName("org.deluge_torrent.Deluge", 
            bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, path)

    def start(self):
        """Called when we connect to a host"""
        log.debug("DbusInterface start..")
        if len(self.queue) == 0:
            return
        # Make sure status bar info is showing
        self.widgets = None
        self.update_status_bar()
        
    def add_to_queue(self, torrents):
        """Adds the list of torrents to the queue"""
        # Add to the queue while removing duplicates
        self.queue = list(set(self.queue + torrents))
        
        # Update the status bar
        self.update_status_bar()
    
    def update_status_bar(self):
        """Attempts to update status bar"""
        # If there are no queued torrents.. remove statusbar widgets and return
        if len(self.queue) == 0:
            if self.widgets != None:
                for widget in self.widgets:
                    component.get("StatusBar").remove(widget)
            return False
            
        try:
            statusbar = component.get("StatusBar")
        except Exception, e:
            # The statusbar hasn't been loaded yet, so we'll add a timer to
            # update it later.
            gobject.timeout_add(100, self.update_status_bar)
            return False
                
        # Set the label text for statusbar
        if len(self.queue) > 1:
            label = str(len(self.queue)) + _(" Torrents Queued")
        else:
            label = str(len(self.queue)) + _(" Torrent Queued")
        
        # Add the statusbar items if needed, or just modify the label if they
        # have already been added.
        if self.widgets == None:
            self.widgets = component.get("StatusBar").add_item(
                stock=gtk.STOCK_SORT_DESCENDING, 
                text=label)
        else:
            self.widgets[1].set_text(label)

        # We return False so the timer stops
        return False
                         
    @dbus.service.method("org.deluge_torrent.Deluge", in_signature="as")
    def process_args(self, args):
        """Process arguments sent to already running Deluge"""
        # Pythonize the values from Dbus
        dbus_args = args
        args = []
        for arg in dbus_args:
            args.append(str(arg))
        log.debug("Processing args from other process: %s", args)
        if not client.connected():
            # We're not connected so add these to the queue
            log.debug("Not connected to host.. Adding to queue.")
            self.add_to_queue(args)
            return
            
        for arg in args:
            if deluge.common.is_url(arg):
                log.debug("Attempting to add %s from external source..",
                    arg)
                client.add_torrent_url(arg)
            else:
                # Just a file
                log.debug("Attempting to add %s from external source..", 
                    os.path.abspath(arg))
                client.add_torrent_file([os.path.abspath(arg)])
            
