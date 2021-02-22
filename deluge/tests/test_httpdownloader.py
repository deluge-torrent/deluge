# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import os
import tempfile
from email.utils import formatdate
from io import open

from twisted.internet import reactor
from twisted.internet.error import CannotListenError
from twisted.python.failure import Failure
from twisted.trial import unittest
from twisted.web.error import PageRedirect
from twisted.web.http import NOT_MODIFIED
from twisted.web.resource import EncodingResourceWrapper, Resource
from twisted.web.server import GzipEncoderFactory, Site
from twisted.web.util import redirectTo

from deluge.httpdownloader import download_file
from deluge.log import setup_logger

temp_dir = tempfile.mkdtemp()


def fname(name):
    return os.path.join(temp_dir, name)


class RedirectResource(Resource):
    def render(self, request):
        url = self.get_url().encode('utf8')
        return redirectTo(url, request)


class RenameResource(Resource):
    def render(self, request):
        filename = request.args.get(b'filename', [b'renamed_file'])[0]
        request.setHeader(b'Content-Type', b'text/plain')
        request.setHeader(b'Content-Disposition', b'attachment; filename=' + filename)
        return b'This file should be called ' + filename


class AttachmentResource(Resource):
    def render(self, request):
        content_type = b'text/plain'
        charset = request.getHeader(b'content-charset')
        if charset:
            content_type += b'; charset=' + charset
        request.setHeader(b'Content-Type', content_type)
        request.setHeader(b'Content-Disposition', b'attachment')
        append = request.getHeader(b'content-append') or b''
        content = 'Attachment with no filename set{}'.format(append.decode('utf8'))
        return (
            content.encode(charset.decode('utf8'))
            if charset
            else content.encode('utf8')
        )


class TorrentResource(Resource):
    def render(self, request):
        content_type = b'application/x-bittorrent'
        charset = request.getHeader(b'content-charset')
        if charset:
            content_type += b'; charset=' + charset
        request.setHeader(b'Content-Type', content_type)
        request.setHeader(b'Content-Disposition', b'attachment; filename=test.torrent')
        return 'Binary attachment ignore charset 世丕且\n'.encode('utf8')


class CookieResource(Resource):
    def render(self, request):
        request.setHeader(b'Content-Type', b'text/plain')
        if request.getCookie(b'password') is None:
            return b'Password cookie not set!'

        if request.getCookie(b'password') == b'deluge':
            return b'COOKIE MONSTER!'

        return request.getCookie('password')


class GzipResource(Resource):
    def getChild(self, path, request):  # NOQA: N802
        return EncodingResourceWrapper(self, [GzipEncoderFactory()])

    def render(self, request):
        message = request.args.get(b'msg', [b'EFFICIENCY!'])[0]
        request.setHeader(b'Content-Type', b'text/plain')
        return message


class PartialDownloadResource(Resource):
    def __init__(self, *args, **kwargs):
        Resource.__init__(self)
        self.render_count = 0

    def render(self, request):
        # encoding = request.requestHeaders._rawHeaders.get('accept-encoding', None)
        if self.render_count == 0:
            request.setHeader(b'content-length', b'5')
        else:
            request.setHeader(b'content-length', b'3')

        # if encoding == "deflate, gzip, x-gzip":
        request.write('abc')
        self.render_count += 1
        return ''


class TopLevelResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild(b'cookie', CookieResource())
        self.putChild(b'gzip', GzipResource())
        self.redirect_rsrc = RedirectResource()
        self.putChild(b'redirect', self.redirect_rsrc)
        self.putChild(b'rename', RenameResource())
        self.putChild(b'attachment', AttachmentResource())
        self.putChild(b'torrent', TorrentResource())
        self.putChild(b'partial', PartialDownloadResource())

    def getChild(self, path, request):  # NOQA: N802
        if not path:
            return self
        else:
            return Resource.getChild(self, path, request)

    def render(self, request):
        if request.getHeader(b'If-Modified-Since'):
            request.setResponseCode(NOT_MODIFIED)
        return b'<h1>Deluge HTTP Downloader tests webserver here</h1>'


