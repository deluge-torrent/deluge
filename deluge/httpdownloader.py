# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging
import os.path
import zlib
from urlparse import urljoin

from twisted.internet import reactor
from twisted.python.failure import Failure
from twisted.web import client, http
from twisted.web.error import PageRedirect

from deluge.common import get_version

log = logging.getLogger(__name__)


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
        self.total_length = 0
        self.decoder = None
        self.value = filename
        self.force_filename = force_filename
        self.allow_compression = allow_compression
        self.code = None
        agent = "Deluge/%s (http://deluge-torrent.org)" % get_version()
        client.HTTPDownloader.__init__(self, url, filename, headers=headers, agent=agent)

    def gotStatus(self, version, status, message):  # NOQA
        self.code = int(status)
        client.HTTPDownloader.gotStatus(self, version, status, message)

    def gotHeaders(self, headers):  # NOQA
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
                new_file_name = os.path.join(os.path.split(self.value)[0], new_file_name)

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

    def pagePart(self, data):  # NOQA
        if self.code == http.OK:
            self.current_length += len(data)
            if self.decoder:
                data = self.decoder.decompress(data)
            if self.part_callback:
                self.part_callback(data, self.current_length, self.total_length)

        return client.HTTPDownloader.pagePart(self, data)

    def pageEnd(self):  # NOQA
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
        log.warning("Potentially malicious server: trying to write to file '%s'", filename)
        # Only use the basename
        filename = os.path.basename(filename)

    filename = filename.strip()
    if filename.startswith(".") or ";" in filename or "|" in filename:
        # Dodgy server, log it
        log.warning("Potentially malicious server: trying to write to file '%s'", filename)

    return filename


def _download_file(url, filename, callback=None, headers=None, force_filename=False, allow_compression=True):
    """
    Downloads a file from a specific URL and returns a Deferred. A callback
    function can be specified to be called as parts are received.

    Args:
        url (str): The url to download from
        filename (str): The filename to save the file as
        callback (func): A function to be called when a part of data is received,
            it's signature should be: func(data, current_length, total_length)
        headers (dict): Any optional headers to send
        force_filename (bool): force us to use the filename specified rather than
            one the server may suggest
        allow_compression (bool): Allows gzip & deflate decoding

    Returns:
        Deferred: the filename of the downloaded file

    Raises:
        t.w.e.PageRedirect
        t.w.e.Error: for all other HTTP response errors

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

    # In Twisted 13.1.0 _parse() function replaced by _URI class.
    # In Twisted 15.0.0 _URI class renamed to URI.
    if hasattr(client, "_parse"):
        scheme, host, port, dummy_path = client._parse(url)
    else:
        try:
            from twisted.web.client import _URI as URI
        except ImportError:
            from twisted.web.client import URI

        uri = URI.fromBytes(url)
        scheme = uri.scheme
        host = uri.host
        port = uri.port

    factory = HTTPDownloader(url, filename, callback, headers, force_filename, allow_compression)
    if scheme == "https":
        from twisted.internet import ssl
        # ClientTLSOptions in Twisted >= 14, see ticket #2765 for details on this addition.
        try:
            from twisted.internet._sslverify import ClientTLSOptions
        except ImportError:
            ctx_factory = ssl.ClientContextFactory()
        else:
            class TLSSNIContextFactory(ssl.ClientContextFactory):
                """
                A custom context factory to add a server name for TLS connections.
                """
                def getContext(self):  # NOQA
                    ctx = ssl.ClientContextFactory.getContext(self)
                    ClientTLSOptions(host, ctx)
                    return ctx
            ctx_factory = TLSSNIContextFactory()

        reactor.connectSSL(host, port, factory, ctx_factory)
    else:
        reactor.connectTCP(host, port, factory)

    return factory.deferred


def download_file(url, filename, callback=None, headers=None, force_filename=False,
                  allow_compression=True, handle_redirects=True):
    """
    Downloads a file from a specific URL and returns a Deferred. A callback
    function can be specified to be called as parts are received.

    Args:
        url (str): The url to download from
        filename (str): The filename to save the file as
        callback (func): A function to be called when a part of data is received,
            it's signature should be: func(data, current_length, total_length)
        headers (dict): Any optional headers to send
        force_filename (bool): force us to use the filename specified rather than
            one the server may suggest
        allow_compression (bool): Allows gzip & deflate decoding
        handle_redirects (bool): If HTTP redirects should be handled automatically

    Returns:
        Deferred: the filename of the downloaded file

    Raises:
        t.w.e.PageRedirect: Unless handle_redirects=True
        t.w.e.Error: for all other HTTP response errors

    """
    def on_download_success(result):
        log.debug("Download success!")
        return result

    def on_download_fail(failure):
        if failure.check(PageRedirect) and handle_redirects:
            new_url = urljoin(url, failure.getErrorMessage().split(" to ")[1])
            result = _download_file(new_url, filename, callback=callback, headers=headers,
                                    force_filename=force_filename,
                                    allow_compression=allow_compression)
            result.addCallbacks(on_download_success, on_download_fail)
        else:
            # Log the error and pass the failure to the caller
            log.error("Error occurred downloading torrent from '%s': %s",
                      url, failure.getErrorMessage())
            result = failure
        return result

    d = _download_file(url, filename, callback=callback, headers=headers,
                       force_filename=force_filename, allow_compression=allow_compression)
    d.addCallbacks(on_download_success, on_download_fail)
    return d
