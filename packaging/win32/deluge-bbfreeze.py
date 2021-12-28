#!/usr/bin/env python
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
# isort:skip_file

import glob
import os
import re
import shutil
import sys


import bbfreeze
import gtk
from win32verstamp import stamp

import deluge.common


class VersionInfo:
    def __init__(
        self,
        version,
        internalname=None,
        originalfilename=None,
        comments=None,
        company=None,
        description=None,
        _copyright=None,
        trademarks=None,
        product=None,
        dll=False,
        debug=False,
        verbose=True,
    ):
        parts = version.split('.')
        while len(parts) < 4:
            parts.append('0')
        self.version = '.'.join(parts)
        self.internal_name = internalname
        self.original_filename = originalfilename
        self.comments = comments
        self.company = company
        self.description = description
        self.copyright = _copyright
        self.trademarks = trademarks
        self.product = product
        self.dll = dll
        self.debug = debug
        self.verbose = verbose


DEBUG = False
if len(sys.argv) == 2 and sys.argv[1].lower() == 'debug':
    DEBUG = True

# Get build_version from installed deluge.
build_version = deluge.common.get_version()
python_path = os.path.dirname(sys.executable)
if python_path.endswith('Scripts'):
    python_path = python_path[:-8]
gtk_root = os.path.join(gtk.__path__[0], '..', 'runtime')
build_dir = os.path.join('build-win32', 'deluge-bbfreeze-' + build_version)

if DEBUG:
    print('Python Path: %s' % python_path)
    print('Gtk Path: %s' % gtk_root)
    print('bbfreeze Output Path: %s' % build_dir)

print('Freezing Deluge %s...' % build_version)
# Disable printing to console for bbfreezing.
if not DEBUG:
    sys.stdout = open(os.devnull, 'w')

# Include python modules not picked up automatically by bbfreeze.
includes = (
    'libtorrent',
    'cairo',
    'pangocairo',
    'atk',
    'pango',
    'twisted.internet.utils',
    'gio',
    'gzip',
    'email.mime.multipart',
    'email.mime.text',
    '_cffi_backend',
)
excludes = ('numpy', 'OpenGL', 'psyco', 'win32ui', 'unittest')


def recipe_gtk_override(mf):
    # Override bbfreeze function so that it includes all gtk libraries
    # in the installer so users don't require a separate GTK+ installation.
    return True


bbfreeze.recipes.recipe_gtk_and_friends = recipe_gtk_override

# Workaround for "ImportError: The 'packaging' package is required" with setuptools > 18.8.
# (https://github.com/pypa/setuptools/issues/517)
bbfreeze.recipes.recipe_pkg_resources = bbfreeze.recipes.include_whole_package(
    'pkg_resources'
)

fzr = bbfreeze.Freezer(build_dir, includes=includes, excludes=excludes)
fzr.include_py = False
fzr.setIcon(
    os.path.join(
        os.path.dirname(deluge.common.__file__), 'ui', 'data', 'pixmaps', 'deluge.ico'
    )
)

# TODO: Can/should we grab the script list from setup.py entry_points somehow.

# Hide cmd console popup for these console entries force gui_script True.
force_gui = ['deluge-web', 'deluged']

for force_script in force_gui:
    script_path = os.path.join(python_path, 'Scripts', force_script + '-script.py')
    shutil.copy(script_path, script_path.replace('script', 'debug-script'))

script_list = []
for script in glob.glob(os.path.join(python_path, 'Scripts\\deluge*-script.py*')):
    # Copy the scripts to remove the '-script' suffix before adding to freezer.
    new_script = script.replace('-script', '')
    shutil.copy(script, new_script)

    gui_script = False
    script_splitext = os.path.splitext(os.path.basename(new_script))
    if script_splitext[1] == '.pyw' or script_splitext[0] in force_gui:
        gui_script = True
    try:
        fzr.addScript(new_script, gui_only=gui_script)
        script_list.append(new_script)
    except Exception:
        os.remove(script)

