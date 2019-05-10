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
from __future__ import unicode_literals

import argparse
import logging
import os
import sys

import pkg_resources

import deluge.common
import deluge.configmanager
from deluge.argparserbase import ArgParserBase
from deluge.i18n import setup_translation

DEFAULT_PREFS = {'default_ui': 'gtk'}

AMBIGUOUS_CMD_ARGS = ('-h', '--help', '-v', '-V', '--version')


def start_ui():
    """Entry point for ui script"""
    setup_translation()

    # Get the registered UI entry points
    ui_entrypoints = {}
    for entrypoint in pkg_resources.iter_entry_points('deluge.ui'):
        try:
            ui_entrypoints[entrypoint.name] = entrypoint.load()
        except ImportError:
            # Unable to load entrypoint so skip adding it.
            pass

    ui_titles = sorted(ui_entrypoints)

    def add_ui_options_group(_parser):
        """Function to enable reuse of UI Options group"""
        group = _parser.add_argument_group(_('UI Options'))
        group.add_argument(
            '-s',
            '--set-default-ui',
            dest='default_ui',
            choices=ui_titles,
            help=_('Set the default UI to be run, when no UI is specified'),
        )
        return _parser

    # Setup parser with Common Options and add UI Options group.
    parser = add_ui_options_group(ArgParserBase())

    # Parse and handle common/process group options
    options = parser.parse_known_ui_args(sys.argv, withhold=AMBIGUOUS_CMD_ARGS)

    config = deluge.configmanager.ConfigManager('ui.conf', DEFAULT_PREFS)
    log = logging.getLogger(__name__)
    log.info('Deluge ui %s', deluge.common.get_version())

    if options.default_ui:
        config['default_ui'] = options.default_ui
        config.save()
        log.info('The default UI has been changed to %s', options.default_ui)
        sys.exit(0)

    default_ui = config['default_ui']
    config.save()  # Save in case config didn't already exist.
    del config

    # We have parsed and got the config dir needed to get the default UI
    # Now create a parser for choosing the UI. We reuse the ui option group for
    # parsing to succeed and the text displayed to user, but result is not used.
    parser = add_ui_options_group(ArgParserBase(common_help=True))

    # Create subparser for each registered UI. Empty title is used to remove unwanted positional text.
    subparsers = parser.add_subparsers(
        dest='selected_ui',
        metavar='{%s} [UI args]' % ','.join(ui_titles),
        title=None,
        help=_('Alternative UI to launch, with optional ui args \n  (default UI: *)'),
    )
    for ui in ui_titles:
        parser_ui = subparsers.add_parser(
            ui,
            common_help=False,
            help=getattr(ui_entrypoints[ui], 'cmd_description', ''),
        )
        parser_ui.add_argument('ui_args', nargs=argparse.REMAINDER)
        # If the UI is set as default, indicate this in help by prefixing with a star.
        subactions = subparsers._get_subactions()
        prefix = '*' if ui == default_ui else ' '
        subactions[-1].metavar = '%s %s' % (prefix, ui)

    # Insert a default UI subcommand unless one of the ambiguous_args are specified
    parser.set_default_subparser(default_ui, abort_opts=AMBIGUOUS_CMD_ARGS)

    # Only parse known arguments to leave the UIs to show a help message if parsing fails.
    options, remaining = parser.parse_known_args()
    selected_ui = options.selected_ui
    ui_args = remaining + options.ui_args

    # Remove the UI argument before launching the UI.
    sys.argv.remove(selected_ui)

    try:
        ui = ui_entrypoints[selected_ui](
            prog='%s %s' % (os.path.basename(sys.argv[0]), selected_ui), ui_args=ui_args
        )
    except KeyError:
        log.error(
            'Unable to find chosen UI: "%s". Please choose a different UI '
            'or use "--set-default-ui" to change default UI.',
            selected_ui,
        )
    except ImportError as ex:
        import traceback

        error_type, error_value, tb = sys.exc_info()
        stack = traceback.extract_tb(tb)
        last_frame = stack[-1]
        if last_frame[0] == __file__:
            log.error(
                'Unable to find chosen UI: "%s". Please choose a different UI '
                'or use "--set-default-ui" to change default UI.',
                selected_ui,
            )
        else:
            log.exception(ex)
            log.error('Encountered an error launching the request UI: %s', selected_ui)
        sys.exit(1)
    else:
        ui.start()
