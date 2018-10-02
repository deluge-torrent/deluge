# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Steve 'Tarka' Smith (tarka@internode.on.net)
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import gzip
import logging
import socket
from struct import unpack

log = logging.getLogger(__name__)


class PGException(Exception):
    pass


# Incrementally reads PeerGuardian blocklists v1 and v2.
# See http://wiki.phoenixlabs.org/wiki/P2B_Format
class PGReader(object):
    def __init__(self, filename):
        log.debug('PGReader loading: %s', filename)

        try:
            with gzip.open(filename, 'rb') as _file:
                self.fd = _file
        except IOError:
            log.debug('Blocklist: PGReader: Incorrect file type or list is corrupt')

        # 4 bytes, should be 0xffffffff
        buf = self.fd.read(4)
        hdr = unpack('l', buf)[0]
        if hdr != -1:
            raise PGException(_('Invalid leader') + ' %d' % hdr)

        magic = self.fd.read(3)
        if magic != 'P2B':
            raise PGException(_('Invalid magic code'))

        buf = self.fd.read(1)
        ver = ord(buf)
        if ver != 1 and ver != 2:
            raise PGException(_('Invalid version') + ' %d' % ver)

    def __next__(self):
        # Skip over the string
        buf = -1
        while buf != 0:
            buf = self.fd.read(1)
            if buf == '':  # EOF
                return False
            buf = ord(buf)

        buf = self.fd.read(4)
        start = socket.inet_ntoa(buf)

        buf = self.fd.read(4)
        end = socket.inet_ntoa(buf)

        return (start, end)

    # Python 2 compatibility
    next = __next__

    def close(self):
        self.fd.close()
