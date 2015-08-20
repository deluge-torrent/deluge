#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""Script to parse javascript files for translation strings and generate gettext.js"""

import os
import re
import sys

if len(sys.argv) != 2:
    WEBUI_JS_DIR = 'deluge/ui/web/js/deluge-all'
else:
    WEBUI_JS_DIR = os.path.abspath(sys.argv[1])

OUTPUT_FILE = os.path.join(os.path.dirname(WEBUI_JS_DIR), 'gettext.js')
STRING_RE = re.compile('_\\(\'(.*?)\'\\)')

strings = {}
for root, dnames, files in os.walk(WEBUI_JS_DIR):
    for filename in files:
        if os.path.splitext(filename)[1] == '.js':
            for lineno, line in enumerate(open(os.path.join(root, filename))):
                for match in STRING_RE.finditer(line):
                    string = match.group(1)
                    locations = strings.get(string, [])
                    locations.append((os.path.basename(filename), lineno + 1))
                    strings[string] = locations

keys = strings.keys()
keys.sort()

gettext_tpl = """/*!
 * Script: gettext.js
 *  A script file that is run through the template renderer in order for translated strings to be used.
 *
 * Copyright (c) 2009 Damien Churchill <damoxc@gmail.com>
 */

GetText = {
    maps: {},
    add: function(string, translation) {
        this.maps[string] = translation;
    },
    get: function(string) {
        if (this.maps[string]) {
            return this.maps[string];
        } else {
            return string;
        }
    }
}

function _(string) {
    return GetText.get(string);
}

"""

with open(OUTPUT_FILE, 'w') as fp:
    fp.write(gettext_tpl)
    for key in keys:
        fp.write('// %s\n' % ', '.join(map(lambda x: '%s:%s' % x, strings[key])))
        fp.write("GetText.add('%(key)s', '${escape(_(\"%(key)s\"))}')\n\n" % locals())

print "Created %s" % OUTPUT_FILE
