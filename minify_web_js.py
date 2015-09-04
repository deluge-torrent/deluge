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

import fileinput
import fnmatch
import os
import sys


def module_exists(module_name):
    try:
        __import__(module_name)
    except ImportError:
        return False
    else:
        return True

# Imports sorted by resulting file size.
if module_exists('closure'):
    def minify_closure(file_in, file_out):
        import subprocess
        subprocess.call(['closure', '--js', file_in, '--js_output_file', file_out,
                        '-W', 'QUIET'])
elif module_exists('slimit'):
    from slimit import minify
elif module_exists('jsmin'):
    from jsmin import jsmin as minify
elif module_exists('rjsmin'):
    from rjsmin import jsmin as minify
else:
    raise ImportError('Minifying WebUI JS requires slimit, jsmin or rjsmin')


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
    try:
        minify_closure(file_debug, file_minified)
    except NameError:
        with open(file_minified, 'w') as file_out:
            with open(file_debug, 'r') as file_in:
                file_out.write(minify(file_in.read()))


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
    minify_file(file_debug_js, file_minified_js)
    print('Minified %s' % source_dir)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        JS_SOURCE_DIRS = ['deluge/ui/web/js/deluge-all', 'deluge/ui/web/js/extjs/ext-extensions']
    else:
        JS_SOURCE_DIRS = [os.path.abspath(sys.argv[1])]

    for source_dir in JS_SOURCE_DIRS:
        minify_js_dir(source_dir)
