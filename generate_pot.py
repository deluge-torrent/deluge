#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
EXCLUSIONS = [
    "deluge/scripts",
    "deluge/i18n",
    "deluge/tests",
]
webui_js_dir = "deluge/ui/web/js/deluge-all"
infiles_list = "infiles.list"
pot_filepath = os.path.join("deluge", "i18n", "deluge.pot")

re_exc_plugin_build = re.compile("deluge\/plugins\/.*\/build")

xgettext_cmd = [
    "xgettext",
    "--from-code=UTF-8",
    "-kN_:1",
    "-f%s" % infiles_list,
    "-o%s" % pot_filepath,
    "--package-name=%s" % "Deluge",
    "--copyright-holder=%s" % "Deluge Team",
    "--package-version=%s" % get_version(prefix='deluge-', suffix='.dev0'),
    "--msgid-bugs-address=%s" % "http://deluge-torrent.org",
]

to_translate = []
for (dirpath, dirnames, filenames) in os.walk("deluge"):
    for filename in filenames:
        if dirpath not in EXCLUSIONS and not re_exc_plugin_build.match(dirpath):
            filepath = os.path.join(dirpath, filename)
            if os.path.splitext(filepath)[1] in (".py", ".glade"):
                to_translate.append(filepath)
            elif filename.endswith(".in"):
                call(["intltool-extract", "--quiet", "--type=gettext/ini", filepath])
                to_translate.append(filepath + ".h")
            elif filename.endswith(".ui"):
                call(["intltool-extract", "--quiet", "--type=gettext/glade", filepath])
                to_translate.append(filepath + ".h")

with open(infiles_list, "wb") as f:
    for line in to_translate:
        f.write(line + "\n")

# Create pot file from file list
call(xgettext_cmd)

# find javascript files
js_to_translate = []
for (dirpath, dirnames, filenames) in os.walk(webui_js_dir):
    for filename in filenames:
        if os.path.splitext(filename)[1] == ".js":
            js_to_translate.append(os.path.join(dirpath, filename))

with open(infiles_list, "wb") as f:
    for line in js_to_translate:
        f.write(line + "\n")

# Force xgettext language to parse javascript and update pot file
# Note: For javascript files xgettext will parse comments, so single apostrophes or quotes are
# flagged as a 'warning: untermined string'. Either ignore warning or edit javascript comment.
output = call(xgettext_cmd + ["--language=Python", "-j"])

# Replace YEAR and PACKAGE in the copyright message
with open(pot_filepath, "r") as f:
    lines = f.readlines()
with open(pot_filepath, "w") as f:
    for line in lines:
        if "YEAR" in line:
            line = line.replace("YEAR", str(datetime.now().year))
        elif "PACKAGE" in line:
            line = line.replace("PACKAGE", "Deluge")
        f.write(line)

# Clean up temp files
os.remove(infiles_list)
for filepath in to_translate:
    if filepath.endswith(".h"):
        os.remove(filepath)

print "Created %s" % pot_filepath
