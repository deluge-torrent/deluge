#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import base64
import os
from base64 import b64encode
from hashlib import sha1 as sha

import pytest
import pytest_twisted
from twisted.internet import defer, reactor, task
from twisted.internet.error import CannotListenError
from twisted.web.http import FORBIDDEN
from twisted.web.resource import EncodingResourceWrapper, Resource
from twisted.web.server import GzipEncoderFactory, Site
from twisted.web.static import File

import deluge.common
import deluge.component as component
import deluge.core.torrent
from deluge._libtorrent import lt
from deluge.conftest import BaseTestCase
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.error import AddTorrentError, InvalidTorrentError

from . import common

common.disable_new_release_check()


class CookieResource(Resource):
    def render(self, request):
        if request.getCookie(b'password') != b'deluge':
            request.setResponseCode(FORBIDDEN)
            return

        request.setHeader(b'Content-Type', b'application/x-bittorrent')
        with open(
            common.get_test_data_file('ubuntu-9.04-desktop-i386.iso.torrent'), 'rb'
        ) as _file:
            data = _file.read()
        return data


class PartialDownload(Resource):
    def getChild(self, path, request):  # NOQA: N802
        return EncodingResourceWrapper(self, [GzipEncoderFactory()])

    def render(self, request):
        with open(
            common.get_test_data_file('ubuntu-9.04-desktop-i386.iso.torrent'), 'rb'
        ) as _file:
            data = _file.read()
        request.setHeader(b'Content-Length', str(len(data)))
        request.setHeader(b'Content-Type', b'application/x-bittorrent')
        return data


class RedirectResource(Resource):
    def render(self, request):
        request.redirect(b'/ubuntu-9.04-desktop-i386.iso.torrent')
        return b''


class TopLevelResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild(b'cookie', CookieResource())
        self.putChild(b'partial', PartialDownload())
        self.putChild(b'redirect', RedirectResource())
        self.putChild(
            b'ubuntu-9.04-desktop-i386.iso.torrent',
            File(common.get_test_data_file('ubuntu-9.04-desktop-i386.iso.torrent')),
        )


