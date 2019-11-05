# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""
This module is used to handle the importing of libtorrent and also controls
the minimum versions of libtorrent that this version of Deluge supports.

Example:
    >>> from deluge._libtorrent import lt

"""
from __future__ import unicode_literals

from deluge.common import VersionSplit, get_version
from deluge.error import LibtorrentImportError

try:
    import deluge.libtorrent as lt
except ImportError:
    try:
        import libtorrent as lt
    except ImportError as ex:
        raise LibtorrentImportError('No libtorrent library found: %s' % (ex))


REQUIRED_VERSION = '1.1.2.0'
LT_VERSION = lt.__version__

if VersionSplit(LT_VERSION) < VersionSplit(REQUIRED_VERSION):
    raise LibtorrentImportError(
        'Deluge %s requires libtorrent >= %s' % (get_version(), REQUIRED_VERSION)
    )
