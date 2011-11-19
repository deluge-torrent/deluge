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

import optparse
import os
import sys
from logging import FileHandler, getLogger

import pkg_resources

import deluge.common
import deluge.configmanager
import deluge.error
from deluge.commonoptions import CommonOptionParser

DEFAULT_PREFS = {
    "default_ui": "gtk"
}


def start_ui():
    """Entry point for ui script"""
    deluge.common.setup_translations()

    # Setup the argument parser
    parser = CommonOptionParser()
    group = optparse.OptionGroup(parser, _("Default Options"))

    ui_entrypoints = dict([(entrypoint.name, entrypoint.load())
                           for entrypoint in pkg_resources.iter_entry_points('deluge.ui')])

    cmd_help = ['The UI that you wish to launch.  The UI choices are:']
    cmd_help.extend(["%s -- %s" % (k, getattr(v, 'cmdline', "")) for k, v in ui_entrypoints.iteritems()])

    parser.add_option("-u", "--ui", dest="ui",
                      choices=ui_entrypoints.keys(), help="\n\t ".join(cmd_help), action="store")
    group.add_option("-a", "--args", dest="args",
                     help="Arguments to pass to UI, -a '--option args'", action="store", type="str")
    group.add_option("-s", "--set-default-ui", dest="default_ui",
                     help="Sets the default UI to be run when no UI is specified", action="store", type="str")

    parser.add_option_group(group)

    # Get the options and args from the OptionParser
    (options, args) = parser.parse_args(deluge.common.unicode_argv()[1:])

    config = deluge.configmanager.ConfigManager("ui.conf", DEFAULT_PREFS)
    log = getLogger(__name__)

    if options.default_ui:
        config["default_ui"] = options.default_ui
        config.save()
        log.info("The default UI has been changed to %s", options.default_ui)
        sys.exit(0)

    log.info("Deluge ui %s", deluge.common.get_version())
    log.debug("options: %s", options)
    log.debug("args: %s", args)

    selected_ui = options.ui if options.ui else config["default_ui"]

    config.save()
    del config

    # reconstruct arguments to hand off to child client
    client_args = []
    if options.args:
        import shlex
        client_args.extend(shlex.split(options.args))
    client_args.extend(args)

    try:
        ui = ui_entrypoints[selected_ui](skip_common=True)
    except KeyError as ex:
        log.error("Unable to find the requested UI: '%s'. Please select a different UI with the '-u' option"
                  " or alternatively use the '-s' option to select a different default UI.", selected_ui)
    except ImportError as ex:
        import sys
        import traceback
        error_type, error_value, tb = sys.exc_info()
        stack = traceback.extract_tb(tb)
        last_frame = stack[-1]
        if last_frame[0] == __file__:
            log.error("Unable to find the requested UI: %s.  Please select a different UI with the '-u' "
                      "option or alternatively use the '-s' option to select a different default UI.", selected_ui)
        else:
            log.exception(ex)
            log.error("There was an error whilst launching the request UI: %s", selected_ui)
            log.error("Look at the traceback above for more information.")
        sys.exit(1)
    else:
        ui.start(client_args)


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
    parser = CommonOptionParser(usage="%prog [options] [actions]")

    group = optparse.OptionGroup(parser, _("Daemon Options"))
    group.add_option("-p", "--port", dest="port",
                     help="Port daemon will listen on", action="store", type="int")
    group.add_option("-i", "--interface", dest="listen_interface",
                     help="Interface daemon will listen for bittorrent connections on, "
                     "this should be an IP address", metavar="IFACE",
                     action="store", type="str")
    group.add_option("-u", "--ui-interface", dest="ui_interface",
                     help="Interface daemon will listen for UI connections on, this should be "
                     "an IP address", metavar="IFACE", action="store", type="str")
    if not (deluge.common.windows_check() or deluge.common.osx_check()):
        group.add_option("-d", "--do-not-daemonize", dest="donot",
                         help="Do not daemonize", action="store_true", default=False)
    group.add_option("-P", "--pidfile", dest="pidfile",
                     help="Use pidfile to store process id", action="store", type="str")
    if not deluge.common.windows_check():
        group.add_option("-U", "--user", dest="user",
                         help="User to switch to. Only use it when starting as root", action="store", type="str")
        group.add_option("-g", "--group", dest="group",
                         help="Group to switch to. Only use it when starting as root", action="store", type="str")
    group.add_option("--read-only-config-keys",
                     help="List of comma-separated config keys that will not be modified by set_config RPC.",
                     action="store", type="str", default="")
    group.add_option("--profile", dest="profile", action="store_true", default=False,
                     help="Profiles the daemon")

    parser.add_option_group(group)

    # Get the options and args from the OptionParser
    (options, args) = parser.parse_args()

    # Check for any daemons running with this same config
    from deluge.core.daemon import check_running_daemon
    pid_file = deluge.configmanager.get_config_dir("deluged.pid")
    try:
        check_running_daemon(pid_file)
    except deluge.error.DaemonRunningError:
        print("You cannot run multiple daemons with the same config directory set.")
        print("If you believe this is an error, you can force a start by deleting: %s" % pid_file)
        sys.exit(1)

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
