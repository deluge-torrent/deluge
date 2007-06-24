##
# Copyright 2007 Steve 'Tarka' Smith (tarka@internode.on.net)
# Distributed under the same terms as Deluge
##


from exceptions import Exception
import re, gzip
from socket import inet_aton
from struct import unpack


class TextException(Exception):
    pass

class FormatException(TextException):
    pass

class TextBase:
    
    def __init__(self, fd, regexp):
        print "TextBase loading"
        self.count = 0
        self.fd = fd
        self.re = re.compile(regexp)

    def numentries(self):
        print "Scanning"
        save = self.fd.tell()
        self.fd.seek(0)
        count = 0
        for l in self.fd:
            count += 1
        self.fd.seek(save)
        return count

    def next(self):
        self.count += 1
        
        txt = self.fd.readline()
        if txt == "":
            return False

        match = self.re.search(txt)
        if not match:
            raise FormatException("Couldn't match on line %d: %s (%s)"%(self.count,txt,self.re.pattern))

        g = match.groups()
        start = ".".join(g[0:4])
        end = ".".join(g[4:8])

        return (start, end)

    def close(self):
        self.fd.close()


# This reads PeerGuardian text-formatted block-lists
class PGTextReader(TextBase):

    def __init__(self, fd):
        print "PGTextReader loading"
        regexp = ':(\d+)\.(\d+)\.(\d+)\.(\d+)-(\d+)\.(\d+)\.(\d+)\.(\d+)\s*$'
        TextBase.__init__(self, fd, regexp)


# This reads uncompressed PG text list
class TextReader(PGTextReader):

    def __init__(self, filename):
        print "TextReader loading",filename
        PGTextReader.__init__(self, open(filename, 'r'))


# Reads Emule style blocklists (aka nipfilter)
class MuleReader(TextBase):

    def __init__(self, fd):
        print "MuleReader loading"
        regexp = '0*(\d+)\.0*(\d+)\.0*(\d+)\.0*(\d+)\s*-\s*0*(\d+)\.0*(\d+)\.0*(\d+)\.0*(\d+)\s*,'
        TextBase.__init__(self, fd, regexp)

class GZMuleReader(MuleReader):

    def __init__(self, filename):
        print "GZMuleReader loading",filename
        MuleReader.__init__(self, gzip.open(filename, "r"))


