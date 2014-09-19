# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 John Garland <johnnybg+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from .decompressers import BZipped2, GZipped, Zipped
from .readers import EmuleReader, PeerGuardianReader, SafePeerReader

COMPRESSION_TYPES = {
    "PK": "Zip",
    "\x1f\x8b": "GZip",
    "BZ": "BZip2"
}

DECOMPRESSERS = {
    "Zip": Zipped,
    "GZip": GZipped,
    "BZip2": BZipped2
}

READERS = {
    "Emule": EmuleReader,
    "SafePeer": SafePeerReader,
    "PeerGuardian": PeerGuardianReader
}


class UnknownFormatError(Exception):
    pass


def detect_compression(filename):
    f = open(filename, "rb")
    magic_number = f.read(2)
    f.close()
    return COMPRESSION_TYPES.get(magic_number, "")


def detect_format(filename, compression=""):
    format = ""
    for reader in READERS:
        if create_reader(reader, compression)(filename).is_valid():
            format = reader
            break
    return format


def create_reader(format, compression=""):
    reader = READERS.get(format)
    if reader and compression:
        decompressor = DECOMPRESSERS.get(compression)
        if decompressor:
            reader = decompressor(reader)
    return reader
