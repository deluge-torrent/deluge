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
import deluge.error


class CoreTestCase(unittest.TestCase):
    def setUp(self):
        common.set_tmp_config_dir()
        self.rpcserver = RPCServer(listen=False)
        self.core = Core()
        d = component.start()
        return d

    def tearDown(self):

        def on_shutdown(result):
            component._ComponentRegistry.components = {}
            del self.rpcserver
            del self.core

        return component.shutdown().addCallback(on_shutdown)

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
        url = "http://deluge-torrent.org/ubuntu-9.04-desktop-i386.iso.torrent"
        options = {}
        info_hash = "60d5d82328b4547511fdeac9bf4d0112daa0ce00"

        d = self.core.add_torrent_url(url, options)
        d.addCallback(self.assertEquals, info_hash)
        return d

    def test_add_torrent_url_with_cookie(self):
        url = "http://deluge-torrent.org/test_torrent.php?test=cookie"
        options = {}
        headers = { "Cookie" : "password=deluge" }
        info_hash = "60d5d82328b4547511fdeac9bf4d0112daa0ce00"

        d = self.core.add_torrent_url(url, options)
        d.addCallbacks(self.fail, self.assertIsInstance, errbackArgs=(Failure,))

        d = self.core.add_torrent_url(url, options, headers)
        d.addCallback(self.assertEquals, info_hash)

        return d

    def test_add_torrent_url_with_redirect(self):
        url = "http://deluge-torrent.org/test_torrent.php?test=redirect"
        options = {}
        info_hash = "60d5d82328b4547511fdeac9bf4d0112daa0ce00"

        d = self.core.add_torrent_url(url, options)
        d.addCallback(self.assertEquals, info_hash)

        return d

    def test_add_torrent_url_with_partial_download(self):
        url = "http://deluge-torrent.org/test_torrent.php?test=partial"
        options = {}
        info_hash = "60d5d82328b4547511fdeac9bf4d0112daa0ce00"

        d = self.core.add_torrent_url(url, options)
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

        self.assertRaises(deluge.error.InvalidTorrentError, self.core.remove_torrent, "torrentidthatdoesntexist", True)

        ret = self.core.remove_torrent(torrent_id, True)

        self.assertTrue(ret)
        self.assertEquals(len(self.core.get_session_state()), 0)

    def test_get_session_status(self):
        status = self.core.get_session_status(["upload_rate", "download_rate"])
        self.assertEquals(type(status), dict)
        self.assertEquals(status["upload_rate"], 0.0)

    def test_get_cache_status(self):
        status = self.core.get_cache_status()
        self.assertEquals(type(status), dict)
        self.assertEquals(status["write_hit_ratio"], 0.0)
        self.assertEquals(status["read_hit_ratio"], 0.0)

    def test_get_free_space(self):
        space = self.core.get_free_space(".")
        self.assertTrue(type(space) in (int, long))
        self.assertTrue(space >= 0)
        self.assertEquals(self.core.get_free_space("/someinvalidpath"), 0)

    def test_test_listen_port(self):
        d = self.core.test_listen_port()

        def result(r):
            self.assertTrue(r in (True, False))

        d.addCallback(result)
        return d

    def test_sanitize_filepath(self):
        pathlist = {
            '\\backslash\\path\\' : 'backslash/path',
            ' single_file ': 'single_file',
            '..' : '',
            '/../..../': '',
            '  Def ////ad./ / . . /b  d /file': 'Def/ad./. ./b  d/file',
            '/ test /\\.. /.file/': 'test/.file',
            'mytorrent/subfold/file1': 'mytorrent/subfold/file1',
            'Torrent/folder/': 'Torrent/folder',
        }

        for key in pathlist:
            self.assertEquals(deluge.core.torrent.sanitize_filepath(key, folder=False), pathlist[key])
            self.assertEquals(deluge.core.torrent.sanitize_filepath(key, folder=True), pathlist[key] + '/')

    def test_read_only_config_keys(self):
        key = 'max_upload_speed'
        self.core.read_only_config_keys = [key]

        old_value = self.core.get_config_value(key)
        self.core.set_config({key: old_value + 10})
        new_value = self.core.get_config_value(key)

        self.assertEquals(old_value, new_value)

        self.core.read_only_config_keys = None