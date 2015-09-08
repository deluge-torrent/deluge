# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import base64
import logging
import os
import sys
from glob import glob
from tempfile import mkstemp
from urllib import url2pathname
from urlparse import urlparse

import twisted.internet.error
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory, Factory, Protocol

import deluge.component as component
from deluge.common import is_magnet, is_url, windows_check
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.ui.client import client

try:
    import rencode
except ImportError:
    import deluge.rencode as rencode

log = logging.getLogger(__name__)


class IPCProtocolServer(Protocol):
    def dataReceived(self, data):  # NOQA
        config = ConfigManager("gtkui.conf")
        data = rencode.loads(data, decode_utf8=True)
        if not data or config["focus_main_window_on_add"]:
            component.get("MainWindow").present()
        process_args(data)


class IPCProtocolClient(Protocol):
    def connectionMade(self):  # NOQA
        self.transport.write(rencode.dumps(self.factory.args))
        self.transport.loseConnection()

    def connectionLost(self, reason):  # NOQA
        reactor.stop()
        self.factory.stop = True


class IPCClientFactory(ClientFactory):
    protocol = IPCProtocolClient

    def __init__(self):
        self.stop = False

    def clientConnectionFailed(self, connector, reason):  # NOQA
        log.warning("Connection to running instance failed.")
        reactor.stop()


class IPCInterface(component.Component):
    def __init__(self, args):
        component.Component.__init__(self, "IPCInterface")
        ipc_dir = get_config_dir("ipc")
        if not os.path.exists(ipc_dir):
            os.makedirs(ipc_dir)
        socket = os.path.join(ipc_dir, "deluge-gtk")
        if windows_check():
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
            # Find and remove any restart tempfiles
            restart_tempfile = glob(os.path.join(ipc_dir, 'tmp*deluge'))
            for f in restart_tempfile:
                os.remove(f)
            lockfile = socket + ".lock"
            log.debug("Checking if lockfile exists: %s", lockfile)
            if os.path.lexists(lockfile):
                def delete_lockfile():
                    log.debug("Removing lockfile since it's stale.")
                    try:
                        os.remove(lockfile)
                        os.remove(socket)
                    except OSError as ex:
                        log.error("Failed to delete lockfile: %s", ex)

                try:
                    os.kill(int(os.readlink(lockfile)), 0)
                except OSError:
                    delete_lockfile()
                else:
                    if restart_tempfile:
                        log.warning("Found running PID but it is not a Deluge process, removing lockfile...")
                        delete_lockfile()
            try:
                self.factory = Factory()
                self.factory.protocol = IPCProtocolServer
                reactor.listenUNIX(socket, self.factory, wantPID=True)
            except twisted.internet.error.CannotListenError as ex:
                log.info("Deluge is already running! Sending arguments to running instance...")
                self.factory = IPCClientFactory()
                self.factory.args = args
                reactor.connectUNIX(socket, self.factory, checkPID=True)
                reactor.run()
                if self.factory.stop:
                    log.info("Success sending arguments to running Deluge.")
                    from gi.repository import Gdk
                    Gdk.notify_startup_complete()
                    sys.exit(0)
                else:
                    if restart_tempfile:
                        log.error("Deluge restart failed: %s", ex)
                        sys.exit(1)
                    else:
                        log.warning('Restarting Deluge... (%s)', ex)
                        # Create a tempfile to keep track of restart
                        mkstemp('deluge', dir=ipc_dir)
                        os.execv(sys.argv[0], sys.argv)
            else:
                process_args(args)

    def shutdown(self):
        if windows_check():
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

        if is_url(arg):
            log.debug("Attempting to add url (%s) from external source...", arg)
            if config["interactive_add"]:
                component.get("AddTorrentDialog").add_from_url(arg)
                component.get("AddTorrentDialog").show(config["focus_add_dialog"])
            else:
                client.core.add_torrent_url(arg, None)

        elif is_magnet(arg):
            log.debug("Attempting to add magnet (%s) from external source...", arg)
            if config["interactive_add"]:
                component.get("AddTorrentDialog").add_from_magnets([arg])
                component.get("AddTorrentDialog").show(config["focus_add_dialog"])
            else:
                client.core.add_torrent_magnet(arg, {})

        else:
            log.debug("Attempting to add file (%s) from external source...", arg)
            if urlparse(arg).scheme == "file":
                arg = url2pathname(urlparse(arg).path)
            path = os.path.abspath(arg)

            if not os.path.exists(path):
                log.error("No such file: %s", path)
                continue

            if config["interactive_add"]:
                component.get("AddTorrentDialog").add_from_files([path])
                component.get("AddTorrentDialog").show(config["focus_add_dialog"])
            else:
                client.core.add_torrent_file(os.path.split(path)[-1],
                                             base64.encodestring(open(path, "rb").read()), None)
