# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""The Deluge daemon"""
from __future__ import unicode_literals

import logging
import os
import socket

from twisted.internet import reactor

import deluge.component as component
from deluge.common import get_version, is_ip, is_process_running, windows_check
from deluge.configmanager import get_config_dir
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer, export
from deluge.error import DaemonRunningError

if windows_check():
    from win32api import SetConsoleCtrlHandler
    from win32con import CTRL_CLOSE_EVENT, CTRL_SHUTDOWN_EVENT

log = logging.getLogger(__name__)


def is_daemon_running(pid_file):
    """
    Check for another running instance of the daemon using the same pid file.

    Args:
        pid_file: The location of the file with pid, port values.

    Returns:
        bool: True is daemon is running, False otherwise.

    """

    try:
        with open(pid_file) as _file:
            pid, port = [int(x) for x in _file.readline().strip().split(';')]
    except (EnvironmentError, ValueError):
        return False

    if is_process_running(pid):
        # Ensure it's a deluged process by trying to open a socket to it's port.
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            _socket.connect(('127.0.0.1', port))
        except socket.error:
            # Can't connect, so pid is not a deluged process.
            return False
        else:
            # This is a deluged process!
            _socket.close()
            return True


class Daemon(object):
    """The Deluge Daemon class"""

    def __init__(
        self,
        listen_interface=None,
        outgoing_interface=None,
        interface=None,
        port=None,
        standalone=False,
        read_only_config_keys=None,
    ):
        """
        Args:
            listen_interface (str, optional): The IP address to listen to
                BitTorrent connections on.
            outgoing_interface (str, optional): The network interface name or
                IP address to open outgoing BitTorrent connections on.
            interface (str, optional): The IP address the daemon will
                listen for UI connections on.
            port (int, optional): The port the daemon will listen for UI
                connections on.
            standalone (bool, optional): If True the client is in Standalone
                mode otherwise, if False, start the daemon as separate process.
            read_only_config_keys (list of str, optional): A list of config
                keys that will not be altered by core.set_config() RPC method.
        """
        self.standalone = standalone
        self.pid_file = get_config_dir('deluged.pid')
        log.info('Deluge daemon %s', get_version())
        if is_daemon_running(self.pid_file):
            raise DaemonRunningError(
                'Deluge daemon already running with this config directory!'
            )

        # Twisted catches signals to terminate, so just have it call the shutdown method.
        reactor.addSystemEventTrigger('before', 'shutdown', self._shutdown)

        # Catch some Windows specific signals
        if windows_check():

            def win_handler(ctrl_type):
                """Handle the Windows shutdown or close events."""
                log.debug('windows handler ctrl_type: %s', ctrl_type)
                if ctrl_type == CTRL_CLOSE_EVENT or ctrl_type == CTRL_SHUTDOWN_EVENT:
                    self._shutdown()
                    return 1

            SetConsoleCtrlHandler(win_handler)

        # Start the core as a thread and join it until it's done
        self.core = Core(
            listen_interface=listen_interface,
            outgoing_interface=outgoing_interface,
            read_only_config_keys=read_only_config_keys,
        )

        if port is None:
            port = self.core.config['daemon_port']
        self.port = port

        if interface and not is_ip(interface):
            log.error('Invalid UI interface (must be IP Address): %s', interface)
            interface = None

        self.rpcserver = RPCServer(
            port=port,
            allow_remote=self.core.config['allow_remote'],
            listen=not standalone,
            interface=interface,
        )

        log.debug(
            'Listening to UI on: %s:%s and bittorrent on: %s Making connections out on: %s',
            interface,
            port,
            listen_interface,
            outgoing_interface,
        )

    def start(self):
        # Register the daemon and the core RPCs
        self.rpcserver.register_object(self.core)
        self.rpcserver.register_object(self)

        # Make sure we start the PreferencesManager first
        component.start('PreferencesManager')

        if not self.standalone:
            log.info('Deluge daemon starting...')
            # Create pid file to track if deluged is running, also includes the port number.
            pid = os.getpid()
            log.debug('Storing pid %s & port %s in: %s', pid, self.port, self.pid_file)
            with open(self.pid_file, 'w') as _file:
                _file.write('%s;%s\n' % (pid, self.port))

            component.start()

            try:
                reactor.run()
            finally:
                log.debug('Remove pid file: %s', self.pid_file)
                os.remove(self.pid_file)
                log.info('Deluge daemon shutdown successfully')

    @export()
    def shutdown(self, *args, **kwargs):
        log.debug('Deluge daemon shutdown requested...')
        reactor.callLater(0, reactor.stop)

    def _shutdown(self, *args, **kwargs):
        log.info('Deluge daemon shutting down, waiting for components to shutdown...')
        if not self.standalone:
            return component.shutdown()

    @export()
    def get_method_list(self):
        """Returns a list of the exported methods."""
        return self.rpcserver.get_method_list()

    @export()
    def get_version(self):
        """Returns the daemon version"""
        return get_version()

    @export(1)
    def authorized_call(self, rpc):
        """Determines if session auth_level is authorized to call RPC.

        Args:
            rpc (str): A RPC, e.g. core.get_torrents_status

        Returns:
            bool: True if authorized to call RPC, otherwise False.
        """
        if rpc not in self.get_method_list():
            return False

        return (
            self.rpcserver.get_session_auth_level()
            >= self.rpcserver.get_rpc_auth_level(rpc)
        )
