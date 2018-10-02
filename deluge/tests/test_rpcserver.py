# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Bro <bro.development@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import deluge.component as component
import deluge.error
from deluge.common import get_localhost_auth
from deluge.core import rpcserver
from deluge.core.authmanager import AuthManager
from deluge.core.rpcserver import DelugeRPCProtocol, RPCServer
from deluge.log import setup_logger

from .basetest import BaseTestCase

setup_logger('none')


class DelugeRPCProtocolTester(DelugeRPCProtocol):

    messages = []

    def transfer_message(self, data):
        self.messages.append(data)


class RPCServerTestCase(BaseTestCase):
    def set_up(self):
        self.rpcserver = RPCServer(listen=False)
        self.rpcserver.factory.protocol = DelugeRPCProtocolTester
        self.factory = self.rpcserver.factory
        self.session_id = '0'
        self.request_id = 11
        self.protocol = self.rpcserver.factory.protocol()
        self.protocol.factory = self.factory
        self.protocol.transport = self.protocol
        self.factory.session_protocols[self.session_id] = self.protocol
        self.factory.authorized_sessions[self.session_id] = None
        self.factory.interested_events[self.session_id] = ['TorrentFolderRenamedEvent']
        self.protocol.sessionno = self.session_id
        return component.start()

    def tear_down(self):
        def on_shutdown(result):
            del self.rpcserver

        return component.shutdown().addCallback(on_shutdown)

    def test_emit_event_for_session_id(self):
        torrent_id = '12'
        from deluge.event import TorrentFolderRenamedEvent

        data = [torrent_id, 'new name', 'old name']
        e = TorrentFolderRenamedEvent(*data)
        self.rpcserver.emit_event_for_session_id(self.session_id, e)
        msg = self.protocol.messages.pop()
        self.assertEqual(msg[0], rpcserver.RPC_EVENT, str(msg))
        self.assertEqual(msg[1], 'TorrentFolderRenamedEvent', str(msg))
        self.assertEqual(msg[2], data, str(msg))

    def test_invalid_client_login(self):
        self.protocol.dispatch(self.request_id, 'daemon.login', [1], {})
        msg = self.protocol.messages.pop()
        self.assertEqual(msg[0], rpcserver.RPC_ERROR)
        self.assertEqual(msg[1], self.request_id)

    def test_valid_client_login(self):
        self.authmanager = AuthManager()
        auth = get_localhost_auth()
        self.protocol.dispatch(
            self.request_id, 'daemon.login', auth, {'client_version': 'Test'}
        )
        msg = self.protocol.messages.pop()
        self.assertEqual(msg[0], rpcserver.RPC_RESPONSE, str(msg))
        self.assertEqual(msg[1], self.request_id, str(msg))
        self.assertEqual(msg[2], rpcserver.AUTH_LEVEL_ADMIN, str(msg))

    def test_client_login_error(self):
        # This test causes error log prints while running the test...
        self.protocol.transport = None  # This should cause AttributeError
        self.authmanager = AuthManager()
        auth = get_localhost_auth()
        self.protocol.dispatch(
            self.request_id, 'daemon.login', auth, {'client_version': 'Test'}
        )
        msg = self.protocol.messages.pop()
        self.assertEqual(msg[0], rpcserver.RPC_ERROR)
        self.assertEqual(msg[1], self.request_id)
        self.assertEqual(msg[2], 'WrappedException')
        self.assertEqual(msg[3][1], 'AttributeError')

    def test_client_invalid_method_call(self):
        self.authmanager = AuthManager()
        auth = get_localhost_auth()
        self.protocol.dispatch(self.request_id, 'invalid_function', auth, {})
        msg = self.protocol.messages.pop()
        self.assertEqual(msg[0], rpcserver.RPC_ERROR)
        self.assertEqual(msg[1], self.request_id)
        self.assertEqual(msg[2], 'WrappedException')
        self.assertEqual(msg[3][1], 'AttributeError')

    def test_daemon_info(self):
        self.protocol.dispatch(self.request_id, 'daemon.info', [], {})
        msg = self.protocol.messages.pop()
        self.assertEqual(msg[0], rpcserver.RPC_RESPONSE, str(msg))
        self.assertEqual(msg[1], self.request_id, str(msg))
        self.assertEqual(msg[2], deluge.common.get_version(), str(msg))
