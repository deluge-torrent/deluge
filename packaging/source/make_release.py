#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Calum Lind <calumlind@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
from __future__ import print_function, unicode_literals

import os.path
from hashlib import sha256
from subprocess import call, check_output

try:
    import lzma
except ImportError:
    try:
        from backports import lzma
    except ImportError:
        print('backports.lzma not installed, falling back to xz shell command')
        lzma = None

# Compress WebUI javascript and gettext.js
call(['python', 'minify_web_js.py'])
call(['python', 'gen_web_gettext.py'])

version = check_output(['python', 'version.py']).strip()

# Create release archive
release_dir = 'dist/release-%s' % version
print('Creating release archive for ' + version)
call('python setup.py --quiet egg_info --egg-base /tmp sdist --formats=tar --dist-dir=%s' % release_dir, shell=True)

# Compress release archive with xz
tar_path = os.path.join(release_dir, 'deluge-%s.tar' % version)
tarxz_path = tar_path + '.xz'
print('Compressing tar (%s) with xz' % tar_path)
if lzma:
    with open(tar_path, 'rb') as tar_file, open(tarxz_path, 'wb') as xz_file:
        xz_file.write(lzma.compress(bytes(tar_file.read()), preset=9 | lzma.PRESET_EXTREME))
else:
    call(['xz', '-e9zkf', tar_path])

# Calculate shasum and add to sha256sums.txt
with open(tarxz_path, 'rb') as _file:
    sha256sum = '%s %s' % (sha256(_file.read()).hexdigest(), os.path.basename(tarxz_path))
with open(os.path.join(release_dir, 'sha256sums.txt'), 'w') as _file:
    _file.write(sha256sum + '\n')

print('Complete: %s' % release_dir)
