#
# ipcinterface.py
#
# Copyright (C) 2008-2009 Andrew Resch <andrewresch@gmail.com>
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
import base64

try:
    import rencode
except ImportError:
    import deluge.rencode as rencode
    
import deluge.component as component
from deluge.ui.client import client
import deluge.common
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

from twisted.internet.protocol import Factory, Protocol, ClientFactory
from twisted.internet import reactor
import twisted.internet.error

class IPCProtocolServer(Protocol):
    def dataReceived(self, data):
        data = rencode.loads(data)
        process_args(data)

class IPCProtocolClient(Protocol):
    def connectionMade(self):
        self.transport.write(rencode.dumps(self.factory.args))
        self.transport.loseConnection()
        
    def connectionLost(self, reason):
        reactor.stop()
        self.factory.stop = True
        
class IPCClientFactory(ClientFactory):
    protocol = IPCProtocolClient

    def __init__(self, args, connect_failed):
        self.stop = False
        self.args = args
        self.connect_failed = connect_failed
        
    def clientConnectionFailed(self, connector, reason):
        log.info("Connection to running instance failed.  Starting new one..")
        reactor.stop()
    
class IPCInterface(component.Component):
    def __init__(self, args):
        component.Component.__init__(self, "IPCInterface")
        if not os.path.exists(deluge.configmanager.get_config_dir("ipc")):
            os.makedirs(deluge.configmanager.get_config_dir("ipc"))

        socket = os.path.join(deluge.configmanager.get_config_dir("ipc"), "deluge-gtk")

        if deluge.common.windows_check():
            # If we're on windows we need to check the global mutex to see if deluge is
            # already running.
            import win32event
            import win32api
            import winerror
            self.mutex = win32event.CreateMutex(None, False, "deluge")
            if win32api.GetLastError() != winerror.ERROR_ALREADY_EXISTS:
                # Create listen socket
                self.factory = Factory()
                self.factory.protocol = IPCProtocolServer
                import random
                port = random.randrange(20000, 65535)
                reactor.listenTCP(port, self.factory)
                # Store the port number in the socket file
                open(socket, "w").write(str(port))
                # We need to process any args when starting this process
                process_args(args)
            else:
                # Send to existing deluge process
                port = int(open(socket, "r").readline())
                self.factory = ClientFactory()
                self.factory.args = args
                self.factory.protocol = IPCProtocolClient
                reactor.connectTCP("127.0.0.1", port, self.factory)
                reactor.run()
                sys.exit(0)
        else:
            lockfile = socket + ".lock"
            log.debug("Checking if lockfile exists: %s", lockfile)
            if os.path.lexists(lockfile):
                try:
                    os.kill(int(os.readlink(lockfile)), 0)
                except OSError:
                    log.debug("Removing lockfile since it's stale.")
                    try:
                        os.remove(lockfile)
                        os.remove(socket)
                    except Exception, e:
                        log.error("Problem deleting lockfile or socket file!")
                        log.exception(e)
            try:
                self.factory = Factory()
                self.factory.protocol = IPCProtocolServer
                reactor.listenUNIX(socket, self.factory, wantPID=True)
            except twisted.internet.error.CannotListenError, e:
                log.info("Deluge is already running! Sending arguments to running instance..")
                self.factory = IPCClientFactory(args, self.connect_failed)
                reactor.connectUNIX(socket, self.factory, checkPID=True)
                reactor.run()
                if self.factory.stop:
                    import gtk
                    gtk.gdk.notify_startup_complete()
                    sys.exit(0)
                else:
                    self.connect_failed(args)
            else:
                process_args(args)

    def connect_failed(self, args):
        # This gets called when we're unable to do a connectUNIX to the ipc
        # socket.  We'll delete the lock and socket files and start up Deluge.
        #reactor.stop()
        socket = os.path.join(deluge.configmanager.get_config_dir("ipc"), "deluge-gtk")
        if os.path.exists(socket):
            try:
                os.remove(socket)
            except Exception, e:
                log.error("Unable to remove socket file: %s", e)
                
        lock = socket + ".lock"
        if os.path.lexists(lock):
            try:
                os.remove(lock)
            except Exception, e:
                log.error("Unable to remove lock file: %s", e)
        try:
            self.factory = Factory()
            self.factory.protocol = IPCProtocolServer
            reactor.listenUNIX(socket, self.factory, wantPID=True)
        except Exception, e:
            log.error("Unable to start IPC listening socket: %s", e)
        finally:
            process_args(args)
        
    def shutdown(self):
        if deluge.common.windows_check():
            import win32api
            win32api.CloseHandle(self.mutex)

def process_args(args):
    """Process arguments sent to already running Deluge"""
    # Make sure args is a list
    args = list(args)
    log.debug("Processing args from other process: %s", args)
    if not client.connected():
        # We're not connected so add these to the queue
        log.debug("Not connected to host.. Adding to queue.")
        component.get("QueuedTorrents").add_to_queue(args)
        return
    config = ConfigManager("gtkui.conf")
    for arg in args:
        if not arg.strip():
            continue
        log.debug("arg: %s", arg)
        if deluge.common.is_url(arg):
            log.debug("Attempting to add %s from external source..",
                arg)
            if config["interactive_add"]:
                component.get("AddTorrentDialog").add_from_url(arg)
                component.get("AddTorrentDialog").show(config["focus_add_dialog"])
            else:
                client.core.add_torrent_url(arg, None)
        elif deluge.common.is_magnet(arg):
            log.debug("Attempting to add %s from external source..", arg)
            if config["interactive_add"]:
                component.get("AddTorrentDialog").add_from_magnets([arg])
                component.get("AddTorrentDialog").show(config["focus_add_dialog"])
            else:
                client.core.add_torrent_magnet(arg, {})
        else:
            # Just a file
            path = os.path.abspath(arg.replace('file://', '', 1))
            log.debug("Attempting to add %s from external source..", path)
            if not os.path.exists(path):
                log.error("No such file: %s", path)
                continue

            if config["interactive_add"]:
                component.get("AddTorrentDialog").add_from_files([path])
                component.get("AddTorrentDialog").show(config["focus_add_dialog"])
            else:
                client.core.add_torrent_file(os.path.split(path)[-1], base64.encodestring(open(path, "rb").read()), None)
