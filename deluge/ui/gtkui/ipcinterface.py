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
# 	Boston, MA    02110-1301, USA.
#


import sys
import os.path
import base64

import deluge.rencode
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
        data = deluge.rencode.loads(data)
        log.debug("Data received: %s", data)
        process_args(data)

class IPCProtocolClient(Protocol):
    def connectionMade(self):
        log.debug("Connection made!")
        self.transport.write(deluge.rencode.dumps(self.factory.args))
        self.transport.loseConnection()
    def connectionLost(self, reason):
        reactor.stop()

class IPCInterface(component.Component):
    def __init__(self, args):
        component.Component.__init__(self, "IPCInterface")
        log.debug("args: %s", args)
        if not os.path.exists(deluge.configmanager.get_config_dir("ipc")):
            os.makedirs(deluge.configmanager.get_config_dir("ipc"))

        socket = os.path.join(deluge.configmanager.get_config_dir("ipc"), "deluge-gtk")

        try:
            self.factory = Factory()
            self.factory.protocol = IPCProtocolServer
            reactor.listenUNIX(socket, self.factory, wantPID=True)
        except twisted.internet.error.CannotListenError, e:
            log.info("Deluge is already running! Sending arguments to running instance..")
            self.factory = ClientFactory()
            self.factory.args = args
            self.factory.protocol = IPCProtocolClient
            reactor.connectUNIX(socket, self.factory, checkPID=True)
            reactor.run()
            sys.exit(0)

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
                client.core.add_torrent_url(arg, None)
        elif deluge.common.is_magnet(arg):
            log.debug("Attempting to add %s from external source..", arg)
            if config["interactive_add"]:
                component.get("AddTorrentDialog").add_from_magnets([arg])
                component.get("AddTorrentDialog").show(config["focus_add_dialog"])
            else:
                client.core.add_torrent_magnets([arg], [])
        else:
            # Just a file
            log.debug("Attempting to add %s from external source..",
                os.path.abspath(arg))
            if config["interactive_add"]:
                component.get("AddTorrentDialog").add_from_files([os.path.abspath(arg)])
                component.get("AddTorrentDialog").show(config["focus_add_dialog"])
            else:
                path = os.path.abspath(arg)
                client.core.add_torrent_file(os.path.split(path)[-1], base64.encodestring(open(path).read()), None)
