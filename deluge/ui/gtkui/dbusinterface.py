#
# dbusinterface.py
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
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
# 	Boston, MA  02110-1301, USA.
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
#

#


import sys
import os

# Import DBUS
import dbus, dbus.service

if dbus.version >= (0,41,0) and dbus.version < (0,80,0):
    import dbus.glib
elif dbus.version >= (0,80,0):
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)

import deluge.component as component
import deluge.common
from deluge.log import LOG as log

class DbusInterface(dbus.service.Object, component.Component):
    def __init__(self, args, path="/org/deluge_torrent/Deluge"):
        component.Component.__init__(self, "DbusInterface")
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
                if not deluge.common.is_url(arg) and not deluge.common.is_magnet(arg):
                    new_args.append(os.path.abspath(arg))
                else:
                    new_args.append(arg)
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

    @dbus.service.method("org.deluge_torrent.Deluge", in_signature="as")
    def process_args(self, args):
        """Process arguments sent to already running Deluge"""
        from ipcinterface import process_args
        process_args(args)

