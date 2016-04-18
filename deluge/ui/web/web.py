# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function

import logging
import os

from deluge.common import run_profiled, windows_check
from deluge.configmanager import get_config_dir
from deluge.ui.ui import UI

log = logging.getLogger(__name__)


class WebUI(object):
    def __init__(self, args):
        from deluge.ui.web import server
        deluge_web = server.DelugeWeb()
        deluge_web.start()


class Web(UI):

    help = """Starts the Deluge web interface"""
    cmdline = """A web-based interface (http://localhost:8112)"""

    def __init__(self, *args, **kwargs):
        super(Web, self).__init__("web", *args, **kwargs)
        self.__server = None

        group = self.parser.add_argument_group(_('Web Options'))

        group.add_argument("-b", "--base", metavar="<path>", action="store", default=None,
                           help="Set the base path that the ui is running on (proxying)")
        if not windows_check():
            group.add_argument("-d", "--do-not-daemonize", dest="donotdaemonize", action="store_true", default=False,
                               help="Do not daemonize the web interface")
        group.add_argument("-P", "--pidfile", metavar="<pidfile>", action="store", default=None,
                           help="Use pidfile to store process id")
        if not windows_check():
            group.add_argument("-U", "--user", metavar="<user>", action="store", default=None,
                               help="User to switch to. Only use it when starting as root")
            group.add_argument("-g", "--group", metavar="<group>", action="store", default=None,
                               help="Group to switch to. Only use it when starting as root")
        group.add_argument("-i", "--interface", metavar="<interface>", action="store", default=None,
                           help="Binds the webserver to a specific IP address")
        group.add_argument("-p", "--port", metavar="<port>", type=int, action="store", default=None,
                           help="Sets the port to be used for the webserver")
        try:
            import OpenSSL
            assert OpenSSL.__version__
        except ImportError:
            pass
        else:
            group.add_argument("--no-ssl", dest="ssl", action="store_false",
                               help="Forces the webserver to disable ssl", default=False)
            group.add_argument("--ssl", dest="ssl", action="store_true",
                               help="Forces the webserver to use ssl", default=False)

    @property
    def server(self):
        return self.__server

    def start(self, args=None):
        super(Web, self).start(args)

        # If donotdaemonize is set, skip process forking.
        if not (windows_check() or self.options.donotdaemonize):
            if os.fork():
                os._exit(0)
            os.setsid()
            # Do second fork
            if os.fork():
                os._exit(0)
            # Ensure process doesn't keep any directory in use that may prevent a filesystem unmount.
            os.chdir(get_config_dir())

        if self.options.pidfile:
            open(self.options.pidfile, "wb").write("%d\n" % os.getpid())

        if self.options.group:
            if not self.options.group.isdigit():
                import grp
                self.options.group = grp.getgrnam(self.options.group)[2]
            os.setuid(self.options.group)
        if self.options.user:
            if not self.options.user.isdigit():
                import pwd
                self.options.user = pwd.getpwnam(self.options.user)[2]
            os.setuid(self.options.user)

        from deluge.ui.web import server
        self.__server = server.DelugeWeb()

        if self.options.base:
            self.server.base = self.options.base

        if self.options.interface:
            self.server.interface = self.options.interface

        if self.options.port:
            self.server.port = self.options.port

        self.server.https = self.options.ssl

        def run():
            try:
                self.server.install_signal_handlers()
                self.server.start()
            except Exception as ex:
                log.exception(ex)
                raise
        run_profiled(run, output_file=self.options.profile, do_profile=self.options.profile)


def start():
    web = Web()
    web.start()
