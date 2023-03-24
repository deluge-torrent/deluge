#!/usr/bin/env python
#
# Copyright 2014 Calum Lind <calumlind@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import os.path
from hashlib import sha256
from subprocess import call, check_output

sdist_formats = 'xztar'

version = check_output(['python', 'version.py']).strip().decode()

# Create release archive
release_dir = 'dist/release-%s' % version
print('Creating release archive for ' + version)

call(
    'python setup.py --quiet egg_info --egg-base /tmp sdist --formats=%s --dist-dir=%s'
    % (sdist_formats, release_dir),
    shell=True,
)


if sdist_formats == 'xztar':
    tarxz_path = os.path.join(release_dir, 'deluge-%s.tar.xz' % version)
else:
    # Compress release archive with xz
    tar_path = os.path.join(release_dir, 'deluge-%s.tar' % version)
    tarxz_path = tar_path + '.xz'
    print('Compressing tar (%s) with xz' % tar_path)
    try:
        from backports import lzma
    except ImportError:
        print('backports.lzma not installed, falling back to xz shell command')
        call(['xz', '-e9zkf', tar_path])
    else:
        with open(tar_path, 'rb') as tar_file, open(tarxz_path, 'wb') as xz_file:
            xz_file.write(
                lzma.compress(bytes(tar_file.read()), preset=9 | lzma.PRESET_EXTREME)
            )

# Calculate shasum and add to sha256sums.txt
with open(tarxz_path, 'rb') as _file:
    sha256sum = '{} {}'.format(
        sha256(_file.read()).hexdigest(),
        os.path.basename(tarxz_path),
    )
with open(os.path.join(release_dir, 'sha256sums.txt'), 'w') as _file:
    _file.write(sha256sum + '\n')

print('Complete: %s' % release_dir)
