# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function

import logging
import sys
from optparse import OptionGroup, OptionParser

import deluge.common
import deluge.configmanager
import deluge.log
from deluge.main import version_callback

try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        return


DEFAULT_PREFS = {
    "default_ui": "gtk"
}

if 'dev' not in deluge.common.get_version():
    import warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning, module='twisted')


class _UI(object):

    def __init__(self, name="gtk"):
        self.__name = name

        self.__parser = OptionParser(usage="%prog [options] [actions]")
        self.__parser.add_option("-v", "--version", action="callback", callback=version_callback,
                                 help="Show program's version number and exit")
        group = OptionGroup(self.__parser, "Common Options")
        group.add_option("-c", "--config", dest="config", help="Set the config folder location")
        group.add_option("-l", "--logfile", dest="logfile", help="Output to designated logfile instead of stdout")
        group.add_option("-L", "--loglevel", dest="loglevel",
                         help="Set the log level: none, info, warning, error, critical, debug")
        group.add_option("-q", "--quiet", dest="quiet", action="store_true", default=False,
                         help="Sets the log level to 'none', this is the same as `-L none`")
        group.add_option("-r", "--rotate-logs", help="Rotate logfiles.", action="store_true", default=False)
        self.__parser.add_option_group(group)

    @property
    def name(self):
        return self.__name

    @property
    def parser(self):
        return self.__parser

    @property
    def options(self):
        return self.__options

    @property
    def args(self):
        return self.__args

    def start(self):
        # Make sure all arguments are unicode
        argv = deluge.common.unicode_argv()[1:]
        (self.__options, self.__args) = self.__parser.parse_args(argv)

        if self.__options.quiet:
            self.__options.loglevel = "none"

        logfile_mode = 'w'
        if self.__options.rotate_logs:
            logfile_mode = 'a'

        if self.__options.loglevel:
            self.__options.loglevel = self.__options.loglevel.lower()

        # Setup the logger
        deluge.log.setup_logger(level=self.__options.loglevel,
                                filename=self.__options.logfile,
                                filemode=logfile_mode)

        log = logging.getLogger(__name__)

        if self.__options.config:
            if not deluge.configmanager.set_config_dir(self.__options.config):
                log.error("There was an error setting the config dir! Exiting..")
                sys.exit(1)

        # Setup gettext
        deluge.common.setup_translations()

        setproctitle("deluge-%s" % self.__name)

        log.info("Deluge ui %s", deluge.common.get_version())
        log.debug("options: %s", self.__options)
        log.debug("args: %s", self.__args)
        log.info("Starting %s ui..", self.__name)


class UI:
    def __init__(self, options, args, ui_args):
        log = logging.getLogger(__name__)
        log.debug("UI init..")

        # Setup gettext
        deluge.common.setup_translations()

        # Set the config directory
        deluge.configmanager.set_config_dir(options.config)

        config = deluge.configmanager.ConfigManager("ui.conf", DEFAULT_PREFS)

        if not options.ui:
            selected_ui = config["default_ui"]
        else:
            selected_ui = options.ui

        setproctitle("deluge")

        config.save()
        del config

        try:
            if selected_ui == "gtk":
                log.info("Starting GtkUI..")
                from deluge.ui.gtkui.gtkui import GtkUI
                GtkUI(args)
            elif selected_ui == "web":
                log.info("Starting WebUI..")
                from deluge.ui.web.web import WebUI
                WebUI(args)
            elif selected_ui == "console":
                log.info("Starting ConsoleUI..")
                from deluge.ui.console.main import ConsoleUI
                ConsoleUI(ui_args)
        except ImportError as ex:
            import traceback
            error_type, error_value, tb = sys.exc_info()
            stack = traceback.extract_tb(tb)
            last_frame = stack[-1]
            if last_frame[0] == __file__:
                log.error("Unable to find the requested UI: %s.  Please select a different UI with the '-u' option \
                          or alternatively use the '-s' option to select a different default UI.", selected_ui)
            else:
                log.exception(ex)
                log.error("There was an error whilst launching the request UI: %s", selected_ui)
                log.error("Look at the traceback above for more information.")
            sys.exit(1)
