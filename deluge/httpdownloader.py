#
# httpdownloader.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
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

from twisted.web import client, http
from twisted.web.error import PageRedirect
from twisted.python.failure import Failure
from twisted.internet import reactor
from twisted.internet import ssl
from mp.network import https
from common import get_version
import base64
import logging
import os.path
import zlib

log = logging.getLogger(__name__)

proxy_host = None
proxy_port = None
proxy_user = None
proxy_pass = None
self.proxy_type = proxy_type
self.proxy_host = proxy_host
self.proxy_port = proxy_port
self.proxy_user = proxy_user
self.proxy_pass = proxy_pass

client.core.get_config_values(["proxy_type", "proxy_host",
                                     "proxy_port", "proxy_user", "proxy_pass"])

class ProxyHTTPClientFactory(client.HTTPClientFactory):

    def __init__(self, uri, proxy_host, proxy_port, *args, **kwargs):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        client.HTTPClientFactory.__init__(self, uri, *args, **kwargs)

    def buildProtocol(self, addr):
        logging.info('Connected')
        return client.HTTPClientFactory.buildProtocol(self, addr)

    def setURL(self, url):
        #logging.debug('Setting URL: %s', url)
        prev_host = getattr(self, 'host', None)
        client.HTTPClientFactory.setURL(self, url)
        #logging.debug('After parse: %s %s %s %s', self.scheme, self.host, self.port, self.path)
        self.path = url
        if prev_host!=self.host:
            self.headers['Host'] = self.host
        self.host = self.proxy_host
        self.port = self.proxy_port

class ProxyHTTPDownloader(client.HTTPDownloader):

    def __init__(self, uri, file, proxy_host, proxy_port, *args, **kwargs):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        if 'followRedirect' in kwargs:
            del kwargs['followRedirect']
        client.HTTPDownloader.__init__(self, uri, file, *args, **kwargs)

    def buildProtocol(self, addr):
        #logging.info('Connected')
        return client.HTTPDownloader.buildProtocol(self, addr)

    def setURL(self, url):
        #logging.debug('Setting URL: %s', url)
        prev_host = getattr(self, 'host', None)
        client.HTTPDownloader.setURL(self, url)
        #logging.debug('After parse: %s %s %s %s', self.scheme, self.host, self.port, self.path)
        self.path = url
        if prev_host!=self.host:
            self.headers['Host'] = self.host
        self.host = self.proxy_host
        self.port = self.proxy_port

def proxifyFactory(factory, host, port, use_ssl = False):
    if not proxy_host or not proxy_port:
        logging.debug('No proxy information - default behaviour')
        if use_ssl:
            reactor.connectSSL(host, port, factory, ssl.ClientContextFactory())
        else:
            reactor.connectTCP(host, port, factory)
        return
    https_factory = https.ProxyHTTPSConnectionFactory(factory, host, port, use_ssl, proxy_user, proxy_pass)
    reactor.connectTCP(proxy_host, proxy_port, https_factory)

