#
# main.py
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


# The main starting point for the program.    This function is called when the
# user runs the command 'deluge'.

"""Main starting point for Deluge.  Contains the main() entry point."""

import os
import os.path
import sys
from optparse import OptionParser

import deluge.common

def start_ui():
    """Entry point for ui script"""
    import deluge.common

    # Setup the argument parser
    parser = OptionParser(usage="%prog [options] [actions]",
                                           version=deluge.common.get_version())

    parser.add_option("-u", "--ui", dest="ui",
        help="""The UI that you wish to launch.  The UI choices are:\n
        \t gtk -- A GTK-based graphical user interface (default)\n
        \t web -- A web-based interface (http://localhost:8112)\n
        \t console -- A console or command-line interface""", action="store", type="str")
    parser.add_option("-c", "--config", dest="config",
        help="Set the config location", action="store", type="str")
    parser.add_option("-l", "--logfile", dest="logfile",
        help="Output to designated logfile instead of stdout", action="store", type="str")
    parser.add_option("-a", "--args", dest="args",
        help="Arguments to pass to UI, -a '--option args'", action="store", type="str")
    parser.add_option("-L", "--loglevel", dest="loglevel",
        help="Set the log level: none, info, warning, error, critical, debug", action="store", type="str")
    parser.add_option("-q", "--quiet", dest="quiet",
        help="Sets the log level to 'none', this is the same as `-L none`", action="store_true", default=False)

    # Get the options and args from the OptionParser
    (options, args) = parser.parse_args()

    if options.quiet:
        options.loglevel = "none"

    if options.config:
        if not os.path.exists(options.config):
            # Try to create the config folder if it doesn't exist
            try:
                os.makedirs(options.config)
            except Exception, e:
                pass
    else:
        if not os.path.exists(deluge.common.get_default_config_dir()):
            os.makedirs(deluge.common.get_default_config_dir())

    # Always log to a file in Windows
    if deluge.common.windows_check() and not options.logfile:
        options.logfile = "deluge.log"

    if options.logfile:
        if options.config:
            logfile = os.path.join(options.config, options.logfile)
        else:
            config_dir = deluge.common.get_default_config_dir()
            logfile = os.path.join(config_dir, options.logfile)
        sys.stdout = open(logfile, "wb")
        sys.stderr = sys.stdout
        sys.stdin = None

    from deluge.log import LOG as log
    # Set the log level if necessary
    if options.loglevel:
        import deluge.log
        deluge.log.setLoggerLevel(options.loglevel)

    version = deluge.common.get_version()
    if deluge.common.get_revision() != "":
        version = version + "r" + deluge.common.get_revision()

    log.info("Deluge ui %s", version)
    log.debug("options: %s", options)
    log.debug("args: %s", args)
    log.debug("ui_args: %s", args)

    from deluge.ui.ui import UI
    log.info("Starting ui..")
    UI(options, args, options.args)

def start_daemon():
    """Entry point for daemon script"""
    import deluge.common

    # Setup the argument parser
    parser = OptionParser(usage="%prog [options] [actions]",
                                           version=deluge.common.get_version())
    parser.add_option("-p", "--port", dest="port",
        help="Port daemon will listen on", action="store", type="int")
    parser.add_option("-d", "--do-not-daemonize", dest="donot",
        help="Do not daemonize", action="store_true", default=False)
    parser.add_option("-c", "--config", dest="config",
        help="Set the config location", action="store", type="str")
    parser.add_option("-l", "--logfile", dest="logfile",
        help="Set the logfile location", action="store", type="str")
    parser.add_option("-P", "--pidfile", dest="pidfile",
        help="Use pidfile to store process id", action="store", type="str")
    parser.add_option("-L", "--loglevel", dest="loglevel",
        help="Set the log level: none, info, warning, error, critical, debug", action="store", type="str")
    parser.add_option("-q", "--quiet", dest="quiet",
        help="Sets the log level to 'none', this is the same as `-L none`", action="store_true", default=False)

    # Get the options and args from the OptionParser
    (options, args) = parser.parse_args()

    if options.quiet:
        options.loglevel = "none"

    if options.config:
        if not os.path.exists(options.config):
            # Try to create the config folder if it doesn't exist
            try:
                os.makedirs(options.config)
            except Exception, e:
                pass
    else:
        if not os.path.exists(deluge.common.get_default_config_dir()):
            os.makedirs(deluge.common.get_default_config_dir())

    # Opens a log file and redirects stdout to it
    def open_logfile():
        path = None
        if options.logfile:
            path = options.logfile
        else:
            if options.config:
                path = os.path.join(options.config, "deluged.log")
            else:
                config_dir = deluge.common.get_default_config_dir()
                path = os.path.join(config_dir, "deluged.log")

        # Open a logfile
        if path:
            sys.stdout = open(path, "wb")
        sys.stderr = sys.stdout
        sys.stdin = None

    # Writes out a pidfile if necessary
    def write_pidfile():
        if options.pidfile:
            open(options.pidfile, "wb").write("%s\n" % os.getpid())

    # If the donot daemonize is set, then we just skip the forking
    if not options.donot:
        # Windows check, we log to the config folder by default
        if deluge.common.windows_check():
            open_logfile()
            write_pidfile()
        else:
            if os.fork() == 0:
                os.setsid()
                if os.fork() == 0:
                    open_logfile()
                    write_pidfile()
                else:
                    os._exit(0)
            else:
                os._exit(0)
    else:
        # Do not daemonize
        write_pidfile()

    # Set the log level if necessary
    if options.loglevel:
        import deluge.log
        deluge.log.setLoggerLevel(options.loglevel)

    from deluge.core.daemon import Daemon
    Daemon(options, args)
