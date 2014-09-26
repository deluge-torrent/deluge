# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""The Deluge daemon"""

import logging
import os

from twisted.internet import reactor

import deluge.component as component
from deluge.common import get_version, is_ip, windows_check
from deluge.configmanager import get_config_dir
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer, export
from deluge.error import DaemonRunningError

if windows_check():
    from win32api import SetConsoleCtrlHandler
    from win32con import CTRL_CLOSE_EVENT, CTRL_SHUTDOWN_EVENT

log = logging.getLogger(__name__)


def check_running_daemon(pid_file):
    """Check for another running instance of the daemon using the same pid file."""
    if os.path.isfile(pid_file):
        # Get the PID and the port of the supposedly running daemon
        with open(pid_file) as _file:
            (pid, port) = _file.readline().strip().split(";")
        try:
            pid, port = int(pid), int(port)
        except ValueError:
            pid, port = None, None

        def process_running(pid):
            """Verify if pid is a running process."""
            if windows_check():
                from win32process import EnumProcesses
                return pid in EnumProcesses()
            else:
                # We can just use os.kill on UNIX to test if the process is running
                try:
                    os.kill(pid, 0)
                except OSError:
                    return False
                else:
                    return True

        if pid is not None and process_running(pid):
            # Ensure it's a deluged process by trying to open a socket to it's port.
            import socket
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                _socket.connect(("127.0.0.1", port))
            except socket.error:
                # Can't connect, so it must not be a deluged process..
                pass
            else:
                # This is a deluged!
                _socket.close()
                raise DaemonRunningError("Deluge daemon already running with this config directory!")


class Daemon(object):
    """The Deluge Daemon class"""

    def __init__(self, listen_interface=None, interface=None, port=None, classic=False):
        """
        Args:
            listen_interface (str, optional): The IP address to listen to bittorrent connections on.
            interface (str, optional): The IP address the daemon will listen for UI connections on.
            port (int, optional): The port the daemon will listen for UI connections on.
            classic (bool, optional): If True the client is in Classic (Standalone) mode otherwise, if
                False, start the daemon as separate process.

        """
        log.info("Deluge daemon %s", get_version())

        pid_file = get_config_dir("deluged.pid")
        check_running_daemon(pid_file)

        # Twisted catches signals to terminate, so just have it call the shutdown method.
        reactor.addSystemEventTrigger("before", "shutdown", self._shutdown)

        # Catch some Windows specific signals
        if windows_check():
            def win_handler(ctrl_type):
                """Handle the Windows shutdown or close events."""
                log.debug("windows handler ctrl_type: %s", ctrl_type)
                if ctrl_type == CTRL_CLOSE_EVENT or ctrl_type == CTRL_SHUTDOWN_EVENT:
                    self._shutdown()
                    return 1
            SetConsoleCtrlHandler(win_handler)

        # Start the core as a thread and join it until it's done
        self.core = Core(listen_interface=listen_interface)

        if port is None:
            port = self.core.config["daemon_port"]

        if interface and not is_ip(interface):
            log.error("Invalid UI interface (must be IP Address): %s", interface)
            interface = None

        self.rpcserver = RPCServer(
            port=port,
            allow_remote=self.core.config["allow_remote"],
            listen=not classic,
            interface=interface
        )

        log.debug("Listening to UI on: %s:%s and bittorrent on: %s", interface, port, listen_interface)

        # Register the daemon and the core RPCs
        self.rpcserver.register_object(self.core)
        self.rpcserver.register_object(self)

        # Make sure we start the PreferencesManager first
        component.start("PreferencesManager")

        if not classic:
            log.info("Deluge daemon starting...")

            # Create pid file to track if deluged is running, also includes the port number.
            pid = os.getpid()
            log.debug("Storing pid %s & port %s in: %s", pid, port, pid_file)
            with open(pid_file, "wb") as _file:
                _file.write("%s;%s\n" % (pid, port))

            component.start()

            try:
                reactor.run()
            finally:
                log.debug("Remove pid file: %s", pid_file)
                os.remove(pid_file)
                log.info("Deluge daemon shutdown successfully")

    @export()
    def shutdown(self, *args, **kwargs):
        log.debug("Deluge daemon shutdown requested...")
        reactor.callLater(0, reactor.stop)

    def _shutdown(self, *args, **kwargs):
        log.info("Deluge daemon shutting down, waiting for components to shutdown...")
        return component.shutdown()

    @export()
    def get_method_list(self):
        """Returns a list of the exported methods."""
        return self.rpcserver.get_method_list()

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

        return self.rpcserver.get_session_auth_level() >= self.rpcserver.get_rpc_auth_level(rpc)
