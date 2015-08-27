#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 Calum Lind <calumlind@gmail.com>
# Copyright (C) 2010 Damien Churchill <damoxc@gmail.com>
# Copyright (C) 2009-2010 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Jesper Lund <mail@jesperlund.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import glob
import os
import re
import shutil
import sys

import bbfreeze
import gtk
from win32verstamp import stamp

import deluge.common


class VersionInfo(object):
    def __init__(self, version, internalname=None, originalfilename=None,
                 comments=None, company=None, description=None,
                 copyright=None, trademarks=None, product=None, dll=False,
                 debug=False, verbose=True):
        parts = version.split(".")
        while len(parts) < 4:
            parts.append("0")
        self.version = ".".join(parts)
        self.internal_name = internalname
        self.original_filename = originalfilename
        self.comments = comments
        self.company = company
        self.description = description
        self.copyright = copyright
        self.trademarks = trademarks
        self.product = product
        self.dll = dll
        self.debug = debug
        self.verbose = verbose

DEBUG = False
if len(sys.argv) == 2 and sys.argv[1].lower() == "debug":
    DEBUG = True

# Get build_version from installed deluge.
build_version = deluge.common.get_version()
python_path = os.path.dirname(sys.executable)
if python_path.endswith("Scripts"):
    python_path = python_path[:-8]
gtk_root = os.path.join(gtk.__path__[0], "..", "runtime")
build_dir = os.path.join("build-win32", "deluge-bbfreeze-" + build_version)

if DEBUG:
    print("Python Path: %s" % python_path)
    print("Gtk Path: %s" % gtk_root)
    print("bbfreeze Output Path: %s" % build_dir)

print("Freezing Deluge %s..." % build_version)
# Disable printing to console for bbfreezing.
if not DEBUG:
    sys.stdout = open(os.devnull, "w")

# Include python modules not picked up automatically by bbfreeze.
includes = ("libtorrent", "cairo", "pangocairo", "atk", "pango", "twisted.internet.utils",
            "gio", "gzip", "email.mime.multipart", "email.mime.text", "_cffi_backend")
excludes = ("numpy", "OpenGL", "psyco", "win32ui")


def recipe_gtk_override(mf):
    # Override bbfreeze function so that it includes all gtk libraries
    # in the installer so users don't require a separate GTK+ installation.
    return True
bbfreeze.recipes.recipe_gtk_and_friends = recipe_gtk_override

fzr = bbfreeze.Freezer(build_dir, includes=includes, excludes=excludes)
fzr.include_py = False
fzr.setIcon(os.path.join(os.path.dirname(deluge.common.__file__), "ui", "data", "pixmaps", "deluge.ico"))

# TODO: Can/should we grab the script list from setup.py entry_points somehow.

# Hide cmd console popup for these console entries force gui_script True.
force_gui = ["deluge-web", "deluged", "deluge-console"]
script_list = []
for script in glob.glob(os.path.join(python_path, "Scripts\\deluge*-script.py*")):
    # Copy the scripts to remove the '-script' suffix before adding to freezer.
    new_script = script.replace("-script", "")
    shutil.copy(script, new_script)

    gui_script = False
    script_splitext = os.path.splitext(os.path.basename(new_script))
    if script_splitext[1] == ".pyw" or script_splitext[0] in force_gui:
        gui_script = True
    try:
        fzr.addScript(new_script, gui_only=gui_script)
        script_list.append(new_script)
    except:
        os.remove(script)

# Start the freezing process.
fzr()

# Clean up the duplicated scripts.
for script in script_list:
    os.remove(script)

# Exclude files which are already included in GTK or Windows.
excludeDlls = ("MSIMG32.dll", "MSVCR90.dll", "MSVCP90.dll", "POWRPROF.dll", "DNSAPI.dll", "USP10.dll")
for dll in excludeDlls:
    try:
        os.remove(os.path.join(build_dir, dll))
    except OSError:
        pass

# Re-enable printing.
if not DEBUG:
    sys.stdout = sys.__stdout__

# Copy gtk locale files.
gtk_locale = os.path.join(gtk_root, 'share/locale')
locale_include_list = ['gtk20.mo', 'locale.alias']


def ignored_files(adir, filenames):
    return [
        filename for filename in filenames
        if not os.path.isdir(os.path.join(adir, filename))
        and filename not in locale_include_list
    ]
shutil.copytree(gtk_locale, os.path.join(build_dir, 'share/locale'), ignore=ignored_files)

# Copy gtk theme files.
theme_include_list = [
    [gtk_root, "share/icons/hicolor/index.theme"],
    [gtk_root, "lib/gtk-2.0/2.10.0/engines"],
    [gtk_root, "share/themes/MS-Windows"],
    ["DelugeStart Theme", "lib/gtk-2.0/2.10.0/engines/libmurrine.dll"],
    ["DelugeStart Theme", "share/themes/DelugeStart"],
    ["DelugeStart Theme", "etc/gtk-2.0/gtkrc"]
]
for path_root, path in theme_include_list:
    full_path = os.path.join(path_root, path)
    if os.path.isdir(full_path):
        shutil.copytree(full_path, os.path.join(build_dir, path))
    else:
        dst_dir = os.path.join(build_dir, os.path.dirname(path))
        try:
            os.makedirs(dst_dir)
        except:
            pass
        shutil.copy(full_path, dst_dir)

# Add version information to exe files.
for script in script_list:
    script_exe = os.path.splitext(os.path.basename(script))[0] + ".exe"
    # Don't add to dev build versions.
    if not re.search('[a-zA-Z_-]', build_version):
        versionInfo = VersionInfo(build_version,
                                  description="Deluge Bittorrent Client",
                                  company="Deluge Team",
                                  product="Deluge",
                                  copyright="GPLv3")
        stamp(os.path.join(build_dir, script_exe), versionInfo)

# Copy version info to file for nsis script.
with open('VERSION.tmp', 'w') as ver_file:
    ver_file.write("build_version = \"%s\"" % build_version)
