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

WEBUI_JS_DIR = 'deluge/ui/web/js/deluge-all'
# Enabling Debug adds file and line number as comments to the gettext file.
DEBUG = False


def create_gettext_js(js_dir):
    string_re = re.compile('_\\(\'(.*?)\'\\)')

    strings = {}
    for root, dnames, files in os.walk(js_dir):
        for filename in files:
            if os.path.splitext(filename)[1] == '.js':
                for lineno, line in enumerate(open(os.path.join(root, filename))):
                    for match in string_re.finditer(line):
                        string = match.group(1)
                        locations = strings.get(string, [])
                        locations.append((os.path.basename(filename), lineno + 1))
                        strings[string] = locations

    gettext_tpl = '''GetText={maps:{},\
    add:function(string,translation) {this.maps[string]=translation},\
    get:function(string) {if (this.maps[string]) {string=this.maps[string]} return string}}
    function _(string) {return GetText.get(string)}\
    '''

    gettext_file = os.path.join(os.path.dirname(js_dir), 'gettext.js')
    with open(gettext_file, 'w') as fp:
        fp.write(gettext_tpl)
        for key in sorted(strings.keys()):
            if DEBUG:
                fp.write('\n// %s\n' % ', '.join(['%s:%s' % x for x in strings[key]]))
            fp.write('''GetText.add('%(key)s','${escape(_("%(key)s"))}')\n''' % locals())

if __name__ == '__main__':
    create_gettext_js(WEBUI_JS_DIR)
    print('Created %s' % WEBUI_JS_DIR)
