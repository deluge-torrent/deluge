import base64
import os
from hashlib import sha1 as sha

import pytest
from twisted.internet import reactor
from twisted.internet.error import CannotListenError
from twisted.python.failure import Failure
from twisted.web.http import FORBIDDEN
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.static import File

import deluge.component as component
import deluge.core.torrent
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.error import InvalidTorrentError
from deluge.ui.web.common import compress

from . import common
from .basetest import BaseTestCase

common.disable_new_release_check()

rpath = common.rpath


class CookieResource(Resource):

    def render(self, request):
        if request.getCookie("password") != "deluge":
            request.setResponseCode(FORBIDDEN)
            return

        request.setHeader("Content-Type", "application/x-bittorrent")
        return open(rpath("ubuntu-9.04-desktop-i386.iso.torrent")).read()


class PartialDownload(Resource):

    def render(self, request):
        data = open(rpath("ubuntu-9.04-desktop-i386.iso.torrent")).read()
        request.setHeader("Content-Type", len(data))
        request.setHeader("Content-Type", "application/x-bittorrent")
        if request.requestHeaders.hasHeader("accept-encoding"):
            return compress(data, request)
        return data


class RedirectResource(Resource):

    def render(self, request):
        request.redirect("/ubuntu-9.04-desktop-i386.iso.torrent")
        return ""


class TopLevelResource(Resource):

    addSlash = True

    def __init__(self):
        Resource.__init__(self)
        self.putChild("cookie", CookieResource())
        self.putChild("partial", PartialDownload())
        self.putChild("redirect", RedirectResource())
        self.putChild("ubuntu-9.04-desktop-i386.iso.torrent",
                      File(common.rpath("ubuntu-9.04-desktop-i386.iso.torrent")))


