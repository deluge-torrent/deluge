##
# Copyright 2007 Steve 'Tarka' Smith (tarka@internode.on.net)
# Distributed under the same terms as Deluge
##

from exceptions import Exception
from struct import unpack
import gzip, socket

from deluge.log import LOG as log

class PGException(Exception):
    pass

# Incrementally reads PeerGuardian blocklists v1 and v2.
# See http://wiki.phoenixlabs.org/wiki/P2B_Format
class PGReader:

    def __init__(self, filename):
        log.debug("PGReader loading: %s", filename)

        try:
            self.fd = gzip.open(filename, "rb")
        except IOError, e:
           log.debug("Blocklist: PGReader: Incorrect file type or list is corrupt")

        # 4 bytes, should be 0xffffffff
        buf = self.fd.read(4)
        hdr = unpack("l", buf)[0]
        if hdr != -1:
            raise PGException(_("Invalid leader") + " %d"%hdr)

        magic = self.fd.read(3)
        if magic != "P2B":
            raise PGException(_("Invalid magic code"))

        buf = self.fd.read(1)
        ver = ord(buf)
        if ver != 1 and ver != 2:
            raise PGException(_("Invalid version") + " %d" % ver)


    def next(self):

        # Skip over the string
        buf = -1
        while buf != 0:
            buf = self.fd.read(1)
            if buf == "":  # EOF
                return False
            buf = ord(buf)

        buf = self.fd.read(4)
        start = socket.inet_ntoa(buf)

        buf = self.fd.read(4)
        end = socket.inet_ntoa(buf)

        return (start, end)

    def close(self):
        self.fd.close()