# Start the freezing process.
fzr()

# Clean up the duplicated scripts.
for script in script_list:
    os.remove(script)

# Exclude files which are already included in GTK or Windows. Also exclude unneeded pygame dlls.
exclude_dlls = (
    'MSIMG32.dll',
    'MSVCR90.dll',
    'MSVCP90.dll',
    'MSVCR120.dll',
    'POWRPROF.dll',
    'DNSAPI.dll',
    'USP10.dll',
    'MPR.dll',
    'jpeg.dll',
    'libfreetype-6.dll',
    'libpng12-0.dll',
    'libtiff.dll',
    'SDL_image.dll',
    'SDL_ttf.dll',
)
for exclude_dll in exclude_dlls:
    try:
        os.remove(os.path.join(build_dir, exclude_dll))
    except OSError:
        pass

# Re-enable printing.
if not DEBUG:
    sys.stdout = sys.__stdout__

# Copy gtk locale files.
gtk_locale = os.path.join(gtk_root, 'share/locale')
locale_include_list = ['gtk20.mo', 'locale.alias']


def ignored_files(adir, ignore_filenames):
    return [
        ignore_file
        for ignore_file in ignore_filenames
        if not os.path.isdir(os.path.join(adir, ignore_file))
        and ignore_file not in locale_include_list
    ]


shutil.copytree(
    gtk_locale, os.path.join(build_dir, 'share/locale'), ignore=ignored_files
)

# Copy gtk theme files.
theme_include_list = [
    [gtk_root, 'share/icons/hicolor/index.theme'],
    [gtk_root, 'lib/gtk-2.0/2.10.0/engines'],
    [gtk_root, 'share/themes/MS-Windows'],
    ['DelugeStart Theme', 'lib/gtk-2.0/2.10.0/engines/libmurrine.dll'],
    ['DelugeStart Theme', 'share/themes/DelugeStart'],
    ['DelugeStart Theme', 'etc/gtk-2.0/gtkrc'],
]
for path_root, path in theme_include_list:
    full_path = os.path.join(path_root, path)
    if os.path.isdir(full_path):
        shutil.copytree(full_path, os.path.join(build_dir, path))
    else:
        dst_dir = os.path.join(build_dir, os.path.dirname(path))
        try:
            os.makedirs(dst_dir)
        except OSError:
            pass
        shutil.copy(full_path, dst_dir)

# Add version information to exe files.
for script in script_list:
    script_exe = os.path.splitext(os.path.basename(script))[0] + '.exe'
    # Don't add to dev build versions.
    if not re.search('[a-zA-Z_-]', build_version):
        version_info = VersionInfo(
            build_version,
            description='Deluge Bittorrent Client',
            company='Deluge Team',
            product='Deluge',
            _copyright='Deluge Team',
        )
        stamp(os.path.join(build_dir, script_exe), version_info)

# Copy version info to file for nsis script.
with open('VERSION.tmp', 'w') as ver_file:
    ver_file.write('build_version = "%s"' % build_version)

# Create the install and uninstall file list for NSIS.
filedir_list = []
for root, dirnames, filenames in os.walk(build_dir):
    dirnames.sort()
    filenames.sort()
    filedir_list.append((root[len(build_dir) :], filenames))

with open('install_files.nsh', 'w') as f:
    f.write('; Files to install\n')
    for dirname, files in filedir_list:
        if not dirname:
            dirname = os.sep
        f.write('\nSetOutPath "$INSTDIR%s"\n' % dirname)
        for filename in files:
            f.write('File "${BBFREEZE_DIR}%s"\n' % os.path.join(dirname, filename))

with open('uninstall_files.nsh', 'w') as f:
    f.write('; Files to uninstall\n')
    for dirname, files in reversed(filedir_list):
        f.write('\n')
        if not dirname:
            dirname = os.sep
        for filename in files:
            f.write('Delete "$INSTDIR%s"\n' % os.path.join(dirname, filename))
        f.write('RMDir "$INSTDIR%s"\n' % dirname)
