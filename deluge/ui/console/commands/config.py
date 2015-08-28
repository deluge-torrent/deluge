# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import cStringIO
import logging
import tokenize
from optparse import make_option

import deluge.component as component
import deluge.ui.console.colors as colors
from deluge.ui.client import client
from deluge.ui.console.main import BaseCommand

log = logging.getLogger(__name__)


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
    elif token[0] is tokenize.NUMBER or token[1] == "-":
        try:
            if token[1] == "-":
                return int(token[-1], 0)
            else:
                return int(token[1], 0)
        except ValueError:
            try:
                return float(token[-1])
            except ValueError:
                return str(token[-1])
    elif token[1].lower() == "true":
        return True
    elif token[1].lower() == "false":
        return False
    elif token[0] is tokenize.STRING or token[1] == "/":
        return token[-1].decode("string-escape")

    raise SyntaxError("malformed expression (%s)" % token[1])


def simple_eval(source):
    """ evaluates the 'source' string into a combination of primitive python objects
    taken from http://effbot.org/zone/simple-iterator-parser.htm"""
    src = cStringIO.StringIO(source).readline
    src = tokenize.generate_tokens(src)
    src = (token for token in src if token[0] is not tokenize.NL)
    res = atom(src.next, src.next())
    return res


class Command(BaseCommand):
    """Show and set configuration values"""

    option_list = BaseCommand.option_list + (
        make_option("-s", "--set", action="store", nargs=2, dest="set", help="set value for key"),
    )
    usage = """Usage: config [key1 [key2 ...]]"
       config --set key value"""

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")
        if options["set"]:
            return self._set_config(*args, **options)
        else:
            return self._get_config(*args, **options)

    def _get_config(self, *args, **options):
        def _on_get_config(config):
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

        return client.core.get_config().addCallback(_on_get_config)

    def _set_config(self, *args, **options):
        config = component.get("CoreConfig")
        key = options["set"][0]
        val = simple_eval(options["set"][1] + " " .join(args))

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

        self.console.write("Setting %s to %s.." % (key, val))
        return client.core.set_config({key: val}).addCallback(on_set_config)

    def complete(self, text):
        return [k for k in component.get("CoreConfig").keys() if k.startswith(text)]
