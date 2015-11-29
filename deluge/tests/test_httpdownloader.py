import tempfile
from email.utils import formatdate

from twisted.internet import reactor
from twisted.internet.error import CannotListenError
from twisted.python.failure import Failure
from twisted.trial import unittest
from twisted.web.error import PageRedirect
from twisted.web.http import NOT_MODIFIED
from twisted.web.server import Site
from twisted.web.util import redirectTo

from deluge.httpdownloader import download_file
from deluge.log import setup_logger
from deluge.ui.web.common import compress

from . import common

try:
    from twisted.web.resource import Resource
except ImportError:
    # twisted 8
    from twisted.web.error import Resource


rpath = common.rpath
temp_dir = tempfile.mkdtemp()


def fname(name):
    return "%s/%s" % (temp_dir, name)


class RedirectResource(Resource):

    def render(self, request):
        url = self.get_url()
        return redirectTo(url, request)


class RenameResource(Resource):

    def render(self, request):
        filename = request.args.get("filename", ["renamed_file"])[0]
        request.setHeader("Content-Type", "text/plain")
        request.setHeader("Content-Disposition", "attachment; filename=" +
                          filename)
        return "This file should be called " + filename


class CookieResource(Resource):

    def render(self, request):
        request.setHeader("Content-Type", "text/plain")
        if request.getCookie("password") is None:
            return "Password cookie not set!"

        if request.getCookie("password") == "deluge":
            return "COOKIE MONSTER!"

        return request.getCookie("password")


class GzipResource(Resource):

    def render(self, request):
        message = request.args.get("msg", ["EFFICIENCY!"])[0]
        request.setHeader("Content-Type", "text/plain")
        return compress(message, request)


class PartialDownloadResource(Resource):

    def __init__(self, *args, **kwargs):
        self.render_count = 0

    def render(self, request):
        # encoding = request.requestHeaders._rawHeaders.get("accept-encoding", None)
        if self.render_count == 0:
            request.setHeader("content-length", "5")
        else:
            request.setHeader("content-length", "3")

        # if encoding == "deflate, gzip, x-gzip":
        request.write('abc')
        self.render_count += 1
        return ''


class TopLevelResource(Resource):

    addSlash = True

    def __init__(self):
        Resource.__init__(self)
        self.putChild("cookie", CookieResource())
        self.putChild("gzip", GzipResource())
        self.redirect_rsrc = RedirectResource()
        self.putChild("redirect", self.redirect_rsrc)
        self.putChild("rename", RenameResource())
        self.putChild("partial", PartialDownloadResource())

    def getChild(self, path, request):  # NOQA
        if path == "":
            return self
        else:
            return Resource.getChild(self, path, request)

    def render(self, request):
        if request.getHeader("If-Modified-Since"):
            request.setResponseCode(NOT_MODIFIED)
        return "<h1>Deluge HTTP Downloader tests webserver here</h1>"


class DownloadFileTestCase(unittest.TestCase):

    def get_url(self, path=""):
        return "http://localhost:%d/%s" % (self.listen_port, path)

    def setUp(self):  # NOQA
        setup_logger("warning", fname("log_file"))
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
        f = open(filename)
        try:
            self.assertEqual(f.read(), contents)
        except Exception as ex:
            self.fail(ex)
        finally:
            f.close()
        return filename

    def failIfContains(self, filename, contents):  # NOQA
        f = open(filename)
        try:
            self.failIfEqual(f.read(), contents)
        except Exception as ex:
            self.fail(ex)
        finally:
            f.close()
        return filename

    def test_download(self):
        d = download_file(self.get_url(), fname("index.html"))
        d.addCallback(self.assertEqual, fname("index.html"))
        return d

    def test_download_without_required_cookies(self):
        url = self.get_url("cookie")
        d = download_file(url, fname("none"))
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d

    def test_download_with_required_cookies(self):
        url = self.get_url("cookie")
        cookie = {"cookie": "password=deluge"}
        d = download_file(url, fname("monster"), headers=cookie)
        d.addCallback(self.assertEqual, fname("monster"))
        d.addCallback(self.assertContains, "COOKIE MONSTER!")
        return d

    def test_download_with_rename(self):
        url = self.get_url("rename?filename=renamed")
        d = download_file(url, fname("original"))
        d.addCallback(self.assertEqual, fname("renamed"))
        d.addCallback(self.assertContains, "This file should be called renamed")
        return d

    def test_download_with_rename_exists(self):
        open(fname('renamed'), 'w').close()
        url = self.get_url("rename?filename=renamed")
        d = download_file(url, fname("original"))
        d.addCallback(self.assertEqual, fname("renamed-1"))
        d.addCallback(self.assertContains, "This file should be called renamed")
        return d

    def test_download_with_rename_sanitised(self):
        url = self.get_url("rename?filename=/etc/passwd")
        d = download_file(url, fname("original"))
        d.addCallback(self.assertEqual, fname("passwd"))
        d.addCallback(self.assertContains, "This file should be called /etc/passwd")
        return d

    def test_download_with_rename_prevented(self):
        url = self.get_url("rename?filename=spam")
        d = download_file(url, fname("forced"), force_filename=True)
        d.addCallback(self.assertEqual, fname("forced"))
        d.addCallback(self.assertContains, "This file should be called spam")
        return d

    def test_download_with_gzip_encoding(self):
        url = self.get_url("gzip?msg=success")
        d = download_file(url, fname("gzip_encoded"))
        d.addCallback(self.assertContains, "success")
        return d

    def test_download_with_gzip_encoding_disabled(self):
        url = self.get_url("gzip?msg=fail")
        d = download_file(url, fname("gzip_encoded"), allow_compression=False)
        d.addCallback(self.failIfContains, "fail")
        return d

    def test_page_redirect_unhandled(self):
        url = self.get_url("redirect")
        d = download_file(url, fname("none"))
        d.addCallback(self.fail)

        def on_redirect(failure):
            self.assertTrue(type(failure), PageRedirect)
        d.addErrback(on_redirect)
        return d

    def test_page_redirect(self):
        url = self.get_url("redirect")
        d = download_file(url, fname("none"), handle_redirects=True)
        d.addCallback(self.assertEqual, fname("none"))
        d.addErrback(self.fail)
        return d

    def test_page_not_found(self):
        d = download_file(self.get_url("page/not/found"), fname("none"))
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d

    def test_page_not_modified(self):
        headers = {'If-Modified-Since': formatdate(usegmt=True)}
        d = download_file(self.get_url(), fname("index.html"), headers=headers)
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d
