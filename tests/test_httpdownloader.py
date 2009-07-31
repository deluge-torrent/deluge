from twisted.trial import unittest
from twisted.python.failure import Failure

from deluge.httpdownloader import download_file

class DownloadFileTestCase(unittest.TestCase):
    def test_download(self):
        d = download_file("http://deluge-torrent.org", "index.html")
        d.addCallback(self.assertEqual, "index.html")
        return d

    def test_download_with_cookies(self):
        pass

    def test_page_moved(self):
        pass

    def test_page_moved_permanently(self):
        pass

    def test_page_not_modified(self):
        pass

    def test_page_not_found(self):
        d = download_file("http://does.not.exist", "none")
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d