class TestCore(BaseTestCase):
    def set_up(self):
        self.rpcserver = RPCServer(listen=False)
        self.core: Core = Core()
        self.core.config.config['lsd'] = False
        self.clock = task.Clock()
        self.core.torrentmanager.clock = self.clock
        self.listen_port = 51242
        return component.start().addCallback(self.start_web_server)

    def start_web_server(self, result):
        website = Site(TopLevelResource())
        for dummy in range(10):
            try:
                self.webserver = reactor.listenTCP(self.listen_port, website)
            except CannotListenError as ex:
                error = ex
                self.listen_port += 1
            else:
                break
        else:
            raise error

        return result

    def tear_down(self):
        def on_shutdown(result):
            del self.rpcserver
            del self.core
            return self.webserver.stopListening()

        return component.shutdown().addCallback(on_shutdown)

    def add_torrent(self, filename, paused=False):
        if not paused:
            # Patch libtorrent flags starting torrents paused
            self.patch(
                deluge.core.torrentmanager,
                'LT_DEFAULT_ADD_TORRENT_FLAGS',
                lt.torrent_flags.auto_managed
                | lt.torrent_flags.update_subscribe
                | lt.torrent_flags.apply_ip_filter,
            )
        options = {'add_paused': paused, 'auto_managed': False}
        filepath = common.get_test_data_file(filename)
        with open(filepath, 'rb') as _file:
            filedump = b64encode(_file.read())
        torrent_id = self.core.add_torrent_file(filename, filedump, options)
        return torrent_id

    @pytest_twisted.inlineCallbacks
    def test_add_torrent_files(self):
        options = {}
        filenames = ['test.torrent', 'test_torrent.file.torrent']
        files_to_add = []
        for f in filenames:
            filename = common.get_test_data_file(f)
            with open(filename, 'rb') as _file:
                filedump = b64encode(_file.read())
            files_to_add.append((filename, filedump, options))
        errors = yield self.core.add_torrent_files(files_to_add)
        assert len(errors) == 0

    @pytest_twisted.inlineCallbacks
    def test_add_torrent_files_error_duplicate(self):
        options = {}
        filenames = ['test.torrent', 'test.torrent']
        files_to_add = []
        for f in filenames:
            filename = common.get_test_data_file(f)
            with open(filename, 'rb') as _file:
                filedump = b64encode(_file.read())
            files_to_add.append((filename, filedump, options))
        errors = yield self.core.add_torrent_files(files_to_add)
        assert len(errors) == 1
        assert str(errors[0]).startswith('Torrent already in session')

    @pytest_twisted.inlineCallbacks
    def test_add_torrent_file(self):
        options = {}
        filename = common.get_test_data_file('test.torrent')
        with open(filename, 'rb') as _file:
            filedump = b64encode(_file.read())
        torrent_id = yield self.core.add_torrent_file_async(filename, filedump, options)

        # Get the info hash from the test.torrent
        from deluge.bencode import bdecode, bencode

        with open(filename, 'rb') as _file:
            info_hash = sha(bencode(bdecode(_file.read())[b'info'])).hexdigest()
        assert torrent_id == info_hash

    def test_add_torrent_file_invalid_filedump(self):
        options = {}
        filename = common.get_test_data_file('test.torrent')
        with pytest.raises(AddTorrentError):
            self.core.add_torrent_file(filename, False, options)

    @pytest_twisted.inlineCallbacks
    def test_add_torrent_url(self, mock_mkstemp):
        url = (
            'http://localhost:%d/ubuntu-9.04-desktop-i386.iso.torrent'
            % self.listen_port
        )
        options = {}
        info_hash = '60d5d82328b4547511fdeac9bf4d0112daa0ce00'

        torrent_id = yield self.core.add_torrent_url(url, options)
        assert torrent_id == info_hash
        assert not os.path.isfile(mock_mkstemp[1])

    async def test_add_torrent_url_with_cookie(self):
        url = 'http://localhost:%d/cookie' % self.listen_port
        options = {}
        headers = {'Cookie': 'password=deluge'}
        info_hash = '60d5d82328b4547511fdeac9bf4d0112daa0ce00'

        with pytest.raises(Exception):
            await self.core.add_torrent_url(url, options)

        result = await self.core.add_torrent_url(url, options, headers)
        assert result == info_hash

    async def test_add_torrent_url_with_redirect(self):
        url = 'http://localhost:%d/redirect' % self.listen_port
        options = {}
        info_hash = '60d5d82328b4547511fdeac9bf4d0112daa0ce00'

        result = await self.core.add_torrent_url(url, options)
        assert result == info_hash

    async def test_add_torrent_url_with_partial_download(self):
        url = 'http://localhost:%d/partial' % self.listen_port
        options = {}
        info_hash = '60d5d82328b4547511fdeac9bf4d0112daa0ce00'

        result = await self.core.add_torrent_url(url, options)
        assert result == info_hash

    @pytest_twisted.inlineCallbacks
    def test_add_torrent_magnet(self):
        info_hash = '60d5d82328b4547511fdeac9bf4d0112daa0ce00'
        tracker = 'udp://tracker.example.com'
        name = 'test magnet'
        uri = deluge.common.create_magnet_uri(info_hash, name=name, trackers=[tracker])
        options = {}
        torrent_id = yield self.core.add_torrent_magnet(uri, options)
        assert torrent_id == info_hash
        torrent_status = self.core.get_torrent_status(torrent_id, ['name', 'trackers'])
        assert torrent_status['trackers'][0]['url'] == tracker
        assert torrent_status['name'] == name

    def test_resume_torrent(self):
        tid1 = self.add_torrent('test.torrent', paused=True)
        tid2 = self.add_torrent('test_torrent.file.torrent', paused=True)
        # Assert paused
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        assert r1['paused']
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        assert r2['paused']

        self.core.resume_torrent(tid2)
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        assert r1['paused']
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        assert not r2['paused']

    def test_resume_torrent_list(self):
        """Backward compatibility for list of torrent_ids."""
        torrent_id = self.add_torrent('test.torrent', paused=True)
        self.core.resume_torrent([torrent_id])
        result = self.core.get_torrent_status(torrent_id, ['paused'])
        assert not result['paused']

    def test_resume_torrents(self):
        tid1 = self.add_torrent('test.torrent', paused=True)
        tid2 = self.add_torrent('test_torrent.file.torrent', paused=True)
        self.core.resume_torrents([tid1, tid2])
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        assert not r1['paused']
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        assert not r2['paused']

    def test_resume_torrents_all(self):
        """With no torrent_ids param, resume all torrents"""
        tid1 = self.add_torrent('test.torrent', paused=True)
        tid2 = self.add_torrent('test_torrent.file.torrent', paused=True)
        self.core.resume_torrents()
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        assert not r1['paused']
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        assert not r2['paused']

    def test_pause_torrent(self):
        tid1 = self.add_torrent('test.torrent')
        tid2 = self.add_torrent('test_torrent.file.torrent')
        # Assert not paused
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        assert not r1['paused']
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        assert not r2['paused']

        self.core.pause_torrent(tid2)
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        assert not r1['paused']
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        assert r2['paused']

    def test_pause_torrent_list(self):
        """Backward compatibility for list of torrent_ids."""
        torrent_id = self.add_torrent('test.torrent')
        result = self.core.get_torrent_status(torrent_id, ['paused'])
        assert not result['paused']
        self.core.pause_torrent([torrent_id])
        result = self.core.get_torrent_status(torrent_id, ['paused'])
        assert result['paused']

    def test_pause_torrents(self):
        tid1 = self.add_torrent('test.torrent')
        tid2 = self.add_torrent('test_torrent.file.torrent')

        self.core.pause_torrents([tid1, tid2])
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        assert r1['paused']
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        assert r2['paused']

    def test_pause_torrents_all(self):
        """With no torrent_ids param, pause all torrents"""
        tid1 = self.add_torrent('test.torrent')
        tid2 = self.add_torrent('test_torrent.file.torrent')

        self.core.pause_torrents()
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        assert r1['paused']
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        assert r2['paused']

    @pytest_twisted.inlineCallbacks
    def test_prefetch_metadata_existing(self):
        """Check another call with same magnet returns existing deferred."""
        magnet = 'magnet:?xt=urn:btih:ab570cdd5a17ea1b61e970bb72047de141bce173'
        expected = ('ab570cdd5a17ea1b61e970bb72047de141bce173', b'')

        d1 = self.core.prefetch_magnet_metadata(magnet)
        d2 = self.core.prefetch_magnet_metadata(magnet)
        dg = defer.gatherResults([d1, d2], consumeErrors=True)
        self.clock.advance(30)
        result = yield dg
        assert result == [expected] * 2

    @pytest_twisted.inlineCallbacks
    def test_remove_torrent(self):
        options = {}
        filename = common.get_test_data_file('test.torrent')
        with open(filename, 'rb') as _file:
            filedump = b64encode(_file.read())
        torrent_id = yield self.core.add_torrent_file_async(filename, filedump, options)
        removed = self.core.remove_torrent(torrent_id, True)
        assert removed
        assert len(self.core.get_session_state()) == 0

    def test_remove_torrent_invalid(self):
        with pytest.raises(InvalidTorrentError):
            self.core.remove_torrent(
                'torrentidthatdoesntexist',
                True,
            )

    @pytest_twisted.inlineCallbacks
    def test_remove_torrents(self):
        options = {}
        filename = common.get_test_data_file('test.torrent')
        with open(filename, 'rb') as _file:
            filedump = b64encode(_file.read())
        torrent_id = yield self.core.add_torrent_file_async(filename, filedump, options)

        filename2 = common.get_test_data_file('unicode_filenames.torrent')
        with open(filename2, 'rb') as _file:
            filedump = b64encode(_file.read())
        torrent_id2 = yield self.core.add_torrent_file_async(
            filename2, filedump, options
        )
        d = self.core.remove_torrents([torrent_id, torrent_id2], True)

        def test_ret(val):
            assert val == []

        d.addCallback(test_ret)

        def test_session_state(val):
            assert len(self.core.get_session_state()) == 0

        d.addCallback(test_session_state)
        yield d

    @pytest_twisted.inlineCallbacks
    def test_remove_torrents_invalid(self):
        options = {}
        filename = common.get_test_data_file('test.torrent')
        with open(filename, 'rb') as _file:
            filedump = b64encode(_file.read())
            torrent_id = yield self.core.add_torrent_file_async(
                filename, filedump, options
            )
        val = yield self.core.remove_torrents(
            ['invalidid1', 'invalidid2', torrent_id], False
        )
        assert len(val) == 2
        assert val[0] == ('invalidid1', 'torrent_id invalidid1 not in session.')
        assert val[1] == ('invalidid2', 'torrent_id invalidid2 not in session.')

    def test_get_session_status(self):
        status = self.core.get_session_status(
            ['net.recv_tracker_bytes', 'net.sent_tracker_bytes']
        )
        assert isinstance(status, dict)
        assert status['net.recv_tracker_bytes'] == 0
        assert status['net.sent_tracker_bytes'] == 0

    def test_get_session_status_all(self):
        status = self.core.get_session_status([])
        assert isinstance(status, dict)
        assert 'upload_rate' in status
        assert 'net.recv_bytes' in status

    def test_get_session_status_depr(self):
        status = self.core.get_session_status(['num_peers', 'num_unchoked'])
        assert isinstance(status, dict)
        assert status['num_peers'] == 0
        assert status['num_unchoked'] == 0

    def test_get_session_status_rates(self):
        status = self.core.get_session_status(['upload_rate', 'download_rate'])
        assert isinstance(status, dict)
        assert status['upload_rate'] == 0

    def test_get_session_status_ratio(self):
        status = self.core.get_session_status(['write_hit_ratio', 'read_hit_ratio'])
        assert isinstance(status, dict)
        assert status['write_hit_ratio'] == 0.0
        assert status['read_hit_ratio'] == 0.0

    def test_get_free_space(self):
        space = self.core.get_free_space('.')
        assert isinstance(space, int)
        assert space >= 0
        assert self.core.get_free_space('/someinvalidpath') == -1

    @pytest.mark.slow
    def test_test_listen_port(self):
        d = self.core.test_listen_port()

        def result(r):
            assert r in (True, False)

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
            assert (
                deluge.core.torrent.sanitize_filepath(key, folder=False)
                == pathlist[key]
            )

            assert (
                deluge.core.torrent.sanitize_filepath(key, folder=True)
                == pathlist[key] + '/'
            )

    def test_get_set_config_values(self):
        assert self.core.get_config_values(['abc', 'foo']) == {'foo': None, 'abc': None}
        assert self.core.get_config_value('foobar') is None
        self.core.set_config({'abc': 'def', 'foo': 10, 'foobar': 'barfoo'})
        assert self.core.get_config_values(['foo', 'abc']) == {'foo': 10, 'abc': 'def'}
        assert self.core.get_config_value('foobar') == 'barfoo'

    def test_read_only_config_keys(self):
        key = 'max_upload_speed'
        self.core.read_only_config_keys = [key]

        old_value = self.core.get_config_value(key)
        self.core.set_config({key: old_value + 10})
        new_value = self.core.get_config_value(key)
        assert old_value == new_value

        self.core.read_only_config_keys = None

    def test__create_peer_id(self):
        assert self.core._create_peer_id('2.0.0') == '-DE200s-'
        assert self.core._create_peer_id('2.0.0.dev15') == '-DE200D-'
        assert self.core._create_peer_id('2.0.1rc1') == '-DE201r-'
        assert self.core._create_peer_id('2.11.0b2') == '-DE2B0b-'
        assert self.core._create_peer_id('2.4.12b2.dev3') == '-DE24CD-'

    @pytest.mark.parametrize(
        'path',
        [
            common.get_test_data_file('deluge.png'),
            os.path.dirname(common.get_test_data_file('deluge.png')),
        ],
    )
    @pytest.mark.parametrize('piece_length', [2**14, 2**16])
    @pytest_twisted.inlineCallbacks
    def test_create_torrent(self, path, tmp_path, piece_length):
        target = tmp_path / 'test.torrent'

        filename, filedump = yield self.core.create_torrent(
            path=path,
            tracker=None,
            piece_length=piece_length,
            target=target,
            add_to_session=False,
        )
        filecontent = base64.b64decode(filedump)

        with open(target, 'rb') as f:
            assert f.read() == filecontent

        lt.torrent_info(filecontent)
