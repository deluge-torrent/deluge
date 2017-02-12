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

try:
    import deluge.libtorrent as lt
except ImportError:
    import libtorrent as lt

REQUIRED_VERSION = '1.1.1.0'

# XXX: Remove and update required when 1.1.2 is released!
if not hasattr(lt, 'generate_fingerprint'):
    raise ImportError('Deluge %s requires lastest github code from libtorrent RC_1_1 branch.\n'
                      'Ubuntu users can add the develop PPA: ppa:deluge-team/develop' % get_version())

if VersionSplit(lt.__version__) < VersionSplit(REQUIRED_VERSION):
    raise ImportError('Deluge %s requires libtorrent >= %s' % (get_version(), REQUIRED_VERSION))
