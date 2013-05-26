#
# test_rpcserver.py
#
# Copyright (C) 2013 Bro <bro.development@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#

import os

from twisted.trial import unittest
from twisted.python import log

import deluge.component as component
import deluge.error
from deluge.core import rpcserver
from deluge.ui.common import get_localhost_auth
from deluge.core.authmanager import AuthManager
from deluge.core.rpcserver import RPCServer, DelugeRPCProtocol

from deluge.log import setupLogger

setupLogger("none")

class DelugeRPCProtocolTester(DelugeRPCProtocol):

    messages = []

    def transfer_message(self, data):
        import traceback
        self.messages.append(data)

class RPCServerTestCase(unittest.TestCase):

    def setUp(self):
        self.rpcserver = RPCServer(listen=False)
        self.rpcserver.factory.protocol = DelugeRPCProtocolTester
        self.factory = self.rpcserver.factory
        self.session_id = "0"
        self.request_id = 11
        self.protocol = self.rpcserver.factory.protocol()
        self.protocol.factory = self.factory
        self.protocol.transport = self.protocol
        self.factory.session_protocols[self.session_id] = self.protocol
        self.factory.authorized_sessions[self.session_id] = None
        self.factory.interested_events[self.session_id] = ["TorrentFolderRenamedEvent"]
        self.protocol.sessionno = self.session_id
        return component.start()

    def tearDown(self):
        def on_shutdown(result):
            component._ComponentRegistry.components = {}
            del self.rpcserver
        return component.shutdown().addCallback(on_shutdown)

    def test_emit_event_for_session_id(self):
        torrent_id = "12"
        from deluge.event import TorrentFolderRenamedEvent
        data = [torrent_id, "new name", "old name"]
        e = TorrentFolderRenamedEvent(*data)
        self.rpcserver.emit_event_for_session_id(self.session_id, e)
        msg = self.protocol.messages.pop()
        self.assertEquals(msg[0], rpcserver.RPC_EVENT, str(msg))
        self.assertEquals(msg[1], "TorrentFolderRenamedEvent", str(msg))
        self.assertEquals(msg[2], data, str(msg))

    def test_invalid_client_login(self):
        ret = self.protocol.dispatch(self.request_id, "daemon.login", [1], {})
        msg = self.protocol.messages.pop()
        self.assertEquals(msg[0], rpcserver.RPC_ERROR)
        self.assertEquals(msg[1], self.request_id)

    def test_invalid_client_login(self):
        ret = self.protocol.dispatch(self.request_id, "daemon.login", [1], {})
        msg = self.protocol.messages.pop()
        self.assertEquals(msg[0], rpcserver.RPC_ERROR)
        self.assertEquals(msg[1], self.request_id)

    def test_valid_client_login(self):
        self.authmanager = AuthManager()
        auth = get_localhost_auth()
        ret = self.protocol.dispatch(self.request_id, "daemon.login", auth, {"client_version": "Test"})
        msg = self.protocol.messages.pop()
        self.assertEquals(msg[0], rpcserver.RPC_RESPONSE, str(msg))
        self.assertEquals(msg[1], self.request_id, str(msg))
        self.assertEquals(msg[2], rpcserver.AUTH_LEVEL_ADMIN, str(msg))

    def test_client_login_error(self):
        # This test causes error log prints while running the test...
        self.protocol.transport = None   # This should causes AttributeError
        self.authmanager = AuthManager()
        auth = get_localhost_auth()
        self.protocol.dispatch(self.request_id, "daemon.login", auth, {"client_version": "Test"})
        msg = self.protocol.messages.pop()
        self.assertEquals(msg[0], rpcserver.RPC_ERROR)
        self.assertEquals(msg[1], self.request_id)
        self.assertEquals(msg[2], "WrappedException")
        self.assertEquals(msg[3][1], "AttributeError")

    def test_daemon_info(self):
        ret = self.protocol.dispatch(self.request_id, "daemon.info", [], {})
        msg = self.protocol.messages.pop()
        self.assertEquals(msg[0], rpcserver.RPC_RESPONSE, str(msg))
        self.assertEquals(msg[1], self.request_id, str(msg))
        self.assertEquals(msg[2], deluge.common.get_version(), str(msg))