class CoreTestCase(BaseTestCase):

    def set_up(self):
        common.set_tmp_config_dir()
        self.rpcserver = RPCServer(listen=False)
        self.core = Core()
        self.listen_port = 51242
        return component.start().addCallback(self.start_web_server)

    def start_web_server(self, result):
        self.website = Site(TopLevelResource())
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
        return result

    def tear_down(self):

        def on_shutdown(result):
            del self.rpcserver
            del self.core
            return self.webserver.stopListening()

        return component.shutdown().addCallback(on_shutdown)

    def test_add_torrent_file(self):
        options = {}
        filename = os.path.join(os.path.dirname(__file__), "test.torrent")
        torrent_id = self.core.add_torrent_file(filename, base64.encodestring(open(filename).read()), options)

        # Get the info hash from the test.torrent
        from deluge.bencode import bdecode, bencode
        info_hash = sha(bencode(bdecode(open(filename).read())["info"])).hexdigest()

        self.assertEquals(torrent_id, info_hash)

    def test_add_torrent_url(self):
        url = "http://localhost:%d/ubuntu-9.04-desktop-i386.iso.torrent" % self.listen_port
        options = {}
        info_hash = "60d5d82328b4547511fdeac9bf4d0112daa0ce00"

        d = self.core.add_torrent_url(url, options)
        d.addCallback(self.assertEquals, info_hash)
        return d

    def test_add_torrent_url_with_cookie(self):
        url = "http://localhost:%d/cookie" % self.listen_port
        options = {}
        headers = {"Cookie": "password=deluge"}
        info_hash = "60d5d82328b4547511fdeac9bf4d0112daa0ce00"

        d = self.core.add_torrent_url(url, options)
        d.addCallbacks(self.fail, self.assertIsInstance, errbackArgs=(Failure,))

        d = self.core.add_torrent_url(url, options, headers)
        d.addCallbacks(self.assertEquals, self.fail, callbackArgs=(info_hash,))

        return d

    def test_add_torrent_url_with_redirect(self):
        url = "http://localhost:%d/redirect" % self.listen_port
        options = {}
        info_hash = "60d5d82328b4547511fdeac9bf4d0112daa0ce00"

        d = self.core.add_torrent_url(url, options)
        d.addCallback(self.assertEquals, info_hash)

        return d

    def test_add_torrent_url_with_partial_download(self):
        url = "http://localhost:%d/partial" % self.listen_port
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
        filename = os.path.join(os.path.dirname(__file__), "test.torrent")
        torrent_id = self.core.add_torrent_file(filename, base64.encodestring(open(filename).read()), options)
        removed = self.core.remove_torrent(torrent_id, True)
        self.assertTrue(removed)
        self.assertEquals(len(self.core.get_session_state()), 0)

    def test_remove_torrent_invalid(self):
        d = self.core.remove_torrents(["torrentidthatdoesntexist"], True)

        def test_true(val):
            self.assertTrue(val[0][0] == "torrentidthatdoesntexist")

            self.assertTrue(type(val[0][1]) == InvalidTorrentError)
        d.addCallback(test_true)
        return d

    def test_remove_torrents(self):
        options = {}
        filename = os.path.join(os.path.dirname(__file__), "test.torrent")
        torrent_id = self.core.add_torrent_file(filename, base64.encodestring(open(filename).read()), options)
        filename2 = os.path.join(os.path.dirname(__file__), "unicode_filenames.torrent")
        torrent_id2 = self.core.add_torrent_file(filename2, base64.encodestring(open(filename2).read()), options)
        d = self.core.remove_torrents([torrent_id, torrent_id2], True)

        def test_ret(val):
            self.assertTrue(val == [])
        d.addCallback(test_ret)

        def test_session_state(val):
            self.assertEquals(len(self.core.get_session_state()), 0)
        d.addCallback(test_session_state)
        return d

    def test_remove_torrents_invalid(self):
        options = {}
        filename = os.path.join(os.path.dirname(__file__), "test.torrent")
        torrent_id = self.core.add_torrent_file(filename, base64.encodestring(open(filename).read()), options)
        d = self.core.remove_torrents(["invalidid1", "invalidid2", torrent_id], False)

        def test_ret(val):
            self.assertTrue(len(val) == 2)
            self.assertTrue(val[0][0] == "invalidid1")
            self.assertTrue(type(val[0][1]) == InvalidTorrentError)
            self.assertTrue(val[1][0] == "invalidid2")
            self.assertTrue(type(val[1][1]) == InvalidTorrentError)
        d.addCallback(test_ret)
        return d

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
        self.assertEquals(self.core.get_free_space("/someinvalidpath"), -1)

    @pytest.mark.slow
    def test_test_listen_port(self):
        d = self.core.test_listen_port()

        def result(r):
            self.assertTrue(r in (True, False))

        d.addCallback(result)
        return d

    def test_sanitize_filepath(self):
        pathlist = {
            '\\backslash\\path\\': 'backslash/path',
            ' single_file ': 'single_file',
            '..': '',
            '/../..../': '',
            '  Def ////ad./ / . . /b  d /file': 'Def/ad./. ./b  d/file',
            '/ test /\\.. /.file/': 'test/.file',
            'mytorrent/subfold/file1': 'mytorrent/subfold/file1',
            'Torrent/folder/': 'Torrent/folder',
        }

        for key in pathlist:
            self.assertEquals(deluge.core.torrent.sanitize_filepath(key, folder=False), pathlist[key])
            self.assertEquals(deluge.core.torrent.sanitize_filepath(key, folder=True), pathlist[key] + '/')

    def test_get_set_config_values(self):
        self.assertEquals(self.core.get_config_values(["abc", "foo"]), {"foo": None, "abc": None})
        self.assertEquals(self.core.get_config_value("foobar"), None)
        self.core.set_config({"abc": "def", "foo": 10, "foobar": "barfoo"})
        self.assertEquals(self.core.get_config_values(["foo", "abc"]), {"foo": 10, "abc": "def"})
        self.assertEquals(self.core.get_config_value("foobar"), "barfoo")
