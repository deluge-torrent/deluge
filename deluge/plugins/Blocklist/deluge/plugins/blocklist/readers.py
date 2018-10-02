# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 John Garland <johnnybg+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import re

from deluge.common import decode_bytes

from .common import IP, BadIP, raises_errors_as

log = logging.getLogger(__name__)


class ReaderParseError(Exception):
    pass


class BaseReader(object):
    """Base reader for blocklist files"""

    def __init__(self, _file):
        """Creates a new BaseReader given a file"""
        self.file = _file

    def open(self):
        """Opens the associated file for reading"""
        return open(self.file)

    def parse(self, line):
        """Extracts ip range from given line"""
        raise NotImplementedError

    def read(self, callback):
        """Calls callback on each ip range in the file"""
        for start, end in self.readranges():
            try:
                callback(IP.parse(start), IP.parse(end))
            except BadIP as ex:
                log.error('Failed to parse IP: %s', ex)
        return self.file

    def is_ignored(self, line):
        """Ignore commented lines and blank lines"""
        line = line.strip()
        return line.startswith('#') or not line

    def is_valid(self):
        """Determines whether file is valid for this reader"""
        blocklist = self.open()
        valid = True
        for line in blocklist:
            line = decode_bytes(line)
            if not self.is_ignored(line):
                try:
                    (start, end) = self.parse(line)
                    if not re.match(r'^(\d{1,3}\.){4}$', start + '.') or not re.match(
                        r'^(\d{1,3}\.){4}$', end + '.'
                    ):
                        valid = False
                except Exception:
                    valid = False
                break
        blocklist.close()
        return valid

    @raises_errors_as(ReaderParseError)
    def readranges(self):
        """Yields each ip range from the file"""
        blocklist = self.open()
        for line in blocklist:
            line = decode_bytes(line)
            if not self.is_ignored(line):
                yield self.parse(line)
        blocklist.close()


class EmuleReader(BaseReader):
    """Blocklist reader for emule style blocklists"""

    def parse(self, line):
        return line.strip().split(' , ')[0].split(' - ')


class SafePeerReader(BaseReader):
    """Blocklist reader for SafePeer style blocklists"""

    def parse(self, line):
        return line.strip().split(':')[-1].split('-')


class PeerGuardianReader(SafePeerReader):
    """Blocklist reader for PeerGuardian style blocklists"""

    pass
