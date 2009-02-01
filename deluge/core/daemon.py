#
# daemon.py
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
# 	Boston, MA    02110-1301, USA.
#

import signal

import gettext
import locale
import pkg_resources
from twisted.internet import reactor

import deluge.component as component
import deluge.configmanager
import deluge.common
from deluge.core.rpcserver import RPCServer, export
from deluge.log import LOG as log

class Daemon(object):
    def __init__(self, options=None, args=None, classic=False):
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

        # Setup signals
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        if not deluge.common.windows_check():
            signal.signal(signal.SIGHUP, self.shutdown)
        else:
            from win32api import SetConsoleCtrlHandler
            from win32con import CTRL_CLOSE_EVENT
            from win32con import CTRL_SHUTDOWN_EVENT
            def win_handler(ctrl_type):
                log.debug("ctrl_type: %s", ctrl_type)
                if ctrl_type == CTRL_CLOSE_EVENT or ctrl_type == CTRL_SHUTDOWN_EVENT:
                    self.__shutdown()
                    return 1
            SetConsoleCtrlHandler(win_handler)

        version = deluge.common.get_version()
        if deluge.common.get_revision():
            version = version + "r" + deluge.common.get_revision()

        log.info("Deluge daemon %s", version)
        log.debug("options: %s", options)
        log.debug("args: %s", args)
        # Set the config directory
        if options:
            deluge.configmanager.set_config_dir(options.config)

        from deluge.core.core import Core
        # Start the core as a thread and join it until it's done
        self.core = Core()

        port = self.core.config["daemon_port"]
        if options and options.port:
            port = options.port
        self.rpcserver = RPCServer(
            port=port,
            allow_remote=self.core.config["allow_remote"],
            listen=not classic
        )

        # Register the daemon and the core RPCs
        self.rpcserver.register_object(self.core)
        self.rpcserver.register_object(self)


        # Make sure we start the PreferencesManager first
        component.start("PreferencesManager")

        if not classic:
            component.start()
            try:
                reactor.run()
            except KeyboardInterrupt:
                self.shutdown()

    @export()
    def shutdown(self, *args, **kwargs):
        component.shutdown()
        reactor.stop()

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
        return self.rpccserver.get_method_list()
