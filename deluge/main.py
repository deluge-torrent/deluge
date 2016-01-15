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
    group = parser.add_argument_group(_("Default Options"))

    ui_entrypoints = dict([(entrypoint.name, entrypoint.load())
                           for entrypoint in pkg_resources.iter_entry_points('deluge.ui')])

    cmd_help = ['The UI that you wish to launch.  The UI choices are:']
    max_len = 0
    for k, v in ui_entrypoints.iteritems():
        cmdline = getattr(v, 'cmdline', "")
        max_len = max(max_len, len(cmdline))

    cmd_help.extend(["%s -- %s" % (k, getattr(v, 'cmdline', "")) for k, v in ui_entrypoints.iteritems()])

    parser.add_argument("-u", "--ui", action="store",
                        choices=ui_entrypoints.keys(), help="\n* ".join(cmd_help))
    group.add_argument("-a", "--args", action="store",
                       help='Arguments to pass to the UI. Multiple args must be quoted, e.g. -a "--option args"')
    group.add_argument("-s", "--set-default-ui", dest="default_ui", choices=ui_entrypoints.keys(),
                       help="Sets the default UI to be run when no UI is specified", action="store")

    options = parser.parse_args(deluge.common.unicode_argv()[1:])

    config = deluge.configmanager.ConfigManager("ui.conf", DEFAULT_PREFS)
    log = getLogger(__name__)

    if options.default_ui:
        config["default_ui"] = options.default_ui
        config.save()
        log.info("The default UI has been changed to %s", options.default_ui)
        sys.exit(0)

    log.info("Deluge ui %s", deluge.common.get_version())
    log.debug("options: %s", options)

    selected_ui = options.ui if options.ui else config["default_ui"]

    config.save()
    del config

    # reconstruct arguments to hand off to child client
    client_args = []
    if options.args:
        import shlex
        client_args.extend(shlex.split(options.args))

    try:
        ui = ui_entrypoints[selected_ui](parser=parser)
    except KeyError as ex:
        log.error("Unable to find the requested UI: '%s'. Please select a different UI with the '-u' option"
                  " or alternatively use the '-s' option to select a different default UI.", selected_ui)
    except ImportError as ex:
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


def add_daemon_options(parser):
    group = parser.add_argument_group('Daemon Options')
    group.add_argument("-p", "--port", metavar="<port>", action="store", type=int,
                       help="The port the daemon will listen on")
    group.add_argument("-i", "--interface", metavar="<iface>", dest="listen_interface",
                       help="Interface daemon will listen for bittorrent connections on, "
                       "this should be an IP address", action="store")
    group.add_argument("-u", "--ui-interface", metavar="<iface>", action="store",
                       help="Interface daemon will listen for UI connections on, "
                       "this should be an IP address")
    if not deluge.common.windows_check():
        group.add_argument("-d", "--do-not-daemonize", dest="donot",
                           help="Do not daemonize", action="store_true", default=False)
    group.add_argument("-P", "--pidfile", metavar="<pidfile>",
                       help="Use pidfile to store process id", action="store")
    if not deluge.common.windows_check():
        group.add_argument("-U", "--user", metavar="<user>", action="store",
                           help="User to switch to. Only use it when starting as root")
        group.add_argument("-g", "--group", metavar="<group>", action="store",
                           help="Group to switch to. Only use it when starting as root")
    group.add_argument("--read-only-config-keys",
                       help="List of comma-separated config keys that will not be modified by set_config RPC.",
                       action="store", type=str, default="")


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
    parser = CommonOptionParser()
    add_daemon_options(parser)

    options = parser.parse_args()

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

    return deluge.common.run_profiled(run_daemon, options, output_file=options.profile,
                                      do_profile=options.profile)
