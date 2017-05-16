#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Calum Lind <calumlind@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import contextlib
import os
import sys
import tarfile
from hashlib import sha256
from subprocess import STDOUT, CalledProcessError, call, check_output


sys.path.append('.')
from version import get_version  # NOQA, isort: skip,

try:
    import lzma
except ImportError:
    try:
        from backports import lzma
    except ImportError:
        print('backports.lzma not installed, falling back to `tar`')
        lzma = None


"""Get latest annotated tag"""
try:
    release_tag = check_output('git describe --exact-match --abbrev=0'.split(), stderr=STDOUT)
except CalledProcessError:
    # Fallback to dev build tag.
    dev_tag = check_output('git describe --tags --abbrev=0'.split()).strip()
    release_tag = dev_tag

version = release_tag.split('deluge-')[1]
version_alt = get_version(prefix='deluge-', suffix='.dev0')
release_dir = 'release'
source_dir = os.path.join(release_dir, release_tag)

# TODO: tag found/not found continue? (add option to specify tag)

# TODO: Verify version and date changed in Changelog?
# if check_output(('git grep -l "%s" | grep -v ChangeLog' % version).split()):
#    sys.exit(1)

"""Create release archive"""
try:
    os.mkdir(release_dir)
except OSError:
    pass

print('Creating release archive for ' + release_tag)
call('git archive --format=tar --prefix={tag}/ {tag} | tar -x -C {_dir}'.format(
     tag=release_tag, _dir=release_dir), shell=True)

"""Compress WebUI javascript"""
call(['python', 'minify_web_js.py'])

"""Create source release tarball."""
tarball = release_tag + '.tar.xz'
tarball_path = os.path.join(release_dir, tarball)
if lzma:
    with contextlib.closing(lzma.LZMAFile(tarball_path, mode='w')) as xz_file:
        with tarfile.open(fileobj=xz_file, mode='w') as _file:
            _file.add(source_dir, arcname=release_tag)
else:
    call(['tar', '-cJf', tarball_path, '-C', release_dir, release_tag])

"""Calculate shasum and add to SHASUMS256.txt"""
with open(tarball_path, 'rb') as _file:
    sha256sum = '%s %s' % (sha256(_file.read()).hexdigest(), tarball)
with open(os.path.join(release_dir, 'SHASUMS256.txt'), 'w') as _file:
    _file.write(sha256sum + '\n')
