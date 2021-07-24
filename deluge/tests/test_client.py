# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

from twisted.internet import defer

import deluge.component as component
from deluge import error
from deluge.common import AUTH_LEVEL_NORMAL, get_localhost_auth
from deluge.core.authmanager import AUTH_LEVEL_ADMIN
from deluge.ui.client import Client, DaemonSSLProxy, client

from .basetest import BaseTestCase
from .daemon_base import DaemonBase


class NoVersionSendingDaemonSSLProxy(DaemonSSLProxy):
    def authenticate(self, username, password):
        self.login_deferred = defer.Deferred()
        d = self.call('daemon.login', username, password)
        d.addCallback(self.__on_login, username)
        d.addErrback(self.__on_login_fail)
        return self.login_deferred

    def __on_login(self, result, username):
        self.login_deferred.callback(result)

    def __on_login_fail(self, result):
        self.login_deferred.errback(result)


class NoVersionSendingClient(Client):
    def connect(
        self,
        host='127.0.0.1',
        port=58846,
        username='',
        password='',
        skip_authentication=False,
    ):
        self._daemon_proxy = NoVersionSendingDaemonSSLProxy()
        self._daemon_proxy.set_disconnect_callback(self.__on_disconnect)

        d = self._daemon_proxy.connect(host, port)

        def on_connect_fail(reason):
            self.disconnect()
            return reason

        def on_authenticate(result, daemon_info):
            return result

        def on_authenticate_fail(reason):
            return reason

        def on_connected(daemon_version):
            return daemon_version

        def authenticate(daemon_version, username, password):
            d = self._daemon_proxy.authenticate(username, password)
            d.addCallback(on_authenticate, daemon_version)
            d.addErrback(on_authenticate_fail)
            return d

        d.addCallback(on_connected)
        d.addErrback(on_connect_fail)
        if not skip_authentication:
            d.addCallback(authenticate, username, password)
        return d

    def __on_disconnect(self):
        if self.disconnect_callback:
            self.disconnect_callback()


class ClientTestCase(BaseTestCase, DaemonBase):
    def set_up(self):
        d = self.common_set_up()
        d.addCallback(self.start_core)
        d.addErrback(self.terminate_core)
        return d

    def tear_down(self):
        d = component.shutdown()
        d.addCallback(self.terminate_core)
        return d

    def test_connect_no_credentials(self):
        d = client.connect('localhost', self.listen_port, username='', password='')

        def on_connect(result):
            self.assertEqual(client.get_auth_level(), AUTH_LEVEL_ADMIN)
            self.addCleanup(client.disconnect)
            return result

        d.addCallbacks(on_connect, self.fail)
        return d

    def test_connect_localclient(self):
        username, password = get_localhost_auth()
        d = client.connect(
            'localhost', self.listen_port, username=username, password=password
        )

        def on_connect(result):
            self.assertEqual(client.get_auth_level(), AUTH_LEVEL_ADMIN)
            self.addCleanup(client.disconnect)
            return result

        d.addCallbacks(on_connect, self.fail)
        return d

    def test_connect_bad_password(self):
        username, password = get_localhost_auth()
        d = client.connect(
            'localhost', self.listen_port, username=username, password=password + '1'
        )

        def on_failure(failure):
            self.assertEqual(failure.trap(error.BadLoginError), error.BadLoginError)
            self.assertEqual(failure.value.message, 'Password does not match')
            self.addCleanup(client.disconnect)

        d.addCallbacks(self.fail, on_failure)
        return d

    def test_connect_invalid_user(self):
        username, password = get_localhost_auth()
        d = client.connect('localhost', self.listen_port, username='invalid-user')

        def on_failure(failure):
            self.assertEqual(failure.trap(error.BadLoginError), error.BadLoginError)
            self.assertEqual(failure.value.message, 'Username does not exist')
            self.addCleanup(client.disconnect)

        d.addCallbacks(self.fail, on_failure)
        return d

    def test_connect_without_password(self):
        username, password = get_localhost_auth()
        d = client.connect('localhost', self.listen_port, username=username)

        def on_failure(failure):
            self.assertEqual(
                failure.trap(error.AuthenticationRequired), error.AuthenticationRequired
            )
            self.assertEqual(failure.value.username, username)
            self.addCleanup(client.disconnect)

        d.addCallbacks(self.fail, on_failure)
        return d

    @defer.inlineCallbacks
    def test_connect_with_password(self):
        username, password = get_localhost_auth()
        yield client.connect(
            'localhost', self.listen_port, username=username, password=password
        )
        yield client.core.create_account('testuser', 'testpw', 'DEFAULT')
        yield client.disconnect()
        ret = yield client.connect(
            'localhost', self.listen_port, username='testuser', password='testpw'
        )
        self.assertEqual(ret, AUTH_LEVEL_NORMAL)
        yield

    @defer.inlineCallbacks
    def test_invalid_rpc_method_call(self):
        yield client.connect('localhost', self.listen_port, username='', password='')
        d = client.core.invalid_method()

        def on_failure(failure):
            self.assertEqual(
                failure.trap(error.WrappedException), error.WrappedException
            )
            self.addCleanup(client.disconnect)

        d.addCallbacks(self.fail, on_failure)
        yield d

    def test_connect_without_sending_client_version_fails(self):
        username, password = get_localhost_auth()
        no_version_sending_client = NoVersionSendingClient()
        d = no_version_sending_client.connect(
            'localhost', self.listen_port, username=username, password=password
        )

        def on_failure(failure):
            self.assertEqual(
                failure.trap(error.IncompatibleClient), error.IncompatibleClient
            )
            self.addCleanup(no_version_sending_client.disconnect)

        d.addCallbacks(self.fail, on_failure)
        return d
