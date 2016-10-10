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
#


# The main starting point for the program.    This function is called when the
# user runs the command 'deluge'.

"""Main starting point for Deluge.  Contains the main() entry point."""

from __future__ import with_statement

import os
import sys
from optparse import OptionParser
from logging import FileHandler
from errno import EEXIST

import deluge.log
import deluge.common
import deluge.configmanager
import deluge.error

def version_callback(option, opt_str, value, parser):
    print os.path.basename(sys.argv[0]) + ": " + deluge.common.get_version()
    try:
        from deluge._libtorrent import lt
        print "libtorrent: %s" % lt.version
    except ImportError:
        pass
    raise SystemExit

def start_ui():
    """Entry point for ui script"""
    import deluge.common

    # Setup the argument parser
    parser = OptionParser(usage="%prog [options] [actions]")
    parser.add_option("-v", "--version", action="callback", callback=version_callback,
        help="Show program's version number and exit")
    parser.add_option("-u", "--ui", dest="ui",
        help="""The UI that you wish to launch.  The UI choices are:\n
        \t gtk -- A GTK-based graphical user interface (default)\n
        \t web -- A web-based interface (http://localhost:8112)\n
        \t console -- A console or command-line interface""", action="store", type="str")
    parser.add_option("-s", "--set-default-ui", dest="default_ui",
        help="Sets the default UI to be run when no UI is specified", action="store", type="str")
    parser.add_option("-a", "--args", dest="args",
        help="Arguments to pass to UI, -a '--option args'", action="store", type="str")
    parser.add_option("-c", "--config", dest="config",
        help="Set the config folder location", action="store", type="str")
    parser.add_option("-l", "--logfile", dest="logfile",
        help="Output to designated logfile instead of stdout", action="store", type="str")
    parser.add_option("-L", "--loglevel", dest="loglevel",
        help="Set the log level: none, info, warning, error, critical, debug", action="store", type="str")
    parser.add_option("-q", "--quiet", dest="quiet",
        help="Sets the log level to 'none', this is the same as `-L none`", action="store_true", default=False)

    # Get the options and args from the OptionParser
    if deluge.common.windows_check():
        (options, args) = parser.parse_args(deluge.common.win32_unicode_argv()[1:])
    else:
        (options, args) = parser.parse_args()

    # Setup the logger
    if options.quiet:
        options.loglevel = "none"
    if options.loglevel:
        options.loglevel = options.loglevel.lower()
    deluge.log.setupLogger(level=options.loglevel, filename=options.logfile)
    from deluge.log import LOG as log

    if options.config:
        if not os.path.exists(options.config):
            # Try to create the config folder if it doesn't exist
            try:
                os.makedirs(options.config)
            except Exception, e:
                pass
        elif not os.path.isdir(options.config):
            log.error("Config option needs to be a directory!")
            sys.exit(1)
    else:
        if not os.path.exists(deluge.common.get_default_config_dir()):
            os.makedirs(deluge.common.get_default_config_dir())

    if options.default_ui:
        if options.config:
            deluge.configmanager.set_config_dir(options.config)

        config = deluge.configmanager.ConfigManager("ui.conf")
        config["default_ui"] = options.default_ui
        config.save()
        print "The default UI has been changed to", options.default_ui
        sys.exit(0)

    version = deluge.common.get_version()

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

    if 'dev' not in deluge.common.get_version():
        import warnings
        warnings.filterwarnings('ignore', category=DeprecationWarning, module='twisted')

    # Setup the argument parser
    parser = OptionParser(usage="%prog [options] [actions]")
    parser.add_option("-v", "--version", action="callback", callback=version_callback,
            help="Show program's version number and exit")
    parser.add_option("-p", "--port", dest="port",
        help="Port daemon will listen on", action="store", type="int")
    parser.add_option("-i", "--interface", dest="listen_interface",
        help="Interface daemon will listen for bittorrent connections on, \
this should be an IP address", metavar="IFACE",
        action="store", type="str")
    parser.add_option("-u", "--ui-interface", dest="ui_interface",
        help="Interface daemon will listen for UI connections on, this should be\
 an IP address", metavar="IFACE", action="store", type="str")
    parser.add_option("-d", "--do-not-daemonize", dest="donot",
        help="Do not daemonize", action="store_true", default=False)
    parser.add_option("-c", "--config", dest="config",
        help="Set the config location", action="store", type="str")
    parser.add_option("-P", "--pidfile", dest="pidfile",
        help="Use pidfile to store process id", action="store", type="str")
    parser.add_option("-l", "--logfile", dest="logfile",
        help="Set the logfile location", action="store", type="str")
    parser.add_option("-L", "--loglevel", dest="loglevel",
        help="Set the log level: none, info, warning, error, critical, debug", action="store", type="str")
    parser.add_option("-q", "--quiet", dest="quiet",
        help="Sets the log level to 'none', this is the same as `-L none`", action="store_true", default=False)
    parser.add_option("--profile", dest="profile", action="store_true", default=False,
        help="Profiles the daemon")
    parser.add_option("--read-only-config-keys", dest="read_only_config_keys",
        help="List of comma-separated config keys that will not be modified by set_config RPC.",
        action="store", type="str")

    # Get the options and args from the OptionParser
    (options, args) = parser.parse_args()

    # Setup the logger
    if options.quiet:
        options.loglevel = "none"
    if options.loglevel:
        options.loglevel = options.loglevel.lower()
    if options.logfile:
        # Try to create the logfile's directory if it doesn't exist
        try:
            os.makedirs(os.path.abspath(os.path.dirname(options.logfile)))
        except OSError, e:
            if e.errno != EEXIST:
                print "There was an error creating the log directory, exiting... (%s)" % e
                sys.exit(1)
    deluge.log.setupLogger(level=options.loglevel, filename=options.logfile)
    from deluge.log import LOG as log

    if options.config:
        if not deluge.configmanager.set_config_dir(options.config):
            log.error("There was an error setting the config directory! Exiting...")
            sys.exit(1)

    # Sets the options.logfile to point to the default location
    def open_logfile():
        if not options.logfile:
            options.logfile = deluge.configmanager.get_config_dir("deluged.log")
            file_handler = FileHandler(options.logfile)
            log.addHandler(file_handler)

    # Writes out a pidfile if necessary
    def write_pidfile():
        if options.pidfile:
            with open(options.pidfile, "wb") as _file:
                _file.write("%s\n" % os.getpid())

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

    if options.profile:
        import hotshot
        hsp = hotshot.Profile(deluge.configmanager.get_config_dir("deluged.profile"))
        hsp.start()
    try:
        from deluge.core.daemon import Daemon
        Daemon(options, args)
    except deluge.error.DaemonRunningError, e:
        log.error(e)
        log.error("You cannot run multiple daemons with the same config directory set.")
        log.error("If you believe this is an error, you can force a start by deleting %s.", deluge.configmanager.get_config_dir("deluged.pid"))
        sys.exit(1)
    except Exception, e:
        log.exception(e)
        sys.exit(1)
    finally:
        if options.profile:
            hsp.stop()
            hsp.close()
            import hotshot.stats
            stats = hotshot.stats.load(deluge.configmanager.get_config_dir("deluged.profile"))
            stats.strip_dirs()
            stats.sort_stats("time", "calls")
            stats.print_stats(400)
