#!/usr/bin/env python
#
# Copyright (C) 2011-2013 Calum Lind <calumlind@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""Parses Python and Javascript code for translation strings to create the 'deluge.pot' template for translators"""

import os
import re
from datetime import datetime
from subprocess import call

from version import get_version

# Paths to exclude
EXCLUSIONS = ['deluge/scripts', 'deluge/i18n', 'deluge/tests']
WEBUI_JS_DIR = 'deluge/ui/web/js/deluge-all'
WEBUI_RENDER_DIR = 'deluge/ui/web/render'
INFILES_LIST = 'infiles.list'
POT_FILEPATH = os.path.join('deluge', 'i18n', 'deluge.pot')

RE_EXC_PLUGIN_BUILD = re.compile('deluge\\/plugins\\/.*\\/build')

xgettext_cmd = [
    'xgettext',
    '--from-code=UTF-8',
    '-kN_:1',
    '-f%s' % INFILES_LIST,
    '-o%s' % POT_FILEPATH,
    '--package-name=%s' % 'Deluge',
    '--copyright-holder=%s' % 'Deluge Team',
    '--package-version=%s' % get_version(prefix='deluge-', suffix='.dev0'),
    '--msgid-bugs-address=%s' % 'http://deluge-torrent.org',
]

to_translate = []
for dirpath, dirnames, filenames in os.walk('deluge'):
    for filename in filenames:
        if dirpath not in EXCLUSIONS and not RE_EXC_PLUGIN_BUILD.match(dirpath):
            filepath = os.path.join(dirpath, filename)
            if os.path.splitext(filepath)[1] in ('.py', '.glade'):
                to_translate.append(filepath)
            else:
                if filename.endswith('.xml.in'):
                    gtxt_type = 'gettext/xml'
                elif filename.endswith('.in'):
                    gtxt_type = 'gettext/ini'
                elif filename.endswith('.ui'):
                    gtxt_type = 'gettext/glade'
                else:
                    continue
                call(['intltool-extract', '--quiet', '--type=%s' % gtxt_type, filepath])
                filepath += '.h'
            to_translate.append(filepath)

with open(INFILES_LIST, 'w') as f:
    for line in to_translate:
        f.write(line + '\n')

# Create pot file from file list
call(xgettext_cmd)

# find javascript files
js_to_translate = []
for dirpath, dirnames, filenames in os.walk(WEBUI_JS_DIR):
    for filename in filenames:
        if os.path.splitext(filename)[1] == '.js':
            js_to_translate.append(os.path.join(dirpath, filename))

# find render html files
for dirpath, dirnames, filenames in os.walk(WEBUI_RENDER_DIR):
    for filename in filenames:
        if os.path.splitext(filename)[1] == '.html':
            js_to_translate.append(os.path.join(dirpath, filename))

with open(INFILES_LIST, 'w') as f:
    for line in js_to_translate:
        f.write(line + '\n')

# Force xgettext language to parse javascript and update pot file
# Note: For javascript files xgettext will parse comments, so single apostrophes or quotes are
# flagged as a 'warning: untermined string'. Either ignore warning or edit javascript comment.
call(xgettext_cmd + ['--language=Python', '-j'])

# Replace YEAR and PACKAGE in the copyright message
with open(POT_FILEPATH) as f:
    lines = f.readlines()
with open(POT_FILEPATH, 'w') as f:
    for line in lines:
        if 'YEAR' in line:
            line = line.replace('YEAR', str(datetime.now().year))
        elif 'PACKAGE' in line:
            line = line.replace('PACKAGE', 'Deluge')
        f.write(line)

# Clean up temp files
os.remove(INFILES_LIST)
for filepath in to_translate:
    if filepath.endswith('.h'):
        os.remove(filepath)

print('Created %s' % POT_FILEPATH)
