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
from twisted.web.iweb import IAgent
from zope.interface import implementer

from deluge.common import get_version

log = logging.getLogger(__name__)


class CompressionDecoder(client.GzipDecoder):
    """A compression decoder for gzip, x-gzip and deflate."""

    def deliverBody(self, protocol):  # NOQA: N802
        self.original.deliverBody(CompressionDecoderProtocol(protocol, self.original))


class CompressionDecoderProtocol(client._GzipProtocol):
    """A compression decoder protocol for CompressionDecoder."""

    def __init__(self, protocol, response):
        super(CompressionDecoderProtocol, self).__init__(protocol, response)
        self._zlibDecompress = zlib.decompressobj(32 + zlib.MAX_WBITS)


class BodyHandler(HTTPClientParser, object):
    """An HTTP parser that saves the response to a file."""

    def __init__(self, request, finished, length, agent, encoding=None):
        """BodyHandler init.

        Args:
            request (t.w.i.IClientRequest): The parser request.
            finished (Deferred): A Deferred to handle the finished response.
            length (int): The length of the response.
            agent (t.w.i.IAgent): The agent from which the request was sent.
        """
        super(BodyHandler, self).__init__(request, finished)
        self.agent = agent
        self.finished = finished
        self.total_length = length
        self.current_length = 0
        self.data = b''
        self.encoding = encoding

    def dataReceived(self, data):  # NOQA: N802
        self.current_length += len(data)
        self.data += data
        if self.agent.part_callback:
            self.agent.part_callback(data, self.current_length, self.total_length)

    def connectionLost(self, reason):  # NOQA: N802
        if self.encoding:
            self.data = self.data.decode(self.encoding).encode('utf8')
        with open(self.agent.filename, 'wb') as _file:
            _file.write(self.data)
        self.finished.callback(self.agent.filename)
        self.state = u'DONE'
        HTTPClientParser.connectionLost(self, reason)


