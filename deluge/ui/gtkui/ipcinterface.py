#
# ipcinterface.py
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
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
import os.path

import deluge.component as component
from deluge.ui.client import aclient as client
import deluge.common
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

class IPCInterface(component.Component):
    def __init__(self, args):
        component.Component.__init__(self, "IPCInterface")

        if deluge.common.windows_check():
            # If we're on windows we need to check the global mutex to see if deluge is
            # already running.
            import win32event
            import win32api
            import winerror
            self.mutex = win32event.CreateMutex(None, False, "deluge")
            if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                # We already have a running session, send a XMLRPC to the existing session
                config = ConfigManager("gtkui.conf")
                uri = "http://127.0.0.1:" + str(config["signal_port"])
                import deluge.xmlrpclib as xmlrpclib
                rpc = xmlrpclib.ServerProxy(uri, allow_none=True)
                rpc.emit_signal("args_from_external", args)
                sys.exit(0)
            else:
                process_args(args)
        else:
            try:
                import dbusinterface
                self.dbusinterface = dbusinterface.DbusInterface(args)
            except Exception, e:
                log.warning("Unable to start DBUS component: %s", e)

    def shutdown(self):
        if deluge.common.windows_check():
            import win32api
            win32api.CloseHandle(self.mutex)

def process_args(args):
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
        component.get("QueuedTorrents").add_to_queue(args)
        return
    config = ConfigManager("gtkui.conf")
    for arg in args:
        if not arg:
            continue
        log.debug("arg: %s", arg)
        if deluge.common.is_url(arg):
            log.debug("Attempting to add %s from external source..",
                arg)
            if config["interactive_add"]:
                component.get("AddTorrentDialog").add_from_url(arg)
                component.get("AddTorrentDialog").show(config["focus_add_dialog"])
            else:
                client.add_torrent_url(arg, None)
        elif deluge.common.is_magnet(arg):
            log.debug("Attempting to add %s from external source..", arg)
            if config["interactive_add"]:
                component.get("AddTorrentDialog").add_from_magnets([arg])
                component.get("AddTorrentDialog").show(config["focus_add_dialog"])
            else:
                client.add_torrent_magnets([arg], [])
        else:
            # Just a file
            log.debug("Attempting to add %s from external source..",
                os.path.abspath(arg))
            if config["interactive_add"]:
                component.get("AddTorrentDialog").add_from_files([os.path.abspath(arg)])
                component.get("AddTorrentDialog").show(config["focus_add_dialog"])
            else:
                client.add_torrent_file([os.path.abspath(arg)])
