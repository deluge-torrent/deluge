# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import json
import logging
import re

import deluge.component as component
import deluge.ui.console.utils.colors as colors
from deluge.ui.client import client

from . import BaseCommand

log = logging.getLogger(__name__)


def json_eval(source):
    """Evaluates string as json data and returns Python objects."""
    if source == '':
        return source

    src = source.splitlines()[0]

    # Substitutions to enable usage of pythonic syntax.
    if src.startswith('(') and src.endswith(')'):
        src = re.sub(r'^\((.*)\)$', r'[\1]', src)
    elif src.lower() in ('true', 'false'):
        src = src.lower()
    elif src.lower() == 'none':
        src = 'null'

    try:
        return json.loads(src)
    except ValueError:
        return src


class Command(BaseCommand):
    """Show and set configuration values"""

    usage = _('Usage: config [--set <key> <value>] [<key> [<key>...] ]')

    def add_arguments(self, parser):
        set_group = parser.add_argument_group('setting a value')
        set_group.add_argument(
            '-s',
            '--set',
            action='store',
            metavar='<key>',
            help=_('set value for this key'),
        )
        set_group.add_argument(
            'values', metavar='<value>', nargs='+', help=_('Value to set')
        )
        get_group = parser.add_argument_group('getting values')
        get_group.add_argument(
            'keys',
            metavar='<keys>',
            nargs='*',
            help=_('one or more keys separated by space'),
        )

    def handle(self, options):
        self.console = component.get('ConsoleUI')
        if options.set:
            return self._set_config(options)
        else:
            return self._get_config(options)

    def _get_config(self, options):
        def _on_get_config(config):
            string = ''
            for key in sorted(config):
                if key not in options.values:
                    continue

                color = '{!white,black,bold!}'
                value = config[key]
                try:
                    color = colors.type_color[type(value)]
                except KeyError:
                    pass

                # We need to format dicts for printing
                if isinstance(value, dict):
                    import pprint

                    value = pprint.pformat(value, 2, 80)
                    new_value = []
                    for line in value.splitlines():
                        new_value.append('%s%s' % (color, line))
                    value = '\n'.join(new_value)

                string += '%s: %s%s\n' % (key, color, value)
            self.console.write(string.strip())

        return client.core.get_config().addCallback(_on_get_config)

    def _set_config(self, options):
        config = component.get('CoreConfig')
        key = options.set
        val = ' '.join(options.values)

        try:
            val = json_eval(val)
        except Exception as ex:
            self.console.write('{!error!}%s' % ex)
            return

        if key not in config:
            self.console.write('{!error!}Invalid key: %s' % key)
            return

        if not isinstance(config[key], type(val)):
            try:
                val = type(config[key])(val)
            except TypeError:
                self.config.write(
                    '{!error!}Configuration value provided has incorrect type.'
                )
                return

        def on_set_config(result):
            self.console.write('{!success!}Configuration value successfully updated.')

        self.console.write('Setting "%s" to: %r' % (key, val))
        return client.core.set_config({key: val}).addCallback(on_set_config)

    def complete(self, text):
        return [k for k in component.get('CoreConfig') if k.startswith(text)]
