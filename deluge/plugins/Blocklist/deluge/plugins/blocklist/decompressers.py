# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 John Garland <johnnybg+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import bz2
import gzip
import zipfile


def Zipped(reader):  # NOQA
    """Blocklist reader for zipped blocklists"""
    def open(self):
        z = zipfile.ZipFile(self.file)
        if hasattr(z, 'open'):
            f = z.open(z.namelist()[0])
        else:
            # Handle python 2.5
            import cStringIO
            f = cStringIO.StringIO(z.read(z.namelist()[0]))
        return f
    reader.open = open
    return reader


def GZipped(reader):  # NOQA
    """Blocklist reader for gzipped blocklists"""
    def open(self):
        return gzip.open(self.file)
    reader.open = open
    return reader


def BZipped2(reader):  # NOQA
    """Blocklist reader for bzipped2 blocklists"""
    def open(self):
        return bz2.BZ2File(self.file)
    reader.open = open
    return reader
