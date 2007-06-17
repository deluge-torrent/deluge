##
# Copyright 2007 Steve 'Tarka' Smith (tarka@internode.on.net)
# Distributed under the same terms as Deluge
##


from exceptions import Exception
import re

class TextException(Exception):
    pass

class FormatException(TextException):
    pass

# This reads text-formatted block-lists
class TextReader:
    
    def __init__(self, filename):
        print "TextReader loading",filename
        self.count = 0

        # FIXME: Catch or just leave?
        self.fd = open(filename, 'r')
        
        self.re = re.compile(':(\d+\.\d+\.\d+\.\d+)-(\d+\.\d+\.\d+\.\d+)\s*$')

    def next(self):
        self.count += 1
        
        txt = self.fd.readline()
        if txt == "":
            return False

        match = self.re.search(txt)
        if not match:
            raise FormatException("Couldn't match on line %d"%self.count)

        return match.groups()

    def close(self):
        self.fd.close()

