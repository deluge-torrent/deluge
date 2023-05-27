#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import json
from io import BytesIO

import pytest
import pytest_twisted
from twisted.internet import defer, reactor
from twisted.web.client import Agent, FileBodyProducer
from twisted.web.http_headers import Headers
from twisted.web.static import File

import deluge.component as component

from . import common
from .common_web import WebServerTestBase

common.disable_new_release_check()


class TestWebAPI(WebServerTestBase):
    @pytest.mark.xfail(reason='This just logs an error at the moment.')
    async def test_connect_invalid_host(self):
        with pytest.raises(Exception):
            await self.deluge_web.web_api.connect('id')

    def test_connect(self, client):
        d = self.deluge_web.web_api.connect(self.host_id)

        def on_connect(result):
            assert type(result) == tuple
            assert len(result) > 0
            return result

        d.addCallback(on_connect)
        d.addErrback(self.fail)
        return d

    def test_disconnect(self):
        d = self.deluge_web.web_api.connect(self.host_id)

        @defer.inlineCallbacks
        def on_connect(result):
            assert self.deluge_web.web_api.connected()
            yield self.deluge_web.web_api.disconnect()
            assert not self.deluge_web.web_api.connected()

        d.addCallback(on_connect)
        d.addErrback(self.fail)
        return d

    def test_get_config(self):
        config = self.deluge_web.web_api.get_config()
        assert self.deluge_web.port == config['port']

    def test_set_config(self):
        config = self.deluge_web.web_api.get_config()
        config['pwd_salt'] = 'new_salt'
        config['pwd_sha1'] = 'new_sha'
        config['sessions'] = {
            '233f23632af0a74748bc5dd1d8717564748877baa16420e6898e17e8aa365e6e': {
                'login': 'skrot',
                'expires': 1460030877.0,
                'level': 10,
            }
        }
        self.deluge_web.web_api.set_config(config)
        web_config = component.get('DelugeWeb').config.config
        assert config['pwd_salt'] != web_config['pwd_salt']
        assert config['pwd_sha1'] != web_config['pwd_sha1']
        assert config['sessions'] != web_config['sessions']

    @defer.inlineCallbacks
    def get_host_status(self):
        host = list(self.deluge_web.web_api._get_host(self.host_id))
        host[3] = 'Online'
        host[4] = '2.0.0.dev562'
        status = yield self.deluge_web.web_api.get_host_status(self.host_id)
        assert status == tuple(status)

    def test_get_host(self):
        assert not self.deluge_web.web_api._get_host('invalid_id')
        conn = list(self.deluge_web.web_api.hostlist.get_hosts_info()[0])
        assert self.deluge_web.web_api._get_host(conn[0]) == conn[0:4]

    def test_add_host(self):
        conn = ['abcdef', '10.0.0.1', 0, 'user123', 'pass123']
        assert not self.deluge_web.web_api._get_host(conn[0])
        # Add valid host
        result, host_id = self.deluge_web.web_api.add_host(
            conn[1], conn[2], conn[3], conn[4]
        )
        assert result
        conn[0] = host_id
        assert self.deluge_web.web_api._get_host(conn[0]) == conn[0:4]

        # Add already existing host
        ret = self.deluge_web.web_api.add_host(conn[1], conn[2], conn[3], conn[4])
        assert ret == (False, 'Host details already in hostlist')

        # Add invalid port
        conn[2] = 'bad port'
        ret = self.deluge_web.web_api.add_host(conn[1], conn[2], conn[3], conn[4])
        assert ret == (False, 'Invalid port. Must be an integer')

    def test_remove_host(self):
        conn = ['connection_id', '', 0, '', '']
        self.deluge_web.web_api.hostlist.config['hosts'].append(conn)
        assert self.deluge_web.web_api._get_host(conn[0]) == conn[0:4]
        # Remove valid host
        assert self.deluge_web.web_api.remove_host(conn[0])
        assert not self.deluge_web.web_api._get_host(conn[0])
        # Remove non-existing host
        assert not self.deluge_web.web_api.remove_host(conn[0])

    def test_get_torrent_info(self):
        filename = common.get_test_data_file('test.torrent')
        ret = self.deluge_web.web_api.get_torrent_info(filename)
        assert ret['name'] == 'azcvsupdater_2.6.2.jar'
        assert ret['info_hash'] == 'ab570cdd5a17ea1b61e970bb72047de141bce173'
        assert 'files_tree' in ret

    def test_get_torrent_info_with_md5(self):
        filename = common.get_test_data_file('md5sum.torrent')
        ret = self.deluge_web.web_api.get_torrent_info(filename)
        # JSON dumping happens during response creation in normal usage
        # JSON serialization may fail if any of the dictionary items are byte arrays rather than strings
        ret = json.loads(json.dumps(ret))
        assert ret['name'] == 'test'
        assert ret['info_hash'] == 'f6408ba9944cf9fe01b547b28f336b3ee6ec32c5'
        assert 'files_tree' in ret

    def test_get_magnet_info(self):
        ret = self.deluge_web.web_api.get_magnet_info(
            'magnet:?xt=urn:btih:SU5225URMTUEQLDXQWRB2EQWN6KLTYKN'
        )
        assert ret['name'] == '953bad769164e8482c7785a21d12166f94b9e14d'
        assert ret['info_hash'] == '953bad769164e8482c7785a21d12166f94b9e14d'
        assert 'files_tree' in ret

    @pytest_twisted.inlineCallbacks
    def test_get_torrent_files(self):
        yield self.deluge_web.web_api.connect(self.host_id)
        filename = common.get_test_data_file('test.torrent')
        torrents = [
            {'path': filename, 'options': {'download_location': '/home/deluge/'}}
        ]
        yield self.deluge_web.web_api.add_torrents(torrents)
        ret = yield self.deluge_web.web_api.get_torrent_files(
            'ab570cdd5a17ea1b61e970bb72047de141bce173'
        )
        assert ret['type'] == 'dir'
        assert ret['contents'] == {
            'azcvsupdater_2.6.2.jar': {
                'priority': 4,
                'index': 0,
                'offset': 0,
                'progress': 0.0,
                'path': 'azcvsupdater_2.6.2.jar',
                'type': 'file',
                'size': 307949,
            }
        }

    @pytest_twisted.inlineCallbacks
    def test_download_torrent_from_url(self):
        filename = 'ubuntu-9.04-desktop-i386.iso.torrent'
        self.deluge_web.top_level.putChild(
            filename.encode(), File(common.get_test_data_file(filename))
        )
        url = 'http://localhost:%d/%s' % (self.deluge_web.port, filename)
        res = yield self.deluge_web.web_api.download_torrent_from_url(url)
        assert res.endswith(filename)

    @pytest_twisted.inlineCallbacks
    def test_invalid_json(self):
        """
        If json_api._send_response does not return server.NOT_DONE_YET
        this error is thrown when json is invalid:
        exceptions.RuntimeError: Request.write called on a request after Request.finish was called.

        """
        agent = Agent(reactor)
        bad_body = b'{ method": "auth.login" }'
        d = yield agent.request(
            b'POST',
            b'http://127.0.0.1:%i/json' % self.deluge_web.port,
            Headers(
                {
                    b'User-Agent': [b'Twisted Web Client Example'],
                    b'Content-Type': [b'application/json'],
                }
            ),
            FileBodyProducer(BytesIO(bad_body)),
        )
        yield d
