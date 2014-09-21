import tempfile
import warnings
from email.utils import formatdate

from twisted.internet import reactor
from twisted.internet.error import CannotListenError
from twisted.python.failure import Failure
from twisted.trial import unittest
from twisted.web.http import NOT_MODIFIED
from twisted.web.server import Site

from . import common
from deluge.httpdownloader import download_file
from deluge.log import setup_logger
from deluge.ui.web.common import compress


try:
    from twisted.web.resource import Resource
except ImportError:
    # twisted 8
    from twisted.web.error import Resource


warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.resetwarnings()


rpath = common.rpath
temp_dir = tempfile.mkdtemp()


def fname(name):
    return "%s/%s" % (temp_dir, name)


class TestRedirectResource(Resource):

    def render(self, request):
        request.redirect("http://localhost:51242/")


class TestRenameResource(Resource):

    def render(self, request):
        filename = request.args.get("filename", ["renamed_file"])[0]
        request.setHeader("Content-Type", "text/plain")
        request.setHeader("Content-Disposition", "attachment; filename=" +
                          filename)
        return "This file should be called " + filename


class TestCookieResource(Resource):

    def render(self, request):
        request.setHeader("Content-Type", "text/plain")
        if request.getCookie("password") is None:
            return "Password cookie not set!"

        if request.getCookie("password") == "deluge":
            return "COOKIE MONSTER!"

        return request.getCookie("password")


class TestGzipResource(Resource):

    def render(self, request):
        message = request.args.get("msg", ["EFFICIENCY!"])[0]
        request.setHeader("Content-Type", "text/plain")
        return compress(message, request)


class TopLevelResource(Resource):

    addSlash = True

    def __init__(self):
        Resource.__init__(self)
        self.putChild("cookie", TestCookieResource())
        self.putChild("gzip", TestGzipResource())
        self.putChild("redirect", TestRedirectResource())
        self.putChild("rename", TestRenameResource())

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

    def setUp(self):  # NOQA
        setup_logger("warning", "log_file")
        self.website = Site(TopLevelResource())
        self.listen_port = 51242
        tries = 10
        error = None
        while tries > 0:
            try:
                self.webserver = reactor.listenTCP(self.listen_port, self.website)
            except CannotListenError as ex:
                error = ex
                self.listen_port += 1
                tries -= 1
            else:
                error = None
                break
        if error:
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
        d = download_file("http://localhost:%d/" % self.listen_port, fname("index.html"))
        d.addCallback(self.assertEqual, fname("index.html"))
        return d

    def test_download_without_required_cookies(self):
        url = "http://localhost:%d/cookie" % self.listen_port
        d = download_file(url, fname("none"))
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d

    def test_download_with_required_cookies(self):
        url = "http://localhost:%d/cookie" % self.listen_port
        cookie = {"cookie": "password=deluge"}
        d = download_file(url, fname("monster"), headers=cookie)
        d.addCallback(self.assertEqual, fname("monster"))
        d.addCallback(self.assertContains, "COOKIE MONSTER!")
        return d

    def test_download_with_rename(self):
        url = "http://localhost:%d/rename?filename=renamed" % self.listen_port
        d = download_file(url, fname("original"))
        d.addCallback(self.assertEqual, fname("renamed"))
        d.addCallback(self.assertContains, "This file should be called renamed")
        return d

    def test_download_with_rename_exists(self):
        open(fname('renamed'), 'w').close()
        url = "http://localhost:%d/rename?filename=renamed" % self.listen_port
        d = download_file(url, fname("original"))
        d.addCallback(self.assertEqual, fname("renamed-1"))
        d.addCallback(self.assertContains, "This file should be called renamed")
        return d

    def test_download_with_rename_sanitised(self):
        url = "http://localhost:%d/rename?filename=/etc/passwd" % self.listen_port
        d = download_file(url, fname("original"))
        d.addCallback(self.assertEqual, fname("passwd"))
        d.addCallback(self.assertContains, "This file should be called /etc/passwd")
        return d

    def test_download_with_rename_prevented(self):
        url = "http://localhost:%d/rename?filename=spam" % self.listen_port
        d = download_file(url, fname("forced"), force_filename=True)
        d.addCallback(self.assertEqual, fname("forced"))
        d.addCallback(self.assertContains, "This file should be called spam")
        return d

    def test_download_with_gzip_encoding(self):
        url = "http://localhost:%d/gzip?msg=success" % self.listen_port
        d = download_file(url, fname("gzip_encoded"))
        d.addCallback(self.assertContains, "success")
        return d

    def test_download_with_gzip_encoding_disabled(self):
        url = "http://localhost:%d/gzip?msg=fail" % self.listen_port
        d = download_file(url, fname("gzip_encoded"), allow_compression=False)
        d.addCallback(self.failIfContains, "fail")
        return d

    def test_page_redirect(self):
        url = 'http://localhost:%d/redirect' % self.listen_port
        d = download_file(url, fname("none"))
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d

    def test_page_not_found(self):
        d = download_file("http://localhost:%d/page/not/found" % self.listen_port, fname("none"))
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d

    def test_page_not_modified(self):
        headers = {'If-Modified-Since': formatdate(usegmt=True)}
        d = download_file("http://localhost:%d/" % self.listen_port, fname("index.html"), headers=headers)
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d