class DownloadFileTestCase(unittest.TestCase):
    def get_url(self, path=''):
        return 'http://localhost:%d/%s' % (self.listen_port, path)

    def setUp(self):  # NOQA
        setup_logger('warning', fname('log_file'))
        self.website = Site(TopLevelResource())
        self.listen_port = 51242
        self.website.resource.redirect_rsrc.get_url = self.get_url
        for dummy in range(10):
            try:
                self.webserver = reactor.listenTCP(self.listen_port, self.website)
            except CannotListenError as ex:
                error = ex
                self.listen_port += 1
            else:
                break
        else:
            raise error

    def tearDown(self):  # NOQA
        return self.webserver.stopListening()

    def assertContains(self, filename, contents):  # NOQA
        with open(filename, 'r', encoding='utf8') as _file:
            try:
                self.assertEqual(_file.read(), contents)
            except Exception as ex:
                self.fail(ex)
        return filename

    def assertNotContains(self, filename, contents, file_mode=''):  # NOQA
        with open(filename, 'r', encoding='utf8') as _file:
            try:
                self.assertNotEqual(_file.read(), contents)
            except Exception as ex:
                self.fail(ex)
        return filename

    def test_download(self):
        d = download_file(self.get_url(), fname('index.html'))
        d.addCallback(self.assertEqual, fname('index.html'))
        return d

    def test_download_without_required_cookies(self):
        url = self.get_url('cookie')
        d = download_file(url, fname('none'))
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d

    def test_download_with_required_cookies(self):
        url = self.get_url('cookie')
        cookie = {'cookie': 'password=deluge'}
        d = download_file(url, fname('monster'), headers=cookie)
        d.addCallback(self.assertEqual, fname('monster'))
        d.addCallback(self.assertContains, 'COOKIE MONSTER!')
        return d

    def test_download_with_rename(self):
        url = self.get_url('rename?filename=renamed')
        d = download_file(url, fname('original'))
        d.addCallback(self.assertEqual, fname('renamed'))
        d.addCallback(self.assertContains, 'This file should be called renamed')
        return d

    def test_download_with_rename_exists(self):
        open(fname('renamed'), 'w').close()
        url = self.get_url('rename?filename=renamed')
        d = download_file(url, fname('original'))
        d.addCallback(self.assertEqual, fname('renamed-1'))
        d.addCallback(self.assertContains, 'This file should be called renamed')
        return d

    def test_download_with_rename_sanitised(self):
        url = self.get_url('rename?filename=/etc/passwd')
        d = download_file(url, fname('original'))
        d.addCallback(self.assertEqual, fname('passwd'))
        d.addCallback(self.assertContains, 'This file should be called /etc/passwd')
        return d

    def test_download_with_attachment_no_filename(self):
        url = self.get_url('attachment')
        d = download_file(url, fname('original'))
        d.addCallback(self.assertEqual, fname('original'))
        d.addCallback(self.assertContains, 'Attachment with no filename set')
        return d

    def test_download_with_rename_prevented(self):
        url = self.get_url('rename?filename=spam')
        d = download_file(url, fname('forced'), force_filename=True)
        d.addCallback(self.assertEqual, fname('forced'))
        d.addCallback(self.assertContains, 'This file should be called spam')
        return d

    def test_download_with_gzip_encoding(self):
        url = self.get_url('gzip?msg=success')
        d = download_file(url, fname('gzip_encoded'))
        d.addCallback(self.assertContains, 'success')
        return d

    def test_download_with_gzip_encoding_disabled(self):
        url = self.get_url('gzip?msg=unzip')
        d = download_file(url, fname('gzip_encoded'), allow_compression=False)
        d.addCallback(self.assertContains, 'unzip')
        return d

    def test_page_redirect_unhandled(self):
        url = self.get_url('redirect')
        d = download_file(url, fname('none'))
        d.addCallback(self.fail)

        def on_redirect(failure):
            self.assertTrue(type(failure), PageRedirect)

        d.addErrback(on_redirect)
        return d

    def test_page_redirect(self):
        url = self.get_url('redirect')
        d = download_file(url, fname('none'), handle_redirects=True)
        d.addCallback(self.assertEqual, fname('none'))
        d.addErrback(self.fail)
        return d

    def test_page_not_found(self):
        d = download_file(self.get_url('page/not/found'), fname('none'))
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d

    def test_page_not_modified(self):
        headers = {'If-Modified-Since': formatdate(usegmt=True)}
        d = download_file(self.get_url(), fname('index.html'), headers=headers)
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d

    def test_download_text_reencode_charset(self):
        """Re-encode as UTF-8 specified charset for text content-type header"""
        url = self.get_url('attachment')
        filepath = fname('test.txt')
        headers = {'content-charset': 'Windows-1251', 'content-append': 'бвгде'}
        d = download_file(url, filepath, headers=headers)
        d.addCallback(self.assertEqual, filepath)
        d.addCallback(self.assertContains, 'Attachment with no filename setбвгде')
        return d

    def test_download_binary_ignore_charset(self):
        """Ignore charset for binary content-type header e.g. torrent files"""
        url = self.get_url('torrent')
        headers = {'content-charset': 'Windows-1251'}
        filepath = fname('test.torrent')
        d = download_file(url, fname('test.torrent'), headers=headers)
        d.addCallback(self.assertEqual, filepath)
        d.addCallback(self.assertContains, 'Binary attachment ignore charset 世丕且\n')
        return d
