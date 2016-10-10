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

from __future__ import with_statement

import os
import gettext
import locale
import pkg_resources
from twisted.internet import reactor
import twisted.internet.error

import deluge.component as component
import deluge.configmanager
import deluge.common
from deluge.core.rpcserver import RPCServer, export
from deluge.log import LOG as log
import deluge.error

class Daemon(object):
    def __init__(self, options=None, args=None, classic=False):
        # Check for another running instance of the daemon
        if os.path.isfile(deluge.configmanager.get_config_dir("deluged.pid")):
            # Get the PID and the port of the supposedly running daemon
            try:
                with open(deluge.configmanager.get_config_dir("deluged.pid")) as _file:
                    (pid, port) = _file.read().strip().split(";")
                pid = int(pid)
                port = int(port)
            except ValueError:
                pid = None
                port = None


            def process_running(pid):
                if deluge.common.windows_check():
                    import win32process
                    return pid in win32process.EnumProcesses()
                else:
                    # We can just use os.kill on UNIX to test if the process is running
                    try:
                        os.kill(pid, 0)
                    except OSError:
                        return False
                    else:
                        return True

            if pid is not None and process_running(pid):
                # Ok, so a process is running with this PID, let's make doubly-sure
                # it's a deluged process by trying to open a socket to it's port.
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.connect(("127.0.0.1", port))
                except socket.error:
                    # Can't connect, so it must not be a deluged process..
                    pass
                else:
                    # This is a deluged!
                    s.close()
                    raise deluge.error.DaemonRunningError("There is a deluge daemon running with this config directory!")

        # Initialize gettext
        try:
            locale.setlocale(locale.LC_ALL, '')
            if hasattr(locale, "bindtextdomain"):
                locale.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
            if hasattr(locale, "textdomain"):
                locale.textdomain("deluge")
            gettext.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
            gettext.textdomain("deluge")
            gettext.install("deluge", pkg_resources.resource_filename("deluge", "i18n"))
        except Exception, e:
            log.error("Unable to initialize gettext/locale: %s", e)
            import __builtin__
            __builtin__.__dict__["_"] = lambda x: x

        # Twisted catches signals to terminate, so just have it call the shutdown
        # method.
        reactor.addSystemEventTrigger("before", "shutdown", self._shutdown)

        # Catch some Windows specific signals
        if deluge.common.windows_check():
            from win32api import SetConsoleCtrlHandler
            from win32con import CTRL_CLOSE_EVENT
            from win32con import CTRL_SHUTDOWN_EVENT
            def win_handler(ctrl_type):
                log.debug("ctrl_type: %s", ctrl_type)
                if ctrl_type == CTRL_CLOSE_EVENT or ctrl_type == CTRL_SHUTDOWN_EVENT:
                    self._shutdown()
                    return 1
            SetConsoleCtrlHandler(win_handler)

        version = deluge.common.get_version()

        log.info("Deluge daemon %s", version)
        log.debug("options: %s", options)
        log.debug("args: %s", args)
        # Set the config directory
        if options and options.config:
            deluge.configmanager.set_config_dir(options.config)

        if options and options.listen_interface:
            listen_interface = options.listen_interface
        else:
            listen_interface = ""

        if options and options.read_only_config_keys:
            read_only_config_keys = options.read_only_config_keys.split(",")
        else:
            read_only_config_keys = []

        from deluge.core.core import Core
        # Start the core as a thread and join it until it's done
        self.core = Core(listen_interface=listen_interface,
                         read_only_config_keys=read_only_config_keys)

        port = self.core.config["daemon_port"]
        if options and options.port:
            port = options.port
        if options and options.ui_interface:
            interface = options.ui_interface
        else:
            interface = ""

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
            # Write out a pid file all the time, we use this to see if a deluged is running
            # We also include the running port number to do an additional test
            with open(deluge.configmanager.get_config_dir("deluged.pid"), "wb") as _file:
                _file.write("%s;%s\n" % (os.getpid(), port))

            component.start()
            try:
                reactor.run()
            finally:
                self._shutdown()

    @export()
    def shutdown(self, *args, **kwargs):
        reactor.callLater(0, reactor.stop)

    def _shutdown(self, *args, **kwargs):
        if os.path.exists(deluge.configmanager.get_config_dir("deluged.pid")):
            try:
                os.remove(deluge.configmanager.get_config_dir("deluged.pid"))
            except Exception, e:
                log.exception(e)
                log.error("Error removing deluged.pid!")

        log.info("Waiting for components to shutdown..")
        d = component.shutdown()
        return d

    @export()
    def info(self):
        """
        Returns some info from the daemon.

        :returns: str, the version number
        """
        return deluge.common.get_version()

    @export()
    def get_method_list(self):
        """
        Returns a list of the exported methods.
        """
        return self.rpcserver.get_method_list()
