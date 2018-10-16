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

"""Minifies the WebUI JS files.

Usage: python minify_web_js.py deluge/ui/web/js/deluge-all

"""

from __future__ import print_function, unicode_literals

import fileinput
import fnmatch
import os
import subprocess
import sys
from distutils.spawn import find_executable

closure_cmd = None
for cmd in ['closure-compiler', 'closure']:
    if find_executable(cmd):
        closure_cmd = cmd
        break


def minify_closure(file_in, file_out):
    try:
        subprocess.check_call(
            [
                closure_cmd,
                '--warning_level',
                'QUIET',
                '--language_in=ECMASCRIPT5',
                '--js',
                file_in,
                '--js_output_file',
                file_out,
            ]
        )
        return True
    except subprocess.CalledProcessError:
        return False


# Closure outputs smallest files but it is a java-based command, so have slimit
# as a python-only fallback.
#
#   deluge-all.js: Closure 127K, Slimit: 143K, JSMin: 162K
#
if not closure_cmd:
    try:
        from slimit import minify as minify
    except ImportError:
        print('Warning: No minifying command found.')
        minify = None


def source_files_list(source_dir):
    scripts = []
    for root, dirnames, filenames in os.walk(source_dir):
        dirnames.sort(reverse=True)
        files = fnmatch.filter(filenames, '*.js')
        files.sort()

        order_file = os.path.join(root, '.order')
        if os.path.isfile(order_file):
            with open(order_file, 'r') as _file:
                for line in _file:
                    if line.startswith('+ '):
                        order_filename = line.split()[1]
                        files.pop(files.index(order_filename))
                        files.insert(0, order_filename)

        # Ensure root directory files are bottom of list.
        if dirnames:
            scripts.extend([os.path.join(root, f) for f in files])
        else:
            for filename in reversed(files):
                scripts.insert(0, os.path.join(root, filename))
    return scripts


def concat_src_files(file_list, fileout_path):
    with open(fileout_path, 'w') as file_out:
        file_in = fileinput.input(file_list)
        file_out.writelines(file_in)


def minify_file(file_debug, file_minified):
    if closure_cmd:
        return minify_closure(file_debug, file_minified)
    elif minify:
        with open(file_minified, 'w') as file_out:
            with open(file_debug, 'r') as file_in:
                file_out.write(minify(file_in.read()))
                return True


def minify_js_dir(source_dir):
    build_name = os.path.basename(source_dir)
    build_dir = os.path.dirname(source_dir)
    file_debug_js = os.path.join(build_dir, build_name + '-debug.js')
    file_minified_js = os.path.join(build_dir, build_name + '.js')
    source_files = source_files_list(source_dir)

    if not source_files:
        print('No js files found, skipping %s' % source_dir)
        return

    concat_src_files(source_files, file_debug_js)
    print('Minifying %s' % source_dir)
    if not minify_file(file_debug_js, file_minified_js):
        print('Warning: Failed minifying files %s, debug only' % source_dir)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        JS_SOURCE_DIRS = [
            'deluge/ui/web/js/deluge-all',
            'deluge/ui/web/js/extjs/ext-extensions',
        ]
    else:
        JS_SOURCE_DIRS = [os.path.abspath(sys.argv[1])]

    for js_source_dir in JS_SOURCE_DIRS:
        minify_js_dir(js_source_dir)
