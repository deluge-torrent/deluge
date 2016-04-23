# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2010 Pedro Algarvio <pedro@algarvio.me>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

# The main starting point for the program. This function is called when the
# user runs the command 'deluge'.

"""Main starting point for Deluge"""

import logging
import sys

import pkg_resources

import deluge.common
import deluge.configmanager
from deluge.ui.baseargparser import BaseArgParser
from deluge.ui.util import lang

DEFAULT_PREFS = {
    "default_ui": "gtk"
}


def start_ui():
    """Entry point for ui script"""
    lang.setup_translations()

    # Setup the argument parser
    parser = BaseArgParser()
    group = parser.add_argument_group(_("UI Options"))

    ui_entrypoints = dict([(entrypoint.name, entrypoint.load())
                           for entrypoint in pkg_resources.iter_entry_points("deluge.ui")])

    cmd_help = [_("The UI that you wish to launch. The UI choices are:")]
    max_len = 0
    for k, v in ui_entrypoints.iteritems():
        cmdline = getattr(v, "cmdline", "")
        max_len = max(max_len, len(cmdline))

    cmd_help.extend(["%s -- %s" % (k, getattr(v, "cmdline", "")) for k, v in ui_entrypoints.iteritems()])

    group.add_argument("-u", "--ui", action="store",
                       choices=ui_entrypoints.keys(), help="\n  * ".join(cmd_help))
    group.add_argument("-a", "--args", action="store",
                       help=_('Arguments to pass to the UI. Multiple args must be quoted, e.g. -a "--option args"'))
    group.add_argument("-s", "--set-default-ui", dest="default_ui", choices=ui_entrypoints.keys(),
                       help=_("Sets the default UI to be run when no UI is specified"), action="store")

    options = parser.parse_args(deluge.common.unicode_argv()[1:])

    config = deluge.configmanager.ConfigManager("ui.conf", DEFAULT_PREFS)
    log = logging.getLogger(__name__)

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
