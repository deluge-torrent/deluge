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
from deluge.ui.web.json_api import GRID_STATE_EXPIRY, WebApi

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
            assert isinstance(result, tuple)
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
        host = list(self.deluge_web.web_api.hostlist.get_host_info(self.host_id))
        host[3] = 'Online'
        host[4] = '2.0.0.dev562'
        status = yield self.deluge_web.web_api.get_host_status(self.host_id)
        assert status == tuple(status)

    def test_get_hosts(self):
        hosts = self.deluge_web.web_api.hostlist.get_hosts_info()
        assert self.deluge_web.web_api.get_hosts() == hosts

    def test_add_host(self):
        conn = ['abcdef', '10.0.0.1', 0, 'user123', 'pass123']
        assert not self.deluge_web.web_api.hostlist.get_host_info(conn[0])
        # Add valid host
        result, host_id = self.deluge_web.web_api.add_host(
            conn[1], conn[2], conn[3], conn[4]
        )
        assert result
        conn[0] = host_id
        assert (
            list(self.deluge_web.web_api.hostlist.get_host_info(conn[0])) == conn[0:4]
        )

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
        assert self.deluge_web.web_api.hostlist.get_host_info(conn[0]) == conn[0:4]
        # Remove valid host
        assert self.deluge_web.web_api.remove_host(conn[0])
        assert not self.deluge_web.web_api.hostlist.get_host_info(conn[0])
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


class TestGridDiff:
    """update_ui's per-session diffing.

    _diff_against_grid_state touches nothing but self.grid_state, so it is
    exercised directly rather than through the web server fixture.
    """

    def setup_method(self):
        self.api = WebApi.__new__(WebApi)
        self.api.grid_state = {}

    def diff(self, torrents, keys=None, filters=None, session='s1'):
        return self.api._diff_against_grid_state(
            session, keys or ['name'], filters if filters is not None else {}, torrents
        )

    def test_without_a_baseline_returns_everything(self):
        torrents = {'a': {'name': 'one'}}
        sent, removed = self.diff(torrents)
        # update_ui tells a diff from a full status by identity, so this must
        # be the dict it was handed and not a copy of it.
        assert sent is torrents
        assert removed == []

    def test_drops_unchanged_torrents(self):
        self.diff({'a': {'name': 'one'}, 'b': {'name': 'two'}})
        sent, removed = self.diff({'a': {'name': 'one'}, 'b': {'name': 'two'}})
        assert sent == {}
        assert removed == []

    def test_sends_only_changed_fields(self):
        keys = ['name', 'progress']
        self.diff({'a': {'name': 'one', 'progress': 1}}, keys=keys)
        sent, removed = self.diff({'a': {'name': 'one', 'progress': 2}}, keys=keys)
        assert sent == {'a': {'progress': 2}}
        assert removed == []

    def test_sends_a_full_status_for_a_torrent_the_client_has_not_seen(self):
        self.diff({'a': {'name': 'one'}})
        sent, removed = self.diff({'a': {'name': 'one'}, 'b': {'name': 'two'}})
        assert sent == {'b': {'name': 'two'}}
        assert removed == []

    def test_reports_torrents_that_went_away(self):
        self.diff({'a': {'name': 'one'}, 'b': {'name': 'two'}})
        sent, removed = self.diff({'a': {'name': 'one'}})
        assert sent == {}
        assert removed == ['b']

    def test_a_key_appearing_counts_as_a_change(self):
        self.diff({'a': {'name': 'one'}})
        sent, removed = self.diff({'a': {'name': 'one', 'progress': 1}})
        assert sent == {'a': {'progress': 1}}

    def test_restarts_when_the_requested_keys_change(self):
        self.diff({'a': {'name': 'one'}}, keys=['name'])
        torrents = {'a': {'name': 'one', 'progress': 1}}
        sent, removed = self.diff(torrents, keys=['name', 'progress'])
        assert sent is torrents
        assert removed == []

    def test_restarts_when_the_filters_change(self):
        self.diff({'a': {'name': 'one'}})
        torrents = {'a': {'name': 'one'}}
        sent, removed = self.diff(torrents, filters={'state': ['Seeding']})
        assert sent is torrents
        assert removed == []

    def test_keeps_a_baseline_per_session(self):
        self.diff({'a': {'name': 'one'}}, session='s1')
        torrents = {'a': {'name': 'one'}}
        sent, removed = self.diff(torrents, session='s2')
        assert sent is torrents
        assert removed == []

    def test_forgets_a_session_that_stopped_polling(self):
        self.diff({'a': {'name': 'one'}})
        self.api.grid_state['s1']['time'] -= GRID_STATE_EXPIRY + 1
        torrents = {'a': {'name': 'one'}}
        sent, _ = self.diff(torrents)
        assert sent is torrents
        assert list(self.api.grid_state) == ['s1']
