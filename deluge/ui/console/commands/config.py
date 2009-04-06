#!/usr/bin/env python
#
# config.py
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

#

from deluge.ui.console.main import BaseCommand, match_torrents
from deluge.ui.console.colors import templates, default_style as style
from deluge.ui.client import aclient as client
from optparse import make_option
import re

import cStringIO, tokenize

def atom(next, token):
    """taken with slight modifications from http://effbot.org/zone/simple-iterator-parser.htm"""
    if token[1] == "(":
        out = []
        token = next()
        while token[1] != ")":
            out.append(atom(next, token))
            token = next()
            if token[1] == ",":
                token = next()
        return tuple(out)
    elif token[0] is tokenize.STRING:
        return token[1][1:-1].decode("string-escape")
    elif token[0] is tokenize.NUMBER:
        try:
            return int(token[1], 0)
        except ValueError:
            return float(token[1])
    elif token[1].lower() == 'true':
        return True
    elif token[1].lower() == 'false':
        return False
    raise SyntaxError("malformed expression (%s)" % token[1])

def simple_eval(source):
    """ evaluates the 'source' string into a combination of primitive python objects
    taken from http://effbot.org/zone/simple-iterator-parser.htm"""
    src = cStringIO.StringIO(source).readline
    src = tokenize.generate_tokens(src)
    src = (token for token in src if token[0] is not tokenize.NL)
    res = atom(src.next, src.next())
    if src.next()[0] is not tokenize.ENDMARKER:
        raise SyntaxError("bogus data after expression")
    return res


class Command(BaseCommand):
    """Show and set configuration values"""

    option_list = BaseCommand.option_list + (
            make_option('-s', '--set', action='store_true', default=False, dest='set',
                        help='set value for key'),
    )
    usage = "Usage: config [key1 [key2 ...]]\n"\
            "       config --set key value"

    def handle(self, *args, **options):
        if options['set']:
            self._set_config(*args, **options)
        else:
            self._get_config(*args, **options)

    def _get_config(self, *args, **options):
        def _on_get_config(config):
            keys = config.keys()
            keys.sort()
            for key in keys:
                if args and key not in args:
                    continue
                color = 'white'
                value = config[key]
                if isinstance(value, bool):
                    color = 'yellow'
                elif isinstance(value, int) or isinstance(value, float):
                    color = 'green'
                elif isinstance(value, str):
                    color = 'cyan'
                elif isinstance(value, list):
                    color = 'magenta'

                print templates.config_display(key, style[color](str(value)))
        client.get_config(_on_get_config)

    def _set_config(self, *args, **options):
        def _got_config_value(config_val):
            global c_val
            c_val = config_val
        key = args[0]
        try:
            val = simple_eval(' '.join(args[1:]))
        except SyntaxError,e:
            print templates.ERROR(str(e))
            return
        client.get_config_value(_got_config_value, key)
        client.force_call()
        if c_val is None:
            print templates.ERROR("Invalid configuration name '%s'" % key)
            return
        if type(c_val) != type(val):
            print templates.ERROR("Configuration value provided has incorrect type.")
            return
        client.set_config({key: val})
        client.force_call()
        print templates.SUCCESS("Configuration value successfully updated.")

    def complete(self, text, *args):
        keys = []
        def _on_get_config(config):
            keys.extend(config.keys())
        client.get_config(_on_get_config)
        client.force_call()
        return [ k for k in keys if k.startswith(text) ]

    def split(self, text):
        return str.split(text)

