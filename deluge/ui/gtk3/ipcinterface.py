# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os
import sys
from base64 import b64encode
from glob import glob
from tempfile import mkstemp

import rencode
import twisted.internet.error
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory, Factory, Protocol, connectionDone

import deluge.component as component
from deluge.common import decode_bytes, is_magnet, is_url, windows_check
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.ui.client import client

try:
    from urllib.parse import urlparse
    from urllib.request import url2pathname
except ImportError:
    # PY2 fallback
    from urllib import url2pathname  # pylint: disable=ungrouped-imports
    from urlparse import urlparse  # pylint: disable=ungrouped-imports

log = logging.getLogger(__name__)


class IPCProtocolServer(Protocol):
    def __init__(self):
        pass

    def dataReceived(self, data):  # NOQA: N802
        config = ConfigManager('gtk3ui.conf')
        data = rencode.loads(data, decode_utf8=True)
        if not data or config['focus_main_window_on_add']:
            component.get('MainWindow').present()
        process_args(data)


class IPCProtocolClient(Protocol):
    def __init__(self):
        pass

    def connectionMade(self):  # NOQA: N802
        self.transport.write(rencode.dumps(self.factory.args))
        self.transport.loseConnection()

    def connectionLost(self, reason=connectionDone):  # NOQA: N802
        reactor.stop()
        self.factory.stop = True


class IPCClientFactory(ClientFactory):
    protocol = IPCProtocolClient

    def __init__(self):
        self.stop = False

    def clientConnectionFailed(self, connector, reason):  # NOQA: N802
        log.warning('Connection to running instance failed.')
        reactor.stop()


class IPCInterface(component.Component):
    def __init__(self, args):
        component.Component.__init__(self, 'IPCInterface')
        self.listener = None
        ipc_dir = get_config_dir('ipc')
        if not os.path.exists(ipc_dir):
            os.makedirs(ipc_dir)
        socket = os.path.join(ipc_dir, 'deluge-gtk')
        if windows_check():
            # If we're on windows we need to check the global mutex to see if deluge is
            # already running.
            import win32api
            import win32event
            import winerror

            self.mutex = win32event.CreateMutex(None, False, 'deluge')
            if win32api.GetLastError() != winerror.ERROR_ALREADY_EXISTS:
                # Create listen socket
                self.factory = Factory()
                self.factory.protocol = IPCProtocolServer
                import random

                port = random.randrange(20000, 65535)
                self.listener = reactor.listenTCP(port, self.factory)
                # Store the port number in the socket file
                with open(socket, 'w') as _file:
                    _file.write(str(port))
                # We need to process any args when starting this process
                process_args(args)
            else:
                # Send to existing deluge process
                with open(socket) as _file:
                    port = int(_file.readline())
                self.factory = ClientFactory()
                self.factory.args = args
                self.factory.protocol = IPCProtocolClient
                reactor.connectTCP('127.0.0.1', port, self.factory)
                reactor.run()
                sys.exit(0)
        else:
            # Find and remove any restart tempfiles
            restart_tempfile = glob(os.path.join(ipc_dir, 'restart.*'))
            for f in restart_tempfile:
                os.remove(f)
            lockfile = socket + '.lock'
            log.debug('Checking if lockfile exists: %s', lockfile)
            if os.path.lexists(lockfile):

                def delete_lockfile():
                    log.debug('Delete stale lockfile.')
                    try:
                        os.remove(lockfile)
                        os.remove(socket)
                    except OSError as ex:
                        log.error('Failed to delete lockfile: %s', ex)

                try:
                    os.kill(int(os.readlink(lockfile)), 0)
                except OSError:
                    delete_lockfile()
                else:
                    if restart_tempfile:
                        log.warning(
                            'Found running PID but it is not a Deluge process, removing lockfile...'
                        )
                        delete_lockfile()
            try:
                self.factory = Factory()
                self.factory.protocol = IPCProtocolServer
                self.listener = reactor.listenUNIX(socket, self.factory, wantPID=True)
            except twisted.internet.error.CannotListenError as ex:
                log.info(
                    'Deluge is already running! Sending arguments to running instance...'
                )
                self.factory = IPCClientFactory()
                self.factory.args = args
                reactor.connectUNIX(socket, self.factory, checkPID=True)
                reactor.run()
                if self.factory.stop:
                    log.info('Success sending arguments to running Deluge.')
                    from gi.repository.Gdk import notify_startup_complete

                    notify_startup_complete()
                    sys.exit(0)
                else:
                    if restart_tempfile:
                        log.error('Deluge restart failed: %s', ex)
                        sys.exit(1)
                    else:
                        log.warning('Restarting Deluge... (%s)', ex)
                        # Create a tempfile to keep track of restart
                        mkstemp(prefix='restart.', dir=ipc_dir)
                        os.execv(sys.argv[0], sys.argv)
            else:
                process_args(args)

    def shutdown(self):
        if windows_check():
            import win32api

            win32api.CloseHandle(self.mutex)
        if self.listener:
            return self.listener.stopListening()


def process_args(args):
    """Process arguments sent to already running Deluge"""
    # Make sure args is a list
    args = list(args)
    log.debug('Processing args from other process: %s', args)
    if not client.connected():
        # We're not connected so add these to the queue
        log.debug('Not connected to host.. Adding to queue.')
        component.get('QueuedTorrents').add_to_queue(args)
        return
    config = ConfigManager('gtk3ui.conf')

    for arg in args:
        if not arg.strip():
            continue
        log.debug('arg: %s', arg)

        if is_url(arg):
            log.debug('Attempting to add url (%s) from external source...', arg)
            if config['interactive_add']:
                component.get('AddTorrentDialog').add_from_url(arg)
                component.get('AddTorrentDialog').show(config['focus_add_dialog'])
            else:
                client.core.add_torrent_url(arg, None)

        elif is_magnet(arg):
            log.debug('Attempting to add magnet (%s) from external source...', arg)
            if config['interactive_add']:
                component.get('AddTorrentDialog').add_from_magnets([arg])
                component.get('AddTorrentDialog').show(config['focus_add_dialog'])
            else:
                client.core.add_torrent_magnet(arg, {})

        else:
            log.debug('Attempting to add file (%s) from external source...', arg)
            if urlparse(arg).scheme == 'file':
                arg = url2pathname(urlparse(arg).path)
            path = os.path.abspath(decode_bytes(arg))

            if not os.path.exists(path):
                log.error('No such file: %s', path)
                continue

            if config['interactive_add']:
                component.get('AddTorrentDialog').add_from_files([path])
                component.get('AddTorrentDialog').show(config['focus_add_dialog'])
            else:
                with open(path, 'rb') as _file:
                    filedump = b64encode(_file.read())
                client.core.add_torrent_file(os.path.split(path)[-1], filedump, None)
