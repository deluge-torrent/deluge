#
# readers.py
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

from common import raisesErrorsAs, remove_zeros
import re

class ReaderParseError(Exception):
    pass

class BaseReader(object):
    """Base reader for blocklist files"""
    def __init__(self, file):
        """Creates a new BaseReader given a file"""
        self.file = file

    def open(self):
        """Opens the associated file for reading"""
        return open(self.file)

    def parse(self, line):
        """Extracts ip range from given line"""
        raise NotYetImplemented

    def read(self, callback):
        """Calls callback on each ip range in the file"""
        for start, end in self.readranges():
            callback(remove_zeros(start), remove_zeros(end))
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
            if not self.is_ignored(line):
                try:
                    (start, end) = self.parse(line)
                    if not re.match("^(\d{1,3}\.){4}$", start + ".") or \
                       not re.match("^(\d{1,3}\.){4}$", end + "."):
                        valid = False
                except:
                    valid = False
                finally:
                    break
        blocklist.close()
        return valid

    @raisesErrorsAs(ReaderParseError)
    def readranges(self):
        """Yields each ip range from the file"""
        blocklist = self.open()
        for line in blocklist:
            if not self.is_ignored(line):
                yield self.parse(line)
        blocklist.close()

class EmuleReader(BaseReader):
    """Blocklist reader for emule style blocklists"""
    def parse(self, line):
        return line.strip().split(" , ")[0].split(" - ")

class SafePeerReader(BaseReader):
    """Blocklist reader for SafePeer style blocklists"""
    def parse(self, line):
        return line.strip().split(":")[-1].split("-")

class PeerGuardianReader(SafePeerReader):
    """Blocklist reader for PeerGuardian style blocklists"""
    pass
