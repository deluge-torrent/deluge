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

import os

import deluge.common

# Get build_version from installed deluge.
build_version = deluge.common.get_version()
build_dir = os.path.join('freeze', 'Deluge')

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
            f.write('File ' + build_dir + os.path.join(dirname, filename) + '\n')

with open('uninstall_files.nsh', 'w') as f:
    f.write('; Files to uninstall\n')
    for dirname, files in reversed(filedir_list):
        f.write('\n')
        if not dirname:
            dirname = os.sep
        for filename in files:
            f.write('Delete "$INSTDIR%s"\n' % os.path.join(dirname, filename))
        f.write('RMDir "$INSTDIR%s"\n' % dirname)
