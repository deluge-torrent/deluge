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

from __future__ import print_function, unicode_literals

import os
import re

WEBUI_JS_DIR = 'deluge/ui/web/js/deluge-all'
# Enabling Debug adds file and line number as comments to the gettext file.
DEBUG = False


def check_missing_markup(js_dir):
    """Search js to check for missed translation markup."""

    # A list of common extjs attributes that are usually marked for translation.
    attr_list = [
        "text: '",
        "msg: '",
        "title: '",
        "fieldLabel: '",
        "boxLabel: '",
        "tooltip: '",
        "header: '",
        "defaultText: '",
        "unit: '",
        r"setText\('",
        r"addButton\('",
    ]

    # Don't match against any of these chars at start of string value.
    except_chars = "' &#"

    # A list of strings that should be skipped shuold the match contain them.
    skip = ['HTTP:']

    # Create a list of the matching strings to search for with the except_chars appended to each one.
    string_re = re.compile(
        '('
        + ')|('.join(['%s[^' + except_chars + "].*'"] * len(attr_list))
        % tuple(attr_list)
        + ')'
    )

    strings = {}
    for root, dnames, files in os.walk(js_dir):
        for filename in files:
            if os.path.splitext(filename)[1] != '.js':
                continue
            for lineno, line in enumerate(open(os.path.join(root, filename))):
                for match in string_re.finditer(line):
                    for string in match.groups():
                        # Ignore string that contains only digits or specificied strings in skip.
                        if (
                            not string
                            or string.split('\'')[1].isdigit()
                            or any(x in string for x in skip)
                        ):
                            continue
                        locations = strings.get(string, [])
                        locations.append(
                            (os.path.join(root, filename), str(lineno + 1))
                        )
                        strings[string] = locations
    return strings


GETTEXT_TPL = (
    'GetText={maps:{},'
    'add:function(string,translation){this.maps[string]=translation},'
    'get:function(string){if (this.maps[string]){string=this.maps[string]} return string}};'
    'function _(string){return GetText.get(string)}'
)
GETTEXT_SUBST_TPL = "GetText.add('{key}','${{escape(_(\"{key}\"))}}')\n"


def create_gettext_js(js_dir):
    string_re = re.compile('_\\(\'(.*?)\'\\)')
    strings = {}
    for root, dnames, files in os.walk(js_dir):
        for filename in files:
            if filename.endswith('.js'):
                filepath = os.path.join(root, filename)
                with open(os.path.join(root, filename)) as _file:
                    for lineno, line in enumerate(_file, 1):
                        for match in string_re.finditer(line):
                            string = match.group(1)
                            locations = strings.get(string, [])
                            locations.append((filepath, lineno))
                            strings[string] = locations

    gettext_file = os.path.join(os.path.dirname(js_dir), 'gettext.js')
    with open(gettext_file, 'w') as fp:
        fp.write(GETTEXT_TPL)
        for key in sorted(strings):
            if DEBUG:
                fp.write(
                    '\n//: %s' % '//: '.join(['%s:%s\n' % x for x in strings[key]])
                )
            fp.write(GETTEXT_SUBST_TPL.format(key=key))
    return gettext_file


if __name__ == '__main__':
    gettext_fname = create_gettext_js(WEBUI_JS_DIR)
    print('Created: %s' % gettext_fname)
    missed_markup = check_missing_markup(WEBUI_JS_DIR)
    if missed_markup:
        print('Possible missed text for translation markup:')
        for text, filenames in missed_markup.iteritems():
            for filename_lineno in filenames:
                print('{0:<58}    {1}'.format(':'.join(filename_lineno), text))
