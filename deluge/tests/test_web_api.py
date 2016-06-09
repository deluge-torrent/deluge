# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os
from StringIO import StringIO

from twisted.internet import defer, reactor
from twisted.python.failure import Failure
from twisted.web.client import Agent, FileBodyProducer
from twisted.web.http_headers import Headers
from twisted.web.static import File

import deluge.common
import deluge.component as component
import deluge.ui.web.auth
import deluge.ui.web.server
from deluge import configmanager
from deluge.ui.client import client
from deluge.ui.web.server import DelugeWeb

from . import common
from .basetest import BaseTestCase
from .daemon_base import DaemonBase

common.disable_new_release_check()


class WebAPITestCase(BaseTestCase, DaemonBase):

    def set_up(self):
        self.host_id = None
        deluge.ui.web.server.reactor = common.ReactorOverride()
        d = self.common_set_up()
        d.addCallback(self.start_core)
        d.addCallback(self.start_webapi)
        return d

    def start_webapi(self, arg):
        self.webserver_listen_port = 8999

        config_defaults = deluge.ui.web.server.CONFIG_DEFAULTS.copy()
        config_defaults["port"] = self.webserver_listen_port
        self.config = configmanager.ConfigManager("web.conf", config_defaults)

        self.deluge_web = DelugeWeb(daemon=False)

        host = list(self.deluge_web.web_api.host_list["hosts"][0])
        host[2] = self.listen_port
        self.deluge_web.web_api.host_list["hosts"][0] = tuple(host)
        self.host_id = host[0]
        self.deluge_web.start()

    def tear_down(self):
        d = component.shutdown()
        d.addCallback(self.terminate_core)
        return d

    def test_connect_invalid_host(self):
        d = self.deluge_web.web_api.connect("id")
        d.addCallback(self.fail)
        d.addErrback(self.assertIsInstance, Failure)
        return d

    def test_connect(self):
        d = self.deluge_web.web_api.connect(self.host_id)

        def on_connect(result):
            self.assertEquals(type(result), tuple)
            self.assertTrue(len(result) > 0)
            self.addCleanup(client.disconnect)
            return result

        d.addCallback(on_connect)
        d.addErrback(self.fail)
        return d

    def test_disconnect(self):
        d = self.deluge_web.web_api.connect(self.host_id)

        @defer.inlineCallbacks
        def on_connect(result):
            self.assertTrue(self.deluge_web.web_api.connected())
            yield self.deluge_web.web_api.disconnect()
            self.assertFalse(self.deluge_web.web_api.connected())

        d.addCallback(on_connect)
        d.addErrback(self.fail)
        return d

    def test_get_config(self):
        config = self.deluge_web.web_api.get_config()
        self.assertEquals(self.webserver_listen_port, config["port"])

    def test_set_config(self):
        config = self.deluge_web.web_api.get_config()
        config["pwd_salt"] = "new_salt"
        config["pwd_sha1"] = 'new_sha'
        config["sessions"] = {
            "233f23632af0a74748bc5dd1d8717564748877baa16420e6898e17e8aa365e6e": {
                "login": "skrot",
                "expires": 1460030877.0,
                "level": 10
            }
        }
        self.deluge_web.web_api.set_config(config)
        web_config = component.get("DelugeWeb").config.config
        self.assertNotEquals(config["pwd_salt"], web_config["pwd_salt"])
        self.assertNotEquals(config["pwd_sha1"], web_config["pwd_sha1"])
        self.assertNotEquals(config["sessions"], web_config["sessions"])

    @defer.inlineCallbacks
    def get_host_status(self):
        host = list(self.deluge_web.web_api._get_host(self.host_id))
        host[3] = 'Online'
        host[4] = u'2.0.0.dev562'
        status = yield self.deluge_web.web_api.get_host_status(self.host_id)
        self.assertEquals(status, tuple(status))

    def test_get_host(self):
        self.assertFalse(self.deluge_web.web_api._get_host("invalid_id"))
        conn = self.deluge_web.web_api.host_list["hosts"][0]
        self.assertEquals(self.deluge_web.web_api._get_host(conn[0]), conn)

    def test_add_host(self):
        conn = [None, '', 0, '', '']
        self.assertFalse(self.deluge_web.web_api._get_host(conn[0]))
        # Add valid host
        ret = self.deluge_web.web_api.add_host(conn[1], conn[2], conn[3], conn[4])
        self.assertEquals(ret[0], True)
        conn[0] = ret[1]
        self.assertEquals(self.deluge_web.web_api._get_host(conn[0]), conn)

        # Add already existing host
        ret = self.deluge_web.web_api.add_host(conn[1], conn[2], conn[3], conn[4])
        self.assertEquals(ret, (False, "Host already in the list"))

        # Add invalid port
        conn[2] = "bad port"
        ret = self.deluge_web.web_api.add_host(conn[1], conn[2], conn[3], conn[4])
        self.assertEquals(ret, (False, "Port is invalid"))

    def test_remove_host(self):
        conn = ['connection_id', '', 0, '', '']
        self.deluge_web.web_api.host_list["hosts"].append(conn)
        self.assertEquals(self.deluge_web.web_api._get_host(conn[0]), conn)
        # Remove valid host
        self.assertTrue(self.deluge_web.web_api.remove_host(conn[0]))
        self.assertFalse(self.deluge_web.web_api._get_host(conn[0]))
        # Remove non-existing host
        self.assertFalse(self.deluge_web.web_api.remove_host(conn[0]))

    def test_get_torrent_info(self):
        filename = os.path.join(os.path.dirname(__file__), "test.torrent")
        ret = self.deluge_web.web_api.get_torrent_info(filename)
        self.assertEquals(ret["name"], "azcvsupdater_2.6.2.jar")
        self.assertEquals(ret["info_hash"], "ab570cdd5a17ea1b61e970bb72047de141bce173")
        self.assertTrue("files_tree" in ret)

    def test_get_magnet_info(self):
        ret = self.deluge_web.web_api.get_magnet_info("magnet:?xt=urn:btih:SU5225URMTUEQLDXQWRB2EQWN6KLTYKN")
        self.assertEquals(ret["name"], "953bad769164e8482c7785a21d12166f94b9e14d")
        self.assertEquals(ret["info_hash"], "953bad769164e8482c7785a21d12166f94b9e14d")
        self.assertTrue("files_tree" in ret)

    @defer.inlineCallbacks
    def test_get_torrent_files(self):
        yield self.deluge_web.web_api.connect(self.host_id)
        filename = os.path.join(os.path.dirname(__file__), "test.torrent")
        torrents = [{"path": filename, "options": {"download_location": "/home/deluge/"}}]
        yield self.deluge_web.web_api.add_torrents(torrents)
        ret = yield self.deluge_web.web_api.get_torrent_files("ab570cdd5a17ea1b61e970bb72047de141bce173")
        self.assertEquals(ret["type"], "dir")
        self.assertEquals(ret["contents"], {u'azcvsupdater_2.6.2.jar':
                                            {'priority': 1, u'index': 0, u'offset': 0, 'progress': 0.0, u'path':
                                             u'azcvsupdater_2.6.2.jar', 'type': 'file', u'size': 307949}})

    @defer.inlineCallbacks
    def test_download_torrent_from_url(self):
        filename = "ubuntu-9.04-desktop-i386.iso.torrent"
        self.deluge_web.top_level.putChild(filename, File(common.rpath(filename)))
        url = "http://localhost:%d/%s" % (self.webserver_listen_port, filename)
        res = yield self.deluge_web.web_api.download_torrent_from_url(url)
        self.assertTrue(res.endswith(filename))

    @defer.inlineCallbacks
    def test_invalid_json(self):
        """
        If json_api._send_response does not return server.NOT_DONE_YET
        this error is thrown when json is invalid:
        exceptions.RuntimeError: Request.write called on a request after Request.finish was called.

        """
        agent = Agent(reactor)
        bad_body = '{ method": "auth.login" }'
        d = yield agent.request(
            'POST',
            'http://127.0.0.1:%s/json' % self.webserver_listen_port,
            Headers({'User-Agent': ['Twisted Web Client Example'],
                     'Content-Type': ['application/json']}),
            FileBodyProducer(StringIO(bad_body)))
        yield d
