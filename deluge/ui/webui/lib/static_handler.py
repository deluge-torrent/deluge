#!/usr/bin/env python
#(c) Martijn Voncken, mvoncken@gmail.com
#Same Licence as web.py 0.22
#
"""
static fileserving for web.py
without the need for wsgi wrapper magic.
"""
import web
from web import url

import posixpath
import urlparse
import urllib
import mimetypes
import os
import datetime
import cgi
from StringIO import StringIO
mimetypes.init() # try to read system mime.types

class static_handler:
    """
    mostly c&p from SimpleHttpServer
    serves relative from start location
    """
    base_dir = './'
    extensions_map = mimetypes.types_map

    def get_base_dir(self):
        #override this if you have a config that changes the base dir at runtime
        #deluge on windows :(
        return self.base_dir

    def GET(self, path):
        path = self.translate_path(path)
        if os.path.isdir(path):
            if not path.endswith('/'):
                path += "/"
            return self.list_directory(path)

        ctype = self.guess_type(path)

        try:
            f = open(path, 'rb')
        except IOError:
            raise Exception('file not found:%s' % path)
            #web.header("404", "File not found")
            #return
        web.header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        web.header("Content-Length", str(fs[6]))
        web.header("Cache-Control" , "public, must-revalidate, max-age=86400")
        #web.lastmodified(datetime.datetime.fromtimestamp(fs.st_mtime))
        print f.read()

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = urlparse.urlparse(path)[2]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = self.get_base_dir()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path

    def guess_type(self, path):
        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return 'application/octet-stream'


    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().
        #TODO ->use web.py +template!
        """
        try:
            list = os.listdir(path)
        except os.error:
            web.header('404', "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(path))
        f.write("<title>Directory listing for %s</title>\n" % displaypath)
        f.write("<h2>Directory listing for %s</h2>\n" % displaypath)
        f.write("<hr>\n<ul>\n")
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f.write('<li><a href="%s">%s</a>\n'
                    % (urllib.quote(linkname), cgi.escape(displayname)))
        f.write("</ul>\n<hr>\n")
        length = f.tell()
        f.seek(0)

        web.header("Content-type", "text/html")
        web.header("Content-Length", str(length))
        print  f.read()


if __name__ == '__main__':
    #example:
    class usr_static(static_handler):
        base_dir = os.path.expanduser('~')

    urls = ('/relative/(.*)','static_handler',
                '/(.*)','usr_static')

    web.run(urls,globals())
