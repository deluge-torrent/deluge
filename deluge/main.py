# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2010 Pedro Algarvio <pedro@algarvio.me>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


# The main starting point for the program.    This function is called when the
# user runs the command 'deluge'.

"""Main starting point for Deluge.  Contains the main() entry point."""
from __future__ import print_function

import os
import platform
import sys
from errno import EEXIST
from logging import FileHandler, getLogger
from optparse import OptionParser

import deluge.common
import deluge.configmanager
import deluge.error
from deluge.log import setup_logger


def version_callback(option, opt_str, value, parser):
    print(os.path.basename(sys.argv[0]) + ": " + deluge.common.get_version())
    try:
        from deluge._libtorrent import lt
        print("libtorrent: %s" % lt.version)
    except ImportError:
        pass
    print("Python: %s" % platform.python_version())
    for version in (platform.linux_distribution(), platform.win32_ver(), platform.mac_ver(), ("n/a",)):
        if filter(None, version):  # pylint: disable=bad-builtin
            print("OS: %s %s" % (platform.system(), " ".join(version)))
            break
    raise SystemExit


def start_ui():
    """Entry point for ui script"""
    # Setup the argument parser
    parser = OptionParser(usage="%prog [options] [actions]")
    parser.add_option("-v", "--version", action="callback", callback=version_callback,
                      help="Show program's version number and exit")
    parser.add_option("-u", "--ui", dest="ui",
                      help="""The UI that you wish to launch.  The UI choices are:\n
                      \t gtk -- A GTK-based graphical user interface (default)\n
                      \t web -- A web-based interface (http://localhost:8112)\n
                      \t console -- A console or command-line interface""")
    parser.add_option("-s", "--set-default-ui", dest="default_ui",
                      help="Sets the default UI to be run when no UI is specified")
    parser.add_option("-a", "--args", dest="args",
                      help="Arguments to pass to UI, -a '--option args'")
    parser.add_option("-c", "--config", dest="config",
                      help="Set the config folder location")
    parser.add_option("-l", "--logfile", dest="logfile",
                      help="Output to designated logfile instead of stdout")
    parser.add_option("-L", "--loglevel", dest="loglevel",
                      help="Set the log level: none, info, warning, error, critical, debug")
    parser.add_option("-q", "--quiet", dest="quiet", action="store_true", default=False,
                      help="Sets the log level to 'none', this is the same as `-L none`")
    parser.add_option("-r", "--rotate-logs",
                      help="Rotate logfiles.", action="store_true", default=False)

    # Get the options and args from the OptionParser
    (options, args) = parser.parse_args(deluge.common.unicode_argv()[1:])

    # Setup the logger
    if options.quiet:
        options.loglevel = "none"
    if options.loglevel:
        options.loglevel = options.loglevel.lower()
    logfile_mode = 'w'
    if options.rotate_logs:
        logfile_mode = 'a'
    setup_logger(level=options.loglevel, filename=options.logfile, filemode=logfile_mode)
    log = getLogger(__name__)

    if options.config:
        if not os.path.exists(options.config):
            # Try to create the config folder if it doesn't exist
            try:
                os.makedirs(options.config)
            except OSError:
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
        print("The default UI has been changed to", options.default_ui)
        sys.exit(0)

    version = deluge.common.get_version()

    log.info("Deluge ui %s", version)
    log.debug("options: %s", options)
    log.debug("args: %s", args)
    log.debug("ui_args: %s", args)

    from deluge.ui.ui import UI
    log.info("Starting ui..")
    UI(options, args, options.args)


