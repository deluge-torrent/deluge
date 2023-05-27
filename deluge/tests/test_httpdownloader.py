#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os
import tempfile
from email.utils import formatdate

import pytest
import pytest_twisted
from twisted.internet import reactor
from twisted.internet.error import CannotListenError
from twisted.web.error import Error, PageRedirect
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
        return 'Binary attachment ignore charset 世丕且\n'.encode()


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


class TestDownloadFile:
    def get_url(self, path=''):
        return 'http://localhost:%d/%s' % (self.listen_port, path)

    @pytest_twisted.async_yield_fixture(autouse=True)
    async def setUp(self, request):  # NOQA
        self = request.instance
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

        yield

        await self.webserver.stopListening()

    def assert_contains(self, filename, contents):
        with open(filename, encoding='utf8') as _file:
            try:
                assert _file.read() == contents
            except Exception as ex:
                pytest.fail(ex)
        return filename

    def assert_not_contains(self, filename, contents, file_mode=''):
        with open(filename, encoding='utf8') as _file:
            try:
                assert _file.read() != contents
            except Exception as ex:
                pytest.fail(ex)
        return filename

    async def test_download(self):
        filename = await download_file(self.get_url(), fname('index.html'))
        assert filename == fname('index.html')

    async def test_download_without_required_cookies(self):
        url = self.get_url('cookie')
        filename = await download_file(url, fname('none'))
        self.assert_contains(filename, 'Password cookie not set!')

    async def test_download_with_required_cookies(self):
        url = self.get_url('cookie')
        cookie = {'cookie': 'password=deluge'}
        filename = await download_file(url, fname('monster'), headers=cookie)
        assert filename == fname('monster')
        self.assert_contains(filename, 'COOKIE MONSTER!')

    async def test_download_with_rename(self):
        url = self.get_url('rename?filename=renamed')
        filename = await download_file(url, fname('original'))
        assert filename == fname('renamed')
        self.assert_contains(filename, 'This file should be called renamed')

    async def test_download_with_rename_exists(self):
        open(fname('renamed'), 'w').close()
        url = self.get_url('rename?filename=renamed')
        filename = await download_file(url, fname('original'))
        assert filename == fname('renamed-1')
        self.assert_contains(filename, 'This file should be called renamed')

    async def test_download_with_rename_sanitised(self):
        url = self.get_url('rename?filename=/etc/passwd')
        filename = await download_file(url, fname('original'))
        assert filename == fname('passwd')
        self.assert_contains(filename, 'This file should be called /etc/passwd')

    async def test_download_with_attachment_no_filename(self):
        url = self.get_url('attachment')
        filename = await download_file(url, fname('original'))
        assert filename == fname('original')
        self.assert_contains(filename, 'Attachment with no filename set')

    async def test_download_with_rename_prevented(self):
        url = self.get_url('rename?filename=spam')
        filename = await download_file(url, fname('forced'), force_filename=True)
        assert filename == fname('forced')
        self.assert_contains(filename, 'This file should be called spam')

    async def test_download_with_gzip_encoding(self):
        url = self.get_url('gzip?msg=success')
        filename = await download_file(url, fname('gzip_encoded'))
        self.assert_contains(filename, 'success')

    async def test_download_with_gzip_encoding_disabled(self):
        url = self.get_url('gzip?msg=unzip')
        filename = await download_file(
            url, fname('gzip_encoded'), allow_compression=False
        )
        self.assert_contains(filename, 'unzip')

    async def test_page_redirect_unhandled(self):
        url = self.get_url('redirect')
        with pytest.raises(PageRedirect):
            await download_file(url, fname('none'), handle_redirects=False)

    async def test_page_redirect(self):
        url = self.get_url('redirect')
        filename = await download_file(url, fname('none'), handle_redirects=True)
        assert filename == fname('none')

    async def test_page_not_found(self):
        with pytest.raises(Error):
            await download_file(self.get_url('page/not/found'), fname('none'))

    @pytest.mark.xfail(reason="Doesn't seem like httpdownloader ever implemented this.")
    async def test_page_not_modified(self):
        headers = {'If-Modified-Since': formatdate(usegmt=True)}
        with pytest.raises(Error) as exc_info:
            await download_file(self.get_url(), fname('index.html'), headers=headers)
        assert exc_info.value.status == NOT_MODIFIED

    async def test_download_text_reencode_charset(self):
        """Re-encode as UTF-8 specified charset for text content-type header"""
        url = self.get_url('attachment')
        filepath = fname('test.txt')
        headers = {'content-charset': 'Windows-1251', 'content-append': 'бвгде'}
        filename = await download_file(url, filepath, headers=headers)
        assert filename == filepath
        self.assert_contains(filename, 'Attachment with no filename setбвгде')

    async def test_download_binary_ignore_charset(self):
        """Ignore charset for binary content-type header e.g. torrent files"""
        url = self.get_url('torrent')
        headers = {'content-charset': 'Windows-1251'}
        filepath = fname('test.torrent')
        filename = await download_file(url, fname('test.torrent'), headers=headers)
        assert filename == filepath
        self.assert_contains(filename, 'Binary attachment ignore charset 世丕且\n')
