# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 John Garland <johnnybg+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
# pylint: disable=redefined-builtin

from __future__ import unicode_literals

import bz2
import gzip
import zipfile


def Zipped(reader):  # NOQA: N802
    """Blocklist reader for zipped blocklists"""

    def _open(self):
        z = zipfile.ZipFile(self.file)
        f = z.open(z.namelist()[0])
        return f

    reader.open = _open
    return reader


def GZipped(reader):  # NOQA: N802
    """Blocklist reader for gzipped blocklists"""

    def _open(self):
        return gzip.open(self.file)

    reader.open = _open
    return reader


def BZipped2(reader):  # NOQA: N802
    """Blocklist reader for bzipped2 blocklists"""

    def _open(self):
        return bz2.BZ2File(self.file)

    reader.open = _open
    return reader