def start_daemon(skip_start=False):
    """
    Entry point for daemon script

    Args:
        skip_start (bool): If starting daemon should be skipped.

    Returns:
        deluge.core.daemon.Daemon: A new daemon object

    """
    deluge.common.setup_translations()

    if 'dev' not in deluge.common.get_version():
        import warnings
        warnings.filterwarnings('ignore', category=DeprecationWarning, module='twisted')

    # Setup the argument parser
    parser = OptionParser(usage="%prog [options] [actions]")
    parser.add_option("-v", "--version", action="callback", callback=version_callback,
                      help="Show program's version number and exit")
    parser.add_option("-p", "--port", dest="port",
                      help="Port daemon will listen on", type="int")
    parser.add_option("-i", "--interface", dest="listen_interface",
                      help="Interface daemon will listen for bittorrent connections on,"
                      "this should be an IP address", metavar="IFACE")
    parser.add_option("-u", "--ui-interface", dest="ui_interface", metavar="IFACE",
                      help="Interface daemon will listen for UI connections on, this should be an IP address")
    if not (deluge.common.windows_check() or deluge.common.osx_check()):
        parser.add_option("-d", "--do-not-daemonize", dest="donot",
                          help="Do not daemonize", action="store_true", default=False)
    parser.add_option("-c", "--config", dest="config", help="Set the config location")
    parser.add_option("-P", "--pidfile", dest="pidfile", help="Use pidfile to store process id")
    if not deluge.common.windows_check():
        parser.add_option("-U", "--user", dest="user", help="User to switch to. Only use it when starting as root")
        parser.add_option("-g", "--group", dest="group", help="Group to switch to. Only use it when starting as root")
    parser.add_option("-l", "--logfile", dest="logfile", help="Set the logfile location")
    parser.add_option("-L", "--loglevel", dest="loglevel",
                      help="Set the log level: none, info, warning, error, critical, debug")
    parser.add_option("-q", "--quiet", dest="quiet", action="store_true", default=False,
                      help="Sets the log level to 'none', this is the same as `-L none`")
    parser.add_option("-r", "--rotate-logs", help="Rotate logfiles.", action="store_true", default=False)
    parser.add_option("--profile", dest="profile", action="store_true", default=False, help="Profiles the daemon")
    parser.add_option("--read-only-config-keys", dest="read_only_config_keys",
                      help="List of comma-separated config keys that will not be modified by \
                      set_config RPC.",
                      action="store", type="str", default="")

    # Get the options and args from the OptionParser
    (options, args) = parser.parse_args()

    if options.config:
        if not deluge.configmanager.set_config_dir(options.config):
            print("There was an error setting the config directory! Exiting...")
            sys.exit(1)

    # Check for any daemons running with this same config
    from deluge.core.daemon import check_running_daemon
    pid_file = deluge.configmanager.get_config_dir("deluged.pid")
    try:
        check_running_daemon(pid_file)
    except deluge.error.DaemonRunningError:
        print("You cannot run multiple daemons with the same config directory set.")
        print("If you believe this is an error, you can force a start by deleting: %s" % pid_file)
        sys.exit(1)

    # Setup the logger
    if options.quiet:
        options.loglevel = "none"
    if options.logfile:
        # Try to create the logfile's directory if it doesn't exist
        try:
            os.makedirs(os.path.abspath(os.path.dirname(options.logfile)))
        except OSError as ex:
            if ex.errno != EEXIST:
                print("There was an error creating the log directory, exiting... (%s)" % ex)
                sys.exit(1)

    logfile_mode = 'w'
    if options.rotate_logs:
        logfile_mode = 'a'
    setup_logger(level=options.loglevel, filename=options.logfile, filemode=logfile_mode)
    log = getLogger(__name__)

    # If no logfile specified add logging to default location (as well as stdout)
    if not options.logfile:
        options.logfile = deluge.configmanager.get_config_dir("deluged.log")
        file_handler = FileHandler(options.logfile)
        log.addHandler(file_handler)

    # If the donot daemonize is set, then we just skip the forking
    if not (deluge.common.windows_check() or options.donot):
        if os.fork():
            # We've forked and this is now the parent process, so die!
            os._exit(0)
        os.setsid()
        # Do second fork
        if os.fork():
            os._exit(0)

    # Write pid file before chuid
    if options.pidfile:
        with open(options.pidfile, "wb") as _file:
            _file.write("%s\n" % os.getpid())

    if not deluge.common.windows_check():
        if options.user:
            if not options.user.isdigit():
                import pwd
                options.user = pwd.getpwnam(options.user)[2]
            os.setuid(options.user)
        if options.group:
            if not options.group.isdigit():
                import grp
                options.group = grp.getgrnam(options.group)[2]
            os.setuid(options.group)

    def run_daemon(options):
        try:
            from deluge.core.daemon import Daemon
            daemon = Daemon(listen_interface=options.listen_interface,
                            interface=options.ui_interface,
                            port=options.port,
                            read_only_config_keys=options.read_only_config_keys.split(","))
            if not skip_start:
                daemon.start()
            return daemon
        except Exception as ex:
            log.exception(ex)
            sys.exit(1)
        finally:
            if options.pidfile:
                os.remove(options.pidfile)

    if options.profile:
        import cProfile
        profiler = cProfile.Profile()
        profile_output = deluge.configmanager.get_config_dir("deluged.profile")

        # Twisted catches signals to terminate
        def save_profile_stats():
            profiler.dump_stats(profile_output)
            print("Profile stats saved to %s" % profile_output)

        from twisted.internet import reactor
        reactor.addSystemEventTrigger("before", "shutdown", save_profile_stats)
        print("Running with profiler...")
        profiler.runcall(run_daemon, options)
    else:
        return run_daemon(options)
