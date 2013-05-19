#
# daemon.py
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
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
import os
import logging
from twisted.internet import reactor

import deluge.component as component
from deluge.configmanager import get_config_dir
from deluge.common import get_version, windows_check
from deluge.core.rpcserver import RPCServer, export
from deluge.error import DaemonRunningError
from deluge.core.core import Core

if windows_check():
    from win32api import SetConsoleCtrlHandler
    from win32con import CTRL_CLOSE_EVENT, CTRL_SHUTDOWN_EVENT

log = logging.getLogger(__name__)


def check_running_daemon(pid_file):
    """Check for another running instance of the daemon using the same pid file"""
    if os.path.isfile(pid_file):
        # Get the PID and the port of the supposedly running daemon
        with open(pid_file) as _file:
            (pid, port) = _file.readline().strip().split(";")
        try:
            pid, port = int(pid), int(port)
        except ValueError:
            pid, port = None, None

        def process_running(pid):
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
    def __init__(self, options=None, args=None, classic=False):
        log.info("Deluge daemon %s", get_version())
        log.debug("options: %s", options)
        log.debug("args: %s", args)

        pid_file = get_config_dir("deluged.pid")
        check_running_daemon(pid_file)

        # Twisted catches signals to terminate, so just have it call the shutdown method.
        reactor.addSystemEventTrigger("before", "shutdown", self._shutdown)

        # Catch some Windows specific signals
        if windows_check():
            def win_handler(ctrl_type):
                log.debug("windows handler ctrl_type: %s", ctrl_type)
                if ctrl_type == CTRL_CLOSE_EVENT or ctrl_type == CTRL_SHUTDOWN_EVENT:
                    self._shutdown()
                    return 1
            SetConsoleCtrlHandler(win_handler)

        listen_interface = None
        if options and options.listen_interface:
            listen_interface = options.listen_interface

        # Start the core as a thread and join it until it's done
        self.core = Core(listen_interface=listen_interface)

        port = self.core.config["daemon_port"]
        if options and options.port:
            port = options.port

        interface = None
        if options and options.ui_interface:
            interface = options.ui_interface

        self.rpcserver = RPCServer(
            port=port,
            allow_remote=self.core.config["allow_remote"],
            listen=not classic,
            interface=interface
        )

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
        """
        Returns a list of the exported methods.
        """
        return self.rpcserver.get_method_list()

    @export(1)
    def authorized_call(self, rpc):
        """
        Returns True if authorized to call rpc.

        :param rpc: a rpc, eg, "core.get_torrents_status"
        :type rpc: string

        """
        if not rpc in self.get_method_list():
            return False

        auth_level = self.rpcserver.get_session_auth_level()
        return auth_level >= self.rpcserver.get_rpc_auth_level(rpc)
