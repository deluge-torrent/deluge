#
# detect.py
#
# Copyright (C) 2009-2010 John Garland <johnnybg+deluge@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#

from decompressers import Zipped, GZipped, BZipped2
from readers import EmuleReader, SafePeerReader, PeerGuardianReader

COMPRESSION_TYPES = {
    "PK" : "Zip",
    "\x1f\x8b" : "GZip",
    "BZ" : "BZip2"
}

DECOMPRESSERS = {
    "Zip" : Zipped,
    "GZip" : GZipped,
    "BZip2" : BZipped2
}

READERS = {
    "Emule" : EmuleReader,
    "SafePeer" : SafePeerReader,
    "PeerGuardian" : PeerGuardianReader
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
