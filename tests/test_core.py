from twisted.trial import unittest
from twisted.python.failure import Failure

try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha

import common

from deluge.core.rpcserver import RPCServer
from deluge.core.core import Core
import deluge.component as component

class CoreTestCase(unittest.TestCase):
    def setUp(self):
        common.set_tmp_config_dir()
        self.rpcserver = RPCServer(listen=False)
        self.core = Core()
        component.start()

    def tearDown(self):
        component.stop()
        component.shutdown()
        del self.rpcserver
        del self.core

    def test_add_torrent_file(self):
        options = {}
        filename = "../test.torrent"
        import base64
        torrent_id = self.core.add_torrent_file(filename, base64.encodestring(open(filename).read()), options)

        # Get the info hash from the test.torrent
        from deluge.bencode import bdecode, bencode
        info_hash = sha(bencode(bdecode(open(filename).read())["info"])).hexdigest()

        self.assertEquals(torrent_id, info_hash)

    def test_add_torrent_url(self):
        url = "http://torrent.ubuntu.com:6969/file?info_hash=%60%D5%D8%23%28%B4Tu%11%FD%EA%C9%BFM%01%12%DA%A0%CE%00"
        options = {}
        info_hash = "60d5d82328b4547511fdeac9bf4d0112daa0ce00"

        d = self.core.add_torrent_url(url, options)
        d.addCallback(self.assertEquals, info_hash)
        return d

    def test_add_torrent_url_with_cookie(self):
        url = "http://cgi.cse.unsw.edu.au/~johnnyg/torrent.php"
        options = {}
        headers = { "Cookie" : "password=deluge" }
        info_hash = "60d5d82328b4547511fdeac9bf4d0112daa0ce00"

        d = self.core.add_torrent_url(url, options)
        d.addCallbacks(self.fail, self.assertIsInstance, Failure)

        d = self.core.add_torrent_url(url, options, headers)
        d.addCallback(self.assertEquals, info_hash)

        return d

    def test_add_magnet(self):
        info_hash = "60d5d82328b4547511fdeac9bf4d0112daa0ce00"
        import deluge.common
        uri = deluge.common.create_magnet_uri(info_hash)
        options = {}

        torrent_id = self.core.add_torrent_magnet(uri, options)
        self.assertEquals(torrent_id, info_hash)

    def test_remove_torrent(self):
        options = {}
        filename = "../test.torrent"
        import base64
        torrent_id = self.core.add_torrent_file(filename, base64.encodestring(open(filename).read()), options)
        
        self.core.remove_torrent(torrent_id, True)
        
        self.assertEquals(len(self.core.get_session_state()), 0)

        
