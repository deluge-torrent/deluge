#
# config.py
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
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

from twisted.internet import defer

from deluge.ui.console.main import BaseCommand
import deluge.ui.console.colors as colors
from deluge.ui.client import client
import deluge.component as component
from deluge.log import LOG as log

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
    elif token[1] == "/":
        count = token[-1].count("/")
        # Check for a trailing / since it messes things up
        trail = False
        if token[-1][-1] == "/":
            count -= 1
            trail = True
        for i in xrange(count * 2 - 1):
            token = next()
        # Check for trailing / and remove it
        path = token[-1].decode("string-escape")
        if trail:
            path = path[0:-1]
            token = next()
        return path
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
            make_option('-s', '--set', action='store', nargs=2, dest='set',
                        help='set value for key'),
    )
    usage = "Usage: config [key1 [key2 ...]]\n"\
            "       config --set key value"

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")
        if options['set']:
            return self._set_config(*args, **options)
        else:
            return self._get_config(*args, **options)

    def _get_config(self, *args, **options):
        deferred = defer.Deferred()
        def on_get_config(result):
            config = component.get("CoreConfig")
            keys = config.keys()
            keys.sort()
            s = ""
            for key in keys:
                if args and key not in args:
                    continue
                color = "{!white,black,bold!}"
                value = config[key]
                if type(value) in colors.type_color:
                    color = colors.type_color[type(value)]

                # We need to format dicts for printing
                if isinstance(value, dict):
                    import pprint
                    value = pprint.pformat(value, 2, 80)
                    new_value = []
                    for line in value.splitlines():
                        new_value.append("%s%s" % (color, line))
                    value = "\n".join(new_value)

                s += "  %s: %s%s\n" % (key, color, value)

            self.console.write(s)
            deferred.callback(True)
            return config

        # We need to ensure the config dict has been received first
        component.get("CoreConfig").start_defer.addCallback(on_get_config)

        return deferred

    def _set_config(self, *args, **options):
        deferred = defer.Deferred()
        config = component.get("CoreConfig")
        key = options["set"][0]
        val = options["set"][1]
        if key not in config.keys():
            self.console.write("{!error!}The key '%s' is invalid!" % key)
            return

        if type(config[key]) != type(val):
            try:
                val = type(config[key])(val)
            except:
                self.config.write("{!error!}Configuration value provided has incorrect type.")
                return

        def on_set_config(result):
            self.console.write("{!success!}Configuration value successfully updated.")
            deferred.callback(True)

        client.core.set_config({key: val}).addCallback(on_set_config)
        return deferred

    def complete(self, text):
        return [ k for k in component.get("CoreConfig").keys() if k.startswith(text) ]
