# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import argparse
import logging
import os
import platform
import sys
import textwrap

import deluge.configmanager
import deluge.log
from deluge import common
from deluge.log import setup_logger


def get_version():
    version_str = "%s\n" % (common.get_version())
    try:
        from deluge._libtorrent import lt
        version_str += "libtorrent: %s\n" % lt.version
    except ImportError:
        pass
    version_str += "Python: %s\n" % platform.python_version()
    version_str += "OS: %s %s\n" % (platform.system(), " ".join(common.get_os_version()))
    return version_str


class DelugeTextHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Help message formatter which retains formatting of all help text.
    """

    def _split_lines(self, text, width):
        """
        Do not remove whitespaces in string but still wrap text to max width.
        Instead of passing the entire text to textwrap.wrap, split and pass each
        line instead. This way list formatting is not mangled by textwrap.wrap.
        """
        wrapped_lines = []
        for l in text.splitlines():
            wrapped_lines.extend(textwrap.wrap(l, width, subsequent_indent="  "))
        return wrapped_lines

    def _format_action_invocation(self, action):
        """
        Combines the options with comma and displays the argument
        value only once instead of after both options.
        Instead of: -s <arg>, --long-opt <arg>
        Show      : -s, --long-opt <arg>

        """
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s, --long ARGS
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                opt = ", ".join(action.option_strings)
                parts.append("%s %s" % (opt, args_string))
            return ", ".join(parts)


class HelpAction(argparse._HelpAction):

    def __call__(self, parser, namespace, values, option_string=None):
        if hasattr(parser, "subparser"):
            subparser = getattr(parser, "subparser")
            # If -h on a subparser is given, the subparser will exit after help message
            subparser.parse_args()
        parser.print_help()
        parser.exit()


class BaseArgParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = lambda prog: DelugeTextHelpFormatter(prog, max_help_position=33, width=90)
        super(BaseArgParser, self).__init__(*args, add_help=False, **kwargs)

        self.common_setup = False
        self.group = self.add_argument_group(_("Common Options"))
        self.group.add_argument("-h", "--help", action=HelpAction,
                                help=_("Print this help message"))
        self.group.add_argument("-V", "--version", action="version", version="%(prog)s " + get_version(),
                                help=_("Print version information"))
        self.group.add_argument("-v", action="version", version="%(prog)s " + get_version(),
                                help=argparse.SUPPRESS)  # Deprecated arg
        self.group.add_argument("-c", "--config", metavar="<config>",
                                help=_("Set the config directory path"))
        self.group.add_argument("-l", "--logfile", metavar="<logfile>",
                                help=_("Output to specified logfile instead of stdout"))
        self.group.add_argument("-L", "--loglevel", choices=[l for k in deluge.log.levels for l in (k, k.upper())],
                                help=_("Set the log level (none, error, warning, info, debug)"), metavar="<level>")
        self.group.add_argument("--logrotate", nargs="?", const="2M", metavar="<max-size>",
                                help=_("Enable logfile rotation, with optional maximum logfile size, "
                                       "default: %(const)s (Logfile rotation count is 5)"))
        self.group.add_argument("-q", "--quiet", action="store_true",
                                help=_("Quieten logging output (Same as `--loglevel none`)"))
        self.group.add_argument("--profile", metavar="<profile-file>", nargs="?", default=False,
                                help=_("Profile %(prog)s with cProfile. Outputs to stdout "
                                       "unless a filename is specified"))

    def parse_args(self, *args):
        options, remaining = super(BaseArgParser, self).parse_known_args(*args)
        options.remaining = remaining

        if not self.common_setup:
            self.common_setup = True
            # Setup the logger
            if options.quiet:
                options.loglevel = "none"
            if options.loglevel:
                options.loglevel = options.loglevel.lower()

            logfile_mode = "w"
            logrotate = options.logrotate
            if options.logrotate:
                logfile_mode = "a"
                logrotate = common.parse_human_size(options.logrotate)

            # Setup the logger
            setup_logger(level=options.loglevel, filename=options.logfile, filemode=logfile_mode,
                         logrotate=logrotate)

            if options.config:
                if not deluge.configmanager.set_config_dir(options.config):
                    log = logging.getLogger(__name__)
                    log.error("There was an error setting the config dir! Exiting..")
                    sys.exit(1)
            else:
                if not os.path.exists(common.get_default_config_dir()):
                    os.makedirs(common.get_default_config_dir())

        return options
