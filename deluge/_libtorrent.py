# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""
This module is used to handle the importing of libtorrent.

We use this module to control what versions of libtorrent this version of Deluge
supports.

** Usage **

>>> from deluge._libtorrent import lt

"""

REQUIRED_VERSION = "1.0.6.0"


def check_version(libtorrent):
    from deluge.common import VersionSplit
    if VersionSplit(libtorrent.version) < VersionSplit(REQUIRED_VERSION):
        raise ImportError("This version of Deluge requires libtorrent >=%s!" % REQUIRED_VERSION)

try:
    import deluge.libtorrent as lt
    check_version(lt)
except ImportError:
    import libtorrent as lt
    check_version(lt)
