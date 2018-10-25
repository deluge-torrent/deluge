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

import logging
import tokenize
from io import StringIO

import deluge.component as component
import deluge.ui.console.utils.colors as colors
from deluge.ui.client import client

from . import BaseCommand

log = logging.getLogger(__name__)


def atom(src, token):
    """taken with slight modifications from http://effbot.org/zone/simple-iterator-parser.htm"""
    if token[1] == '(':
        out = []
        token = next(src)
        while token[1] != ')':
            out.append(atom(src, token))
            token = next(src)
            if token[1] == ',':
                token = next(src)
        return tuple(out)
    elif token[0] is tokenize.NUMBER or token[1] == '-':
        try:
            if token[1] == '-':
                return int(token[-1], 0)
            else:
                if token[1].startswith('0x'):
                    # Hex number so return unconverted as string.
                    return token[1].decode('string-escape')
                else:
                    return int(token[1], 0)
        except ValueError:
            try:
                return float(token[-1])
            except ValueError:
                return str(token[-1])
    elif token[1].lower() == 'true':
        return True
    elif token[1].lower() == 'false':
        return False
    elif token[0] is tokenize.STRING or token[1] == '/':
        return token[-1].decode('string-escape')
    elif token[1].isalpha():
        # Parse Windows paths e.g. 'C:\\xyz' or 'C:/xyz'.
        if next()[1] == ':' and next()[1] in '\\/':
            return token[-1].decode('string-escape')

    raise SyntaxError('malformed expression (%s)' % token[1])


def simple_eval(source):
    """ evaluates the 'source' string into a combination of primitive python objects
    taken from http://effbot.org/zone/simple-iterator-parser.htm"""
    src = StringIO(source).readline
    src = tokenize.generate_tokens(src)
    src = (token for token in src if token[0] is not tokenize.NL)
    res = atom(src, next(src))
    return res


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
            val = simple_eval(val)
        except SyntaxError as ex:
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

        self.console.write('Setting "%s" to: %s' % (key, val))
        return client.core.set_config({key: val}).addCallback(on_set_config)

    def complete(self, text):
        return [k for k in component.get('CoreConfig') if k.startswith(text)]
