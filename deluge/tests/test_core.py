# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

from base64 import b64encode
from hashlib import sha1 as sha

import pytest
from six import integer_types
from twisted.internet import defer, reactor, task
from twisted.internet.error import CannotListenError
from twisted.python.failure import Failure
from twisted.web.http import FORBIDDEN
from twisted.web.resource import EncodingResourceWrapper, Resource
from twisted.web.server import GzipEncoderFactory, Site
from twisted.web.static import File

import deluge.common
import deluge.component as component
import deluge.core.torrent
from deluge._libtorrent import lt
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.error import AddTorrentError, InvalidTorrentError

from . import common
from .basetest import BaseTestCase

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


class CoreTestCase(BaseTestCase):
    def set_up(self):
        common.set_tmp_config_dir()
        self.rpcserver = RPCServer(listen=False)
        self.core = Core()
        self.core.config.config['lsd'] = False
        self.clock = task.Clock()
        self.core.torrentmanager.callLater = self.clock.callLater
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
                lt.add_torrent_params_flags_t.flag_auto_managed
                | lt.add_torrent_params_flags_t.flag_update_subscribe
                | lt.add_torrent_params_flags_t.flag_apply_ip_filter,
            )
        options = {'add_paused': paused, 'auto_managed': False}
        filepath = common.get_test_data_file(filename)
        with open(filepath, 'rb') as _file:
            filedump = b64encode(_file.read())
        torrent_id = self.core.add_torrent_file(filename, filedump, options)
        return torrent_id

    @defer.inlineCallbacks
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
        self.assertEqual(len(errors), 0)

    @defer.inlineCallbacks
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
        self.assertEqual(len(errors), 1)
        self.assertTrue(str(errors[0]).startswith('Torrent already in session'))

    @defer.inlineCallbacks
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
        self.assertEqual(torrent_id, info_hash)

    def test_add_torrent_file_invalid_filedump(self):
        options = {}
        filename = common.get_test_data_file('test.torrent')
        self.assertRaises(
            AddTorrentError, self.core.add_torrent_file, filename, False, options
        )

    @defer.inlineCallbacks
    def test_add_torrent_url(self):
        url = (
            'http://localhost:%d/ubuntu-9.04-desktop-i386.iso.torrent'
            % self.listen_port
        )
        options = {}
        info_hash = '60d5d82328b4547511fdeac9bf4d0112daa0ce00'

        torrent_id = yield self.core.add_torrent_url(url, options)
        self.assertEqual(torrent_id, info_hash)

    def test_add_torrent_url_with_cookie(self):
        url = 'http://localhost:%d/cookie' % self.listen_port
        options = {}
        headers = {'Cookie': 'password=deluge'}
        info_hash = '60d5d82328b4547511fdeac9bf4d0112daa0ce00'

        d = self.core.add_torrent_url(url, options)
        d.addCallbacks(self.fail, self.assertIsInstance, errbackArgs=(Failure,))

        d = self.core.add_torrent_url(url, options, headers)
        d.addCallbacks(self.assertEqual, self.fail, callbackArgs=(info_hash,))

        return d

    def test_add_torrent_url_with_redirect(self):
        url = 'http://localhost:%d/redirect' % self.listen_port
        options = {}
        info_hash = '60d5d82328b4547511fdeac9bf4d0112daa0ce00'

        d = self.core.add_torrent_url(url, options)
        d.addCallback(self.assertEqual, info_hash)
        return d

    def test_add_torrent_url_with_partial_download(self):
        url = 'http://localhost:%d/partial' % self.listen_port
        options = {}
        info_hash = '60d5d82328b4547511fdeac9bf4d0112daa0ce00'

        d = self.core.add_torrent_url(url, options)
        d.addCallback(self.assertEqual, info_hash)
        return d

    @defer.inlineCallbacks
    def test_add_torrent_magnet(self):
        info_hash = '60d5d82328b4547511fdeac9bf4d0112daa0ce00'
        uri = deluge.common.create_magnet_uri(info_hash)
        options = {}
        torrent_id = yield self.core.add_torrent_magnet(uri, options)
        self.assertEqual(torrent_id, info_hash)

    def test_resume_torrent(self):
        tid1 = self.add_torrent('test.torrent', paused=True)
        tid2 = self.add_torrent('test_torrent.file.torrent', paused=True)
        # Assert paused
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        self.assertTrue(r1['paused'])
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        self.assertTrue(r2['paused'])

        self.core.resume_torrent(tid2)
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        self.assertTrue(r1['paused'])
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        self.assertFalse(r2['paused'])

    def test_resume_torrent_list(self):
        """Backward compatibility for list of torrent_ids."""
        torrent_id = self.add_torrent('test.torrent', paused=True)
        self.core.resume_torrent([torrent_id])
        result = self.core.get_torrent_status(torrent_id, ['paused'])
        self.assertFalse(result['paused'])

    def test_resume_torrents(self):
        tid1 = self.add_torrent('test.torrent', paused=True)
        tid2 = self.add_torrent('test_torrent.file.torrent', paused=True)
        self.core.resume_torrents([tid1, tid2])
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        self.assertFalse(r1['paused'])
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        self.assertFalse(r2['paused'])

    def test_resume_torrents_all(self):
        """With no torrent_ids param, resume all torrents"""
        tid1 = self.add_torrent('test.torrent', paused=True)
        tid2 = self.add_torrent('test_torrent.file.torrent', paused=True)
        self.core.resume_torrents()
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        self.assertFalse(r1['paused'])
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        self.assertFalse(r2['paused'])

    def test_pause_torrent(self):
        tid1 = self.add_torrent('test.torrent')
        tid2 = self.add_torrent('test_torrent.file.torrent')
        # Assert not paused
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        self.assertFalse(r1['paused'])
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        self.assertFalse(r2['paused'])

        self.core.pause_torrent(tid2)
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        self.assertFalse(r1['paused'])
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        self.assertTrue(r2['paused'])

    def test_pause_torrent_list(self):
        """Backward compatibility for list of torrent_ids."""
        torrent_id = self.add_torrent('test.torrent')
        result = self.core.get_torrent_status(torrent_id, ['paused'])
        self.assertFalse(result['paused'])
        self.core.pause_torrent([torrent_id])
        result = self.core.get_torrent_status(torrent_id, ['paused'])
        self.assertTrue(result['paused'])

    def test_pause_torrents(self):
        tid1 = self.add_torrent('test.torrent')
        tid2 = self.add_torrent('test_torrent.file.torrent')

        self.core.pause_torrents([tid1, tid2])
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        self.assertTrue(r1['paused'])
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        self.assertTrue(r2['paused'])

    def test_pause_torrents_all(self):
        """With no torrent_ids param, pause all torrents"""
        tid1 = self.add_torrent('test.torrent')
        tid2 = self.add_torrent('test_torrent.file.torrent')

        self.core.pause_torrents()
        r1 = self.core.get_torrent_status(tid1, ['paused'])
        self.assertTrue(r1['paused'])
        r2 = self.core.get_torrent_status(tid2, ['paused'])
        self.assertTrue(r2['paused'])

    def test_prefetch_metadata_existing(self):
        """Check another call with same magnet returns existing deferred."""
        magnet = 'magnet:?xt=urn:btih:ab570cdd5a17ea1b61e970bb72047de141bce173'
        expected = ('ab570cdd5a17ea1b61e970bb72047de141bce173', None)

        def on_result(result):
            self.assertEqual(result, expected)

        d = self.core.prefetch_magnet_metadata(magnet)
        d.addCallback(on_result)
        d2 = self.core.prefetch_magnet_metadata(magnet)
        d2.addCallback(on_result)
        self.clock.advance(30)
        return defer.DeferredList([d, d2])

    @defer.inlineCallbacks
    def test_remove_torrent(self):
        options = {}
        filename = common.get_test_data_file('test.torrent')
        with open(filename, 'rb') as _file:
            filedump = b64encode(_file.read())
        torrent_id = yield self.core.add_torrent_file_async(filename, filedump, options)
        removed = self.core.remove_torrent(torrent_id, True)
        self.assertTrue(removed)
        self.assertEqual(len(self.core.get_session_state()), 0)

    def test_remove_torrent_invalid(self):
        self.assertRaises(
            InvalidTorrentError,
            self.core.remove_torrent,
            'torrentidthatdoesntexist',
            True,
        )

    @defer.inlineCallbacks
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
            self.assertTrue(val == [])

        d.addCallback(test_ret)

        def test_session_state(val):
            self.assertEqual(len(self.core.get_session_state()), 0)

        d.addCallback(test_session_state)
        yield d

    @defer.inlineCallbacks
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
        self.assertEqual(len(val), 2)
        self.assertEqual(
            val[0], ('invalidid1', 'torrent_id invalidid1 not in session.')
        )
        self.assertEqual(
            val[1], ('invalidid2', 'torrent_id invalidid2 not in session.')
        )

    def test_get_session_status(self):
        status = self.core.get_session_status(
            ['net.recv_tracker_bytes', 'net.sent_tracker_bytes']
        )
        self.assertIsInstance(status, dict)
        self.assertEqual(status['net.recv_tracker_bytes'], 0)
        self.assertEqual(status['net.sent_tracker_bytes'], 0)

    def test_get_session_status_all(self):
        status = self.core.get_session_status([])
        self.assertIsInstance(status, dict)
        self.assertIn('upload_rate', status)
        self.assertIn('net.recv_bytes', status)

    def test_get_session_status_depr(self):
        status = self.core.get_session_status(['num_peers', 'num_unchoked'])
        self.assertIsInstance(status, dict)
        self.assertEqual(status['num_peers'], 0)
        self.assertEqual(status['num_unchoked'], 0)

    def test_get_session_status_rates(self):
        status = self.core.get_session_status(['upload_rate', 'download_rate'])
        self.assertIsInstance(status, dict)
        self.assertEqual(status['upload_rate'], 0)

    def test_get_session_status_ratio(self):
        status = self.core.get_session_status(['write_hit_ratio', 'read_hit_ratio'])
        self.assertIsInstance(status, dict)
        self.assertEqual(status['write_hit_ratio'], 0.0)
        self.assertEqual(status['read_hit_ratio'], 0.0)

    def test_get_free_space(self):
        space = self.core.get_free_space('.')
        # get_free_space returns long on Python 2 (32-bit).
        self.assertTrue(isinstance(space, integer_types))
        self.assertTrue(space >= 0)
        self.assertEqual(self.core.get_free_space('/someinvalidpath'), -1)

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
            self.assertEqual(
                deluge.core.torrent.sanitize_filepath(key, folder=False), pathlist[key]
            )
            self.assertEqual(
                deluge.core.torrent.sanitize_filepath(key, folder=True),
                pathlist[key] + '/',
            )

    def test_get_set_config_values(self):
        self.assertEqual(
            self.core.get_config_values(['abc', 'foo']), {'foo': None, 'abc': None}
        )
        self.assertEqual(self.core.get_config_value('foobar'), None)
        self.core.set_config({'abc': 'def', 'foo': 10, 'foobar': 'barfoo'})
        self.assertEqual(
            self.core.get_config_values(['foo', 'abc']), {'foo': 10, 'abc': 'def'}
        )
        self.assertEqual(self.core.get_config_value('foobar'), 'barfoo')

    def test_read_only_config_keys(self):
        key = 'max_upload_speed'
        self.core.read_only_config_keys = [key]

        old_value = self.core.get_config_value(key)
        self.core.set_config({key: old_value + 10})
        new_value = self.core.get_config_value(key)
        self.assertEqual(old_value, new_value)

        self.core.read_only_config_keys = None

    def test__create_peer_id(self):
        self.assertEqual(self.core._create_peer_id('2.0.0'), '-DE200s-')
        self.assertEqual(self.core._create_peer_id('2.0.0.dev15'), '-DE200D-')
        self.assertEqual(self.core._create_peer_id('2.0.1rc1'), '-DE201r-')
        self.assertEqual(self.core._create_peer_id('2.11.0b2'), '-DE2B0b-')
        self.assertEqual(self.core._create_peer_id('2.4.12b2.dev3'), '-DE24CD-')