class HTTPDownloader(client.HTTPDownloader):
    """
    Factory class for downloading files and keeping track of progress.
    """
    def __init__(self, url, filename, part_callback=None, headers=None,
                 force_filename=False, allow_compression=True):
        """
        :param url: the url to download from
        :type url: string
        :param filename: the filename to save the file as
        :type filename: string
        :param force_filename: forces use of the supplied filename, regardless of header content
        :type force_filename: bool
        :param part_callback: a function to be called when a part of data
            is received, it's signature should be: func(data, current_length, total_length)
        :type part_callback: function
        :param headers: any optional headers to send
        :type headers: dictionary
        """
        self.part_callback = part_callback
        self.current_length = 0
        self.decoder = None
        self.value = filename
        self.force_filename = force_filename
        self.allow_compression = allow_compression
        agent = "Deluge/%s (http://deluge-torrent.org)" % get_version()
        client.HTTPDownloader.__init__(self, url, filename, headers=headers, agent=agent)

    def gotStatus(self, version, status, message):
        self.code = int(status)
        client.HTTPDownloader.gotStatus(self, version, status, message)

    def gotHeaders(self, headers):
        if self.code == http.OK:
            if "content-length" in headers:
                self.total_length = int(headers["content-length"][0])
            else:
                self.total_length = 0

            if self.allow_compression and "content-encoding" in headers and \
               headers["content-encoding"][0] in ("gzip", "x-gzip", "deflate"):
                # Adding 32 to the wbits enables gzip & zlib decoding (with automatic header detection)
                # Adding 16 just enables gzip decoding (no zlib)
                self.decoder = zlib.decompressobj(zlib.MAX_WBITS + 32)

            if "content-disposition" in headers and not self.force_filename:
                new_file_name = str(headers["content-disposition"][0]).split(";")[1].split("=")[1]
                new_file_name = sanitise_filename(new_file_name)
                new_file_name = os.path.join(os.path.split(self.fileName)[0], new_file_name)

                count = 1
                fileroot = os.path.splitext(new_file_name)[0]
                fileext = os.path.splitext(new_file_name)[1]
                while os.path.isfile(new_file_name):
                    # Increment filename if already exists
                    new_file_name = "%s-%s%s" % (fileroot, count, fileext)
                    count += 1

                self.fileName = new_file_name
                self.value = new_file_name

        elif self.code in (http.MOVED_PERMANENTLY, http.FOUND, http.SEE_OTHER, http.TEMPORARY_REDIRECT):
            location = headers["location"][0]
            error = PageRedirect(self.code, location=location)
            self.noPage(Failure(error))

        return client.HTTPDownloader.gotHeaders(self, headers)

    def pagePart(self, data):
        if self.code == http.OK:
            self.current_length += len(data)
            if self.decoder:
                data = self.decoder.decompress(data)
            if self.part_callback:
                self.part_callback(data, self.current_length, self.total_length)

        return client.HTTPDownloader.pagePart(self, data)

    def pageEnd(self):
        if self.decoder:
            data = self.decoder.flush()
            self.current_length -= len(data)
            self.decoder = None
            self.pagePart(data)

        return client.HTTPDownloader.pageEnd(self)

def sanitise_filename(filename):
    """
    Sanitises a filename to use as a download destination file.
    Logs any filenames that could be considered malicious.

    :param filename: the filename to sanitise
    :type filename: string
    :returns: the sanitised filename
    :rtype: string
    """

    # Remove any quotes
    filename = filename.strip("'\"")

    if os.path.basename(filename) != filename:
        # Dodgy server, log it
        log.warning("Potentially malicious server: trying to write to file '%s'" % filename)
        # Only use the basename
        filename = os.path.basename(filename)

    filename = filename.strip()
    if filename.startswith(".") or ";" in filename or "|" in filename:
        # Dodgy server, log it
        log.warning("Potentially malicious server: trying to write to file '%s'" % filename)

    return filename

def download_file(url, filename, callback=None, headers=None,
                  force_filename=False, allow_compression=True):
    """
    Downloads a file from a specific URL and returns a Deferred.  You can also
    specify a callback function to be called as parts are received.

    :param url: the url to download from
    :type url: string
    :param filename: the filename to save the file as
    :type filename: string
    :param callback: a function to be called when a part of data is received,
         it's signature should be: func(data, current_length, total_length)
    :type callback: function
    :param headers: any optional headers to send
    :type headers: dictionary
    :param force_filename: force us to use the filename specified rather than
                           one the server may suggest
    :type force_filename: boolean
    :param allow_compression: allows gzip & deflate decoding
    :type allow_compression: boolean

    :returns: the filename of the downloaded file
    :rtype: Deferred

    :raises t.w.e.PageRedirect: when server responds with a temporary redirect
         or permanently moved.
    :raises t.w.e.Error: for all other HTTP response errors (besides OK)
    """
    url = str(url)
    filename = str(filename)
    if headers:
        for key, value in headers.items():
            headers[str(key)] = str(value)

    if allow_compression:
        if not headers:
            headers = {}
        headers["accept-encoding"] = "deflate, gzip, x-gzip"

    # In twisted 13.1.0 the _parse() function was replaced by the _URI class 
    if hasattr(client, '_parse'):
        scheme, host, port, path = client._parse(url)
    else:
        from twisted.web.client import _URI
        uri = _URI.fromBytes(url)
        scheme = uri.scheme
        host = uri.host
        port = uri.port
        path = uri.path

    factory = proxyFactoryFactory(url, proxy_host, proxy_port, followRedirect = 0, *args, **kwargs)
    if scheme == "https":
        from twisted.internet import ssl
        reactor.connectSSL(self.proxy_url, self.proxy_port,factory, contextFactory)
    else:
        reactor.connectTCP(proxy_host, proxy_port, factory)

    return factory.deferred
