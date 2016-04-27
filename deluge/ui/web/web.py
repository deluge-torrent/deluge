# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function

import argparse
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

        group = self.parser.add_argument_group(_("Web Server Options"))
        group.add_argument("-i", "--interface", metavar="<ip_address>", action="store",
                           help=_("IP address for web server to listen on"))
        group.add_argument("-p", "--port", metavar="<port>", type=int, action="store",
                           help=_("Port for web server to listen on"))
        group.add_argument("-P", "--pidfile", metavar="<pidfile>", action="store",
                           help=_("Pidfile to store the process id"))
        if not windows_check():
            group.add_argument("-d", "--do-not-daemonize", dest="donotdaemonize", action="store_true",
                               help=_("Do not daemonize (fork) this process"))
            group.add_argument("-f", "--fork", dest="donotdaemonize", action="store_false",
                               help=argparse.SUPPRESS)  # Deprecated arg
            group.add_argument("-U", "--user", metavar="<user>", action="store",
                               help=_("Change to this user on startup (Requires root)"))
            group.add_argument("-g", "--group", metavar="<group>", action="store",
                               help=_("Change to this group on startup (Requires root)"))
        group.add_argument("-b", "--base", metavar="<path>", action="store",
                           help=_("Set the base path that the ui is running on"))
        try:
            import OpenSSL
            assert OpenSSL.__version__
        except ImportError:
            pass
        else:
            group.add_argument("--ssl", action="store_true", help=_("Force the web server to use SSL"))
            group.add_argument("--no-ssl", action="store_true", help=_("Force the web server to disable SSL"))

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

        # Write pid file before chuid
        if self.options.pidfile:
            with open(self.options.pidfile, "wb") as _file:
                _file.write("%d\n" % os.getpid())

        if not windows_check():
            if self.options.user:
                if not self.options.user.isdigit():
                    import pwd
                    self.options.user = pwd.getpwnam(self.options.user)[2]
                os.setuid(self.options.user)
            if self.options.group:
                if not self.options.group.isdigit():
                    import grp
                    self.options.group = grp.getgrnam(self.options.group)[2]
                os.setuid(self.options.group)

        from deluge.ui.web import server
        self.__server = server.DelugeWeb(options=self.options)

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
