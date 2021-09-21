# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import argparse
import logging
import os
import platform
import sys
import textwrap

import deluge.log
from deluge import common
from deluge.configmanager import get_config_dir, set_config_dir


def find_subcommand(self, args=None, sys_argv=True):
    """Find if a subcommand has been supplied.

    Args:
        args (list, optional): The argument list to search through.
        sys_argv (bool): Use sys.argv[1:] if args is None.

    Returns:
        int: Index of the subcommand or '-1' if none found.

    """
    subcommand_found = -1
    if args is None:
        args = sys.argv[1:] if sys_argv is None else []

    for x in self._subparsers._actions:
        if not isinstance(x, argparse._SubParsersAction):
            continue
        for sp_name in x._name_parser_map:
            if sp_name in args:
                subcommand_found = args.index(sp_name)

    return subcommand_found


def set_default_subparser(self, name, abort_opts=None):
    """Sets the default argparse subparser.

    Args:
        name (str): The name of the default subparser.
        abort_opts (list): The arguments to test for in case no subcommand is found.
                           If any of the values are found, the default subparser will
                           not be inserted into sys.argv.

    Returns:
        list: The arguments found in sys.argv if no subcommand found, else None

    """
    found_abort_opts = []
    abort_opts = [] if abort_opts is None else abort_opts
    test_args = sys.argv[1:]
    subparser_found = self.find_subcommand(args=test_args)

    for i, arg in enumerate(test_args):
        if subparser_found == i:
            break
        if arg in abort_opts:
            found_abort_opts.append(arg)

    if subparser_found == -1:
        if found_abort_opts:
            # Found one or more of arguments in abort_opts
            return found_abort_opts

        # insert default in first position, this implies no
        # global options without a sub_parsers specified
        sys.argv.insert(1, name)

    return None


argparse.ArgumentParser.find_subcommand = find_subcommand
argparse.ArgumentParser.set_default_subparser = set_default_subparser


def _get_version_detail():
    version_str = '%s\n' % (common.get_version())
    try:
        from deluge._libtorrent import LT_VERSION

        version_str += 'libtorrent: %s\n' % LT_VERSION
    except ImportError:
        pass
    version_str += 'Python: %s\n' % platform.python_version()
    version_str += 'OS: %s %s\n' % (platform.system(), common.get_os_version())
    return version_str


class DelugeTextHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Help message formatter which retains formatting of all help text."""

    def _split_lines(self, text, width):
        """
        Do not remove whitespaces in string but still wrap text to max width.
        Instead of passing the entire text to textwrap.wrap, split and pass each
        line instead. This way list formatting is not mangled by textwrap.wrap.
        """
        wrapped_lines = []
        for l in text.splitlines():
            wrapped_lines.extend(textwrap.wrap(l, width, subsequent_indent='  '))
        return wrapped_lines

    def _format_action_invocation(self, action):
        """
        Combines the options with comma and displays the argument
        value only once instead of after both options.
        Instead of: -s <arg>, --long-opt <arg>
        Show      : -s, --long-opt <arg>

        """
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
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
                opt = ', '.join(action.option_strings)
                parts.append('%s %s' % (opt, args_string))
            return ', '.join(parts)


class HelpAction(argparse._HelpAction):
    def __call__(self, parser, namespace, values, option_string=None):
        if hasattr(parser, 'subparser'):
            subparser = getattr(parser, 'subparser')
            subparser.print_help()
        else:
            parser.print_help()
        parser.exit()


class ArgParserBase(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        if 'formatter_class' not in kwargs:
            kwargs['formatter_class'] = lambda prog: DelugeTextHelpFormatter(
                prog, max_help_position=33, width=90
            )

        kwargs['add_help'] = kwargs.get('add_help', False)
        common_help = kwargs.pop('common_help', True)
        self.log_stream = sys.stdout
        if 'log_stream' in kwargs:
            self.log_stream = kwargs['log_stream']
            del kwargs['log_stream']

        super(ArgParserBase, self).__init__(*args, **kwargs)

        self.common_setup = False
        self.process_arg_group = False
        self.group = self.add_argument_group(_('Common Options'))
        if common_help:
            self.group.add_argument(
                '-h', '--help', action=HelpAction, help=_('Print this help message')
            )
        self.group.add_argument(
            '-V',
            '--version',
            action='version',
            version='%(prog)s ' + _get_version_detail(),
            help=_('Print version information'),
        )
        self.group.add_argument(
            '-v',
            action='version',
            version='%(prog)s ' + _get_version_detail(),
            help=argparse.SUPPRESS,
        )  # Deprecated arg
        self.group.add_argument(
            '-c',
            '--config',
            metavar='<config>',
            help=_('Set the config directory path'),
        )
        self.group.add_argument(
            '-l',
            '--logfile',
            metavar='<logfile>',
            help=_('Output to specified logfile instead of stdout'),
        )
        self.group.add_argument(
            '-L',
            '--loglevel',
            choices=[l for k in deluge.log.levels for l in (k, k.upper())],
            help=_('Set the log level (none, error, warning, info, debug)'),
            metavar='<level>',
        )
        self.group.add_argument(
            '--logrotate',
            nargs='?',
            const='2M',
            metavar='<max-size>',
            help=_(
                'Enable logfile rotation, with optional maximum logfile size, '
                'default: %(const)s (Logfile rotation count is 5)'
            ),
        )
        self.group.add_argument(
            '-q',
            '--quiet',
            action='store_true',
            help=_('Quieten logging output (Same as `--loglevel none`)'),
        )
        self.group.add_argument(
            '--profile',
            metavar='<profile-file>',
            nargs='?',
            default=False,
            help=_(
                'Profile %(prog)s with cProfile. Outputs to stdout '
                'unless a filename is specified'
            ),
        )

    def parse_args(self, args=None):
        """Parse UI arguments and handle common and process group options.

        Notes:
            Unknown arguments results in usage text printed and system exit.

        Args:
            args (list, optional): The arguments to parse.

        Returns:
            argparse.Namespace: The parsed arguments.

        """
        options = super(ArgParserBase, self).parse_args(args=args)
        return self._handle_ui_options(options)

    def parse_known_ui_args(self, args, withhold=None):
        """Parse UI arguments and handle common and process group options without error.

        Args:
            args (list): The arguments to parse.
            withhold (list): Values to ignore in the args list.

        Returns:
            argparse.Namespace: The parsed arguments.

        """
        if withhold:
            args = [a for a in args if a not in withhold]
        options, remaining = super(ArgParserBase, self).parse_known_args(args=args)
        options.remaining = remaining
        # Handle common and process group options
        return self._handle_ui_options(options)

    def _handle_ui_options(self, options):
        """Handle UI common and process group options.

        Args:
            options (argparse.Namespace): The parsed options.

        Returns:
            argparse.Namespace: The parsed options.

        """
        if not self.common_setup:
            self.common_setup = True

            # Setup the logger
            if options.quiet:
                options.loglevel = 'none'
            if options.loglevel:
                options.loglevel = options.loglevel.lower()

            logfile_mode = 'w'
            logrotate = options.logrotate
            if options.logrotate:
                logfile_mode = 'a'
                logrotate = common.parse_human_size(options.logrotate)

            # Setup the logger
            deluge.log.setup_logger(
                level=options.loglevel,
                filename=options.logfile,
                filemode=logfile_mode,
                logrotate=logrotate,
                output_stream=self.log_stream,
            )

            if options.config:
                if not set_config_dir(options.config):
                    log = logging.getLogger(__name__)
                    log.error('There was an error setting the config dir! Exiting..')
                    sys.exit(1)
            else:
                if not os.path.exists(common.get_default_config_dir()):
                    os.makedirs(common.get_default_config_dir())

        if self.process_arg_group:
            self.process_arg_group = False
            # If donotdaemonize is set, skip process forking.
            if not (common.windows_check() or options.donotdaemonize):
                if os.fork():
                    os._exit(0)
                os.setsid()
                # Do second fork
                if os.fork():
                    os._exit(0)
                # Ensure process doesn't keep any directory in use that may prevent a filesystem unmount.
                os.chdir(get_config_dir())

            # Write pid file before chuid
            if options.pidfile:
                with open(options.pidfile, 'w') as _file:
                    _file.write('%d\n' % os.getpid())

            if not common.windows_check():
                if options.group:
                    if not options.group.isdigit():
                        import grp

                        options.group = grp.getgrnam(options.group)[2]
                    os.setgid(options.group)
                if options.user:
                    if not options.user.isdigit():
                        import pwd

                        options.user = pwd.getpwnam(options.user)[2]
                    os.setuid(options.user)

        return options

    def add_process_arg_group(self):
        """Adds a grouping of common process args to control a daemon to the parser"""

        self.process_arg_group = True
        self.group = self.add_argument_group(_('Process Control Options'))
        self.group.add_argument(
            '-P',
            '--pidfile',
            metavar='<pidfile>',
            action='store',
            help=_('Pidfile to store the process id'),
        )
        if not common.windows_check():
            self.group.add_argument(
                '-d',
                '--do-not-daemonize',
                dest='donotdaemonize',
                action='store_true',
                help=_('Do not daemonize (fork) this process'),
            )
            self.group.add_argument(
                '-f',
                '--fork',
                dest='donotdaemonize',
                action='store_false',
                help=argparse.SUPPRESS,
            )  # Deprecated arg
            self.group.add_argument(
                '-U',
                '--user',
                metavar='<user>',
                action='store',
                help=_('Change to this user on startup (Requires root)'),
            )
            self.group.add_argument(
                '-g',
                '--group',
                metavar='<group>',
                action='store',
                help=_('Change to this group on startup (Requires root)'),
            )
