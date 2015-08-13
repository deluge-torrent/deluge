#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Calum Lind <calumlind@gmail.com>
# Copyright (C) 2010 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""Minifies the Webui JS files.

Usage: python minify_web_js.py deluge/ui/web/js/deluge-all

"""

import fileinput
import fnmatch
import os
import sys

from slimit import minify

if len(sys.argv) != 2:
    print 'Specify a source js directory, e.g. deluge/ui/web/js/deluge-all'
    sys.exit(1)

SOURCE_DIR = os.path.abspath(sys.argv[1])
BUILD_NAME = os.path.basename(SOURCE_DIR)
BUILD_DIR = os.path.dirname(SOURCE_DIR)
SRC_FILE_LIST = []

for root, dirnames, filenames in os.walk(SOURCE_DIR):
    dirnames.sort(reverse=True)
    filenames_js = fnmatch.filter(filenames, '*.js')
    filenames_js.sort()

    order_file = os.path.join(root, '.order')
    if os.path.isfile(order_file):
        with open(order_file, 'r') as _file:
            for line in _file:
                line = line.strip()
                if not line or line[0] == '#':
                    continue
                order_pos, order_filename = line.split()
                filenames_js.pop(filenames_js.index(order_filename))
                if order_pos == '+':
                    filenames_js.insert(0, order_filename)

    # Ensure root directory files are bottom of list.
    if dirnames:
        for filename in filenames_js:
            SRC_FILE_LIST.append(os.path.join(root, filename))
    else:
        for filename in reversed(filenames_js):
            SRC_FILE_LIST.insert(0, os.path.join(root, filename))

if not SRC_FILE_LIST:
    print 'No js files found'
    sys.exit(1)

print 'Minifying %s ...' % BUILD_NAME

# Create the unminified debug file.
file_debug_js = os.path.join(BUILD_DIR, BUILD_NAME + '-debug.js')
with open(file_debug_js, 'w') as _file:
    input_lines = fileinput.input(SRC_FILE_LIST)
    _file.writelines(input_lines)

file_minified_js = os.path.join(BUILD_DIR, BUILD_NAME + '.js')
with open(file_minified_js, 'w') as file_out:
    with open(file_debug_js, 'r') as file_in:
        file_out.write(minify(file_in.read()))