@implementer(IAgent)
class HTTPDownloaderAgent(object):
    """A File Downloader Agent."""

    def __init__(
        self,
        agent,
        filename,
        part_callback=None,
        force_filename=False,
        allow_compression=True,
        handle_redirect=True,
    ):
        """HTTPDownloaderAgent init.

        Args:
            agent (t.w.c.Agent): The agent which will send the requests.
            filename (str): The filename to save the file as.
            force_filename (bool): Forces use of the supplied filename,
                regardless of header content.
            part_callback (func): A function to be called when a part of data
                is received, it's signature should be:
                    func(data, current_length, total_length)
        """

        self.handle_redirect = handle_redirect
        self.agent = agent
        self.filename = filename
        self.part_callback = part_callback
        self.force_filename = force_filename
        self.allow_compression = allow_compression
        self.decoder = None

    def request_callback(self, response):
        finished = Deferred()

        if not self.handle_redirect and response.code in (
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

            if headers.hasHeader(b'content-disposition') and not self.force_filename:
                content_disp = headers.getRawHeaders(b'content-disposition')[0].decode(
                    'utf-8'
                )
                content_disp_params = cgi.parse_header(content_disp)[1]
                if 'filename' in content_disp_params:
                    new_file_name = content_disp_params['filename']
                    new_file_name = sanitise_filename(new_file_name)
                    new_file_name = os.path.join(
                        os.path.split(self.filename)[0], new_file_name
                    )

                    count = 1
                    fileroot = os.path.splitext(new_file_name)[0]
                    fileext = os.path.splitext(new_file_name)[1]
                    while os.path.isfile(new_file_name):
                        # Increment filename if already exists
                        new_file_name = '%s-%s%s' % (fileroot, count, fileext)
                        count += 1

                    self.filename = new_file_name

            cont_type_header = headers.getRawHeaders(b'content-type')[0].decode()
            cont_type, params = cgi.parse_header(cont_type_header)
            # Only re-ecode text content types.
            encoding = None
            if cont_type.startswith('text/'):
                encoding = params.get('charset', None)
            response.deliverBody(
                BodyHandler(response.request, finished, body_length, self, encoding)
            )

        return finished

    def request(self, method, uri, headers=None, body_producer=None):
        """Issue a new request to the wrapped agent.

        Args:
            method (bytes): The HTTP method to use.
            uri (bytes): The url to download from.
            headers (t.w.h.Headers, optional): Any extra headers to send.
            body_producer (t.w.i.IBodyProducer, optional): Request body data.

        Returns:
            Deferred: The filename of the of the downloaded file.
        """
        if headers is None:
            headers = Headers()

        if not headers.hasHeader(b'User-Agent'):
            version = get_version()
            user_agent = 'Deluge/%s (https://deluge-torrent.org)' % version
            headers.addRawHeader('User-Agent', user_agent)

        d = self.agent.request(
            method=method, uri=uri, headers=headers, bodyProducer=body_producer
        )
        d.addCallback(self.request_callback)
        return d


def sanitise_filename(filename):
    """Sanitises a filename to use as a download destination file.

    Logs any filenames that could be considered malicious.

    filename (str): The filename to sanitise.

    Returns:
        str: The sanitised filename.
    """

    # Remove any quotes
    filename = filename.strip('\'"')

    if os.path.basename(filename) != filename:
        # Dodgy server, log it
        log.warning(
            'Potentially malicious server: trying to write to file: %s', filename
        )
        # Only use the basename
        filename = os.path.basename(filename)

    filename = filename.strip()
    if filename.startswith('.') or ';' in filename or '|' in filename:
        # Dodgy server, log it
        log.warning(
            'Potentially malicious server: trying to write to file: %s', filename
        )

    return filename


def _download_file(
    url,
    filename,
    callback=None,
    headers=None,
    force_filename=False,
    allow_compression=True,
    handle_redirects=True,
):
    """Downloads a file from a specific URL and returns a Deferred.

    A callback function can be specified to be called as parts are received.

    Args:
        url (str): The url to download from.
        filename (str): The filename to save the file as.
        callback (func): A function to be called when partial data is received,
            it's signature should be: func(data, current_length, total_length)
        headers (dict): Any optional headers to send.
        force_filename (bool): Force using the filename specified rather than
            one the server may suggest.
        allow_compression (bool): Allows gzip & deflate decoding.

    Returns:
        Deferred: The filename of the downloaded file.

    Raises:
        t.w.e.PageRedirect
        t.w.e.Error: for all other HTTP response errors
    """

    agent = client.Agent(reactor)

    if allow_compression:
        enc_accepted = ['gzip', 'x-gzip', 'deflate']
        decoders = [(enc.encode(), CompressionDecoder) for enc in enc_accepted]
        agent = client.ContentDecoderAgent(agent, decoders)
    if handle_redirects:
        agent = client.RedirectAgent(agent)

    agent = HTTPDownloaderAgent(
        agent, filename, callback, force_filename, allow_compression, handle_redirects
    )

    # The Headers init expects dict values to be a list.
    if headers:
        for name, value in list(headers.items()):
            if not isinstance(value, list):
                headers[name] = [value]

    return agent.request(b'GET', url.encode(), Headers(headers))


def download_file(
    url,
    filename,
    callback=None,
    headers=None,
    force_filename=False,
    allow_compression=True,
    handle_redirects=True,
):
    """Downloads a file from a specific URL and returns a Deferred.

    A callback function can be specified to be called as parts are received.

    Args:
        url (str): The url to download from.
        filename (str): The filename to save the file as.
        callback (func): A function to be called when partial data is received,
            it's signature should be: func(data, current_length, total_length).
        headers (dict): Any optional headers to send.
        force_filename (bool): Force the filename specified rather than one the
            server may suggest.
        allow_compression (bool): Allows gzip & deflate decoding.
        handle_redirects (bool): HTTP redirects handled automatically or not.

    Returns:
        Deferred: The filename of the downloaded file.

    Raises:
        t.w.e.PageRedirect: If handle_redirects is False.
        t.w.e.Error: For all other HTTP response errors.
    """

    def on_download_success(result):
        log.debug('Download success!')
        return result

    def on_download_fail(failure):
        log.warning(
            'Error occurred downloading file from "%s": %s',
            url,
            failure.getErrorMessage(),
        )
        result = failure
        return result

    d = _download_file(
        url,
        filename,
        callback=callback,
        headers=headers,
        force_filename=force_filename,
        allow_compression=allow_compression,
        handle_redirects=handle_redirects,
    )
    d.addCallbacks(on_download_success, on_download_fail)
    return d
