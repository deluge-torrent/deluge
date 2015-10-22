# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function

import os
from optparse import OptionGroup

from deluge.common import osx_check, windows_check
from deluge.configmanager import get_config_dir
from deluge.ui.ui import _UI, UI


class WebUI(UI):
    def __init__(self, args):
        from deluge.ui.web import server
        deluge_web = server.DelugeWeb()
        deluge_web.start()


class Web(_UI):

    help = """Starts the Deluge web interface"""

    def __init__(self):
        super(Web, self).__init__("web")
        self.__server = None

        group = OptionGroup(self.parser, "Web Options")
        group.add_option("-b", "--base", dest="base",
                         help="Set the base path that the ui is running on (proxying)",
                         action="store", default=None)
        if not (windows_check() or osx_check()):
            group.add_option("-d", "--do-not-daemonize", dest="donotdaemonize",
                             help="Do not daemonize the web interface",
                             action="store_true", default=False)
        group.add_option("-P", "--pidfile", dest="pidfile", type="str",
                         help="Use pidfile to store process id",
                         action="store", default=None)
        if not windows_check():
            group.add_option("-U", "--user", dest="user", type="str",
                             help="User to switch to. Only use it when starting as root",
                             action="store", default=None)
            group.add_option("-g", "--group", dest="group", type="str",
                             help="Group to switch to. Only use it when starting as root",
                             action="store", default=None)
        group.add_option("-i", "--interface", dest="interface",
                         type="str", help="Binds the webserver to a specific IP address",
                         action="store", default=None)
        group.add_option("-p", "--port", dest="port", type="int",
                         help="Sets the port to be used for the webserver",
                         action="store", default=None)
        group.add_option("--profile", dest="profile",
                         help="Profile the web server code",
                         action="store_true", default=False)
        try:
            import OpenSSL
            assert OpenSSL.__version__
        except ImportError:
            pass
        else:
            group.add_option("--no-ssl", dest="ssl", action="store_false",
                             help="Forces the webserver to disable ssl", default=False)
            group.add_option("--ssl", dest="ssl", action="store_true",
                             help="Forces the webserver to use ssl", default=False)
        self.parser.add_option_group(group)

    @property
    def server(self):
        return self.__server

    def start(self):
        super(Web, self).start()

        # Steps taken from http://www.faqs.org/faqs/unix-faq/programmer/faq/
        # Section 1.7
        if not self.options.ensure_value("donotdaemonize", True):
            # fork() so the parent can exit, returns control to the command line
            # or shell invoking the program.
            if os.fork():
                os._exit(0)

            # setsid() to become a process group and session group leader.
            os.setsid()

            # fork() again so the parent, (the session group leader), can exit.
            if os.fork():
                os._exit(0)

            # chdir() to esnure that our process doesn't keep any directory in
            # use that may prevent a filesystem unmount.
            os.chdir(get_config_dir())

        if self.options.pidfile:
            open(self.options.pidfile, "wb").write("%d\n" % os.getpid())

        if self.options.ensure_value("group", None):
            if not self.options.group.isdigit():
                import grp
                self.options.group = grp.getgrnam(self.options.group)[2]
            os.setuid(self.options.group)
        if self.options.ensure_value("user", None):
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

        if self.options.ensure_value("ssl", None):
            self.server.https = self.options.ssl

        def run_server():
            self.server.install_signal_handlers()
            self.server.start()

        if self.options.profile:
            import cProfile
            profiler = cProfile.Profile()
            profile_output = get_config_dir("delugeweb.profile")

            # Twisted catches signals to terminate
            def save_profile_stats():
                profiler.dump_stats(profile_output)
                print("Profile stats saved to %s" % profile_output)

            from twisted.internet import reactor
            reactor.addSystemEventTrigger("before", "shutdown", save_profile_stats)
            print("Running with profiler...")
            profiler.runcall(run_server)
        else:
            run_server()


def start():
    web = Web()
    web.start()
