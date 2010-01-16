from twisted.trial import unittest
from twisted.python.failure import Failure

from deluge.httpdownloader import download_file
from deluge.log import setupLogger

from email.utils import formatdate

class DownloadFileTestCase(unittest.TestCase):
    def setUp(self):
        setupLogger("warning", "log_file")

    def tearDown(self):
        pass

    def assertContains(self, filename, contents):
        f = open(filename)
        try:
            self.assertEqual(f.read(), contents)
        except Exception, e:
            self.fail(e)
        finally:
            f.close()
        return filename

    def failIfContains(self, filename, contents):
        f = open(filename)
        try:
            self.failIfEqual(f.read(), contents)
        except Exception, e:
            self.fail(e)
        finally:
            f.close()
        return filename

    def test_download(self):
        d = download_file("http://deluge-torrent.org", "index.html")
        d.addCallback(self.assertEqual, "index.html")
        return d

    def test_download_without_required_cookies(self):
        url = "http://deluge-torrent.org/httpdownloader.php?test=cookie"
        d = download_file(url, "none")
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d

    def test_download_with_required_cookies(self):
        url = "http://deluge-torrent.org/httpdownloader.php?test=cookie"
        cookie = { "cookie" : "password=deluge" }
        d = download_file(url, "monster", headers=cookie)
        d.addCallback(self.assertEqual, "monster")
        d.addCallback(self.assertContains, "COOKIE MONSTER!")
        return d

    def test_download_with_rename(self):
        url = "http://deluge-torrent.org/httpdownloader.php?test=rename&filename=renamed"
        d = download_file(url, "original")
        d.addCallback(self.assertEqual, "renamed")
        d.addCallback(self.assertContains, "This file should be called renamed")
        return d

    def test_download_with_rename_fail(self):
        url = "http://deluge-torrent.org/httpdownloader.php?test=rename&filename=renamed"
        d = download_file(url, "original")
        d.addCallback(self.assertEqual, "original")
        d.addCallback(self.assertContains, "This file should be called renamed")
        return d

    def test_download_with_rename_sanitised(self):
        url = "http://deluge-torrent.org/httpdownloader.php?test=rename&filename=/etc/passwd"
        d = download_file(url, "original")
        d.addCallback(self.assertEqual, "passwd")
        d.addCallback(self.assertContains, "This file should be called /etc/passwd")
        return d

    def test_download_with_rename_prevented(self):
        url = "http://deluge-torrent.org/httpdownloader.php?test=rename&filename=spam"
        d = download_file(url, "forced", force_filename=True)
        d.addCallback(self.assertEqual, "forced")
        d.addCallback(self.assertContains, "This file should be called spam")
        return d

    def test_download_with_gzip_encoding(self):
        url = "http://deluge-torrent.org/httpdownloader.php?test=gzip&msg=success"
        d = download_file(url, "gzip_encoded")
        d.addCallback(self.assertContains, "success")
        return d

    def test_download_with_gzip_encoding_disabled(self):
        url = "http://deluge-torrent.org/httpdownloader.php?test=gzip&msg=fail"
        d = download_file(url, "gzip_encoded", allow_compression=False)
        d.addCallback(self.failIfContains, "fail")
        return d

    def test_page_redirect(self):
        url = "http://deluge-torrent.org/httpdownloader.php?test=redirect"
        d = download_file(url, "none")
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d

    def test_page_not_found(self):
        d = download_file("http://does.not.exist", "none")
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d

    def test_page_not_modified(self):
        headers = { 'If-Modified-Since' : formatdate(usegmt=True) }
        d = download_file("http://deluge-torrent.org", "index.html", headers=headers)
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d
