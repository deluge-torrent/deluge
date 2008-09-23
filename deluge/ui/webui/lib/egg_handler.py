#!/usr/bin/env python
#(c) Martijn Voncken, mvoncken@gmail.com
#Same Licence as web.py 0.22
#
"""
static fileserving for web.py
serves 1 directory from a packed egg, using pkg_resourses
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
import pkg_resources

class egg_handler:
    """
    serves files directly from an egg
    """
    resource = "label"
    base_path = "data"
    extensions_map = mimetypes.types_map

    def GET(self, path):
        path = os.path.join(self.base_path, path)
        ctype = self.guess_type(path)

        data = pkg_resources.resource_string(self.resource,path)

        web.header("Content-type", ctype)
        web.header("Cache-Control" , "public, must-revalidate, max-age=86400")
        #web.lastmodified(datetime.datetime.fromtimestamp(fs.st_mtime))
        print data

    def guess_type(self, path):
        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return 'application/octet-stream'

if __name__ == '__main__':
    #example:
    class usr_static(egg_handler):
        resource = "label"
        base_path = "data"

    urls = ('/relative/(.*)','static_handler',
                '/(.*)','usr_static')

    web.run(urls,globals())
