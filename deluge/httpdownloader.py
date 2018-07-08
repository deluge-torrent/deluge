# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import cgi
import logging
import os.path
import zlib

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure
from twisted.web import client, http
from twisted.web._newclient import HTTPClientParser
from twisted.web.error import PageRedirect
from twisted.web.http_headers import Headers

from deluge.common import get_version, utf8_encode_structure

try:
    from urllib.parse import urljoin
except ImportError:
    # PY2 fallback
    from urlparse import urljoin  # pylint: disable=ungrouped-imports

log = logging.getLogger(__name__)


class BodyHandler(HTTPClientParser):
    def __init__(self, request, finished, length, agent):
        HTTPClientParser.__init__(self, request, finished)
        self.agent = agent
        self.finished = finished
        self.total_length = length
        self.current_length = 0
        self.data = b''

    def dataReceived(self, data):  # NOQA: N802
        self.current_length += len(data)
        if self.agent.decoder:
            data = self.agent.decoder.decompress(data)
        self.data += data
        if self.agent.part_callback:
            self.agent.part_callback(data, self.current_length, self.total_length)

    def connectionLost(self, reason):  # NOQA: N802
        with open(self.agent.filename, 'wb') as _file:
            _file.write(self.data)
        self.finished.callback(self.agent.filename)
        self.state = u'DONE'
        HTTPClientParser.connectionLost(self, reason)


class HTTPDownloaderAgent(client.Agent):
    """
    A File Downloader Agent
    """
    def __init__(
        self, url, filename, part_callback=None, headers=None,
        force_filename=False, allow_compression=True
    ):
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
        if not headers:
            headers = {}
        else:
            for key, value in headers.items():
                headers[key] = [value]
        headers.update({'User-Agent': ['Deluge/%s (http://deluge-torrent.org)' % get_version()]})

        self.url = url.encode()
        self.filename = filename
        self.part_callback = part_callback
        self.headers = Headers(headers)
        self.force_filename = force_filename
        self.allow_compression = allow_compression
        self.decoder = None
        client.Agent.__init__(self, reactor)

    def request_callback(self, response):
        finished = Deferred()

        if response.code in (
            http.MOVED_PERMANENTLY,
            http.FOUND,
            http.SEE_OTHER,
            http.TEMPORARY_REDIRECT,
        ):
            location = response.headers.getRawHeaders(b'location')[0]
            error = PageRedirect(response.code, location=location)
            finished.errback(Failure(error))

        else:
            headers = response.headers
            body_length = int(headers.getRawHeaders(b'content-length', default=[0])[0])

            encodings_accepted = [b'gzip', b'x-gzip', b'deflate']
            if (
                self.allow_compression and headers.hasHeader(b'content-encoding')
                and headers.getRawHeaders(b'content-encoding')[0] in encodings_accepted
            ):
                # Adding 32 to the wbits enables gzip & zlib decoding (with automatic header detection)
                # Adding 16 just enables gzip decoding (no zlib)
                self.decoder = zlib.decompressobj(zlib.MAX_WBITS + 32)

            if headers.hasHeader(b'content-disposition') and not self.force_filename:
                content_disp = headers.getRawHeaders(b'content-disposition')[0].decode('utf-8')
                content_disp_params = cgi.parse_header(content_disp)[1]
                if 'filename' in content_disp_params:
                    new_file_name = content_disp_params['filename']
                    new_file_name = sanitise_filename(new_file_name)
                    new_file_name = os.path.join(os.path.split(self.filename)[0], new_file_name)

                    count = 1
                    fileroot = os.path.splitext(new_file_name)[0]
                    fileext = os.path.splitext(new_file_name)[1]
                    while os.path.isfile(new_file_name):
                        # Increment filename if already exists
                        new_file_name = '%s-%s%s' % (fileroot, count, fileext)
                        count += 1

                    self.filename = new_file_name

            response.deliverBody(BodyHandler(response.request, finished, body_length, self))

        return finished

    def request(self):
        d = client.Agent.request(
            self,
            method=b'GET',
            uri=self.url,
            headers=self.headers
        )
        d.addCallback(self.request_callback)
        return d


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
    filename = filename.strip('\'"')

    if os.path.basename(filename) != filename:
        # Dodgy server, log it
        log.warning('Potentially malicious server: trying to write to file: %s', filename)
        # Only use the basename
        filename = os.path.basename(filename)

    filename = filename.strip()
    if filename.startswith('.') or ';' in filename or '|' in filename:
        # Dodgy server, log it
        log.warning('Potentially malicious server: trying to write to file: %s', filename)

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

    headers = utf8_encode_structure(headers) if headers else headers
    agent = HTTPDownloaderAgent(url, filename, callback, headers, force_filename, allow_compression)
    return agent.request()


def download_file(
    url, filename, callback=None, headers=None, force_filename=False,
    allow_compression=True, handle_redirects=True,
):
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
        log.debug('Download success!')
        return result

    def on_download_fail(failure):
        if failure.check(PageRedirect) and handle_redirects:
            new_url = urljoin(url, failure.getErrorMessage().split(' to ')[1])
            result = _download_file(
                new_url, filename, callback=callback, headers=headers,
                force_filename=force_filename,
                allow_compression=allow_compression,
            )
            result.addCallbacks(on_download_success, on_download_fail)
        else:
            # Log the failure and pass to the caller
            log.warning(
                'Error occurred downloading file from "%s": %s',
                url, failure.getErrorMessage(),
            )
            result = failure
        return result

    d = _download_file(
        url, filename, callback=callback, headers=headers,
        force_filename=force_filename, allow_compression=allow_compression,
    )
    d.addCallbacks(on_download_success, on_download_fail)
    return d
