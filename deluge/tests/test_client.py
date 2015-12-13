from twisted.internet import defer
from twisted.internet.error import CannotListenError

import deluge.component as component
import deluge.ui.common
from deluge import error
from deluge.core.authmanager import AUTH_LEVEL_ADMIN
from deluge.ui.client import Client, DaemonSSLProxy, client

from . import common
from .basetest import BaseTestCase


class NoVersionSendingDaemonSSLProxy(DaemonSSLProxy):
    def authenticate(self, username, password):
        self.login_deferred = defer.Deferred()
        d = self.call("daemon.login", username, password)
        d.addCallback(self.__on_login, username)
        d.addErrback(self.__on_login_fail)
        return self.login_deferred

    def __on_login(self, result, username):
        self.login_deferred.callback(result)

    def __on_login_fail(self, result):
        self.login_deferred.errback(result)


class NoVersionSendingClient(Client):

    def connect(self, host="127.0.0.1", port=58846, username="", password="",
                skip_authentication=False):
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


class ClientTestCase(BaseTestCase):

    def set_up(self):
        self.listen_port = 58846
        for dummy in range(10):
            try:
                self.core = common.start_core(listen_port=self.listen_port)
            except CannotListenError as ex:
                exception_error = ex
                self.listen_port += 1
            else:
                break
        else:
            raise exception_error

    def tear_down(self):
        self.core.terminate()
        return component.shutdown()

    def test_connect_no_credentials(self):
        d = client.connect(
            "localhost", self.listen_port, username="", password=""
        )

        def on_connect(result):
            self.assertEqual(client.get_auth_level(), AUTH_LEVEL_ADMIN)
            self.addCleanup(client.disconnect)
            return result

        d.addCallback(on_connect)
        return d

    def test_connect_localclient(self):
        username, password = deluge.ui.common.get_localhost_auth()
        d = client.connect(
            "localhost", self.listen_port, username=username, password=password
        )

        def on_connect(result):
            self.assertEqual(client.get_auth_level(), AUTH_LEVEL_ADMIN)
            self.addCleanup(client.disconnect)
            return result

        d.addCallback(on_connect)
        return d

    def test_connect_bad_password(self):
        username, password = deluge.ui.common.get_localhost_auth()
        d = client.connect(
            "localhost", self.listen_port, username=username, password=password + "1"
        )

        def on_failure(failure):
            self.assertEqual(
                failure.trap(error.BadLoginError),
                error.BadLoginError
            )
            self.addCleanup(client.disconnect)

        d.addErrback(on_failure)
        return d

    def test_connect_without_password(self):
        username, password = deluge.ui.common.get_localhost_auth()
        d = client.connect(
            "localhost", self.listen_port, username=username
        )

        def on_failure(failure):
            self.assertEqual(
                failure.trap(error.AuthenticationRequired),
                error.AuthenticationRequired
            )
            self.assertEqual(failure.value.username, username)
            self.addCleanup(client.disconnect)

        d.addErrback(on_failure)
        return d

    @defer.inlineCallbacks
    def test_invalid_rpc_method_call(self):
        yield client.connect(
            "localhost", self.listen_port, username="", password=""
        )
        d = client.core.invalid_method()

        def on_failure(failure):
            self.assertEqual(
                failure.trap(error.WrappedException),
                error.WrappedException
            )
            self.addCleanup(client.disconnect)
        d.addErrback(on_failure)
        yield d

    def test_connect_without_sending_client_version_fails(self):
        username, password = deluge.ui.common.get_localhost_auth()
        no_version_sending_client = NoVersionSendingClient()
        d = no_version_sending_client.connect(
            "localhost", self.listen_port, username=username, password=password
        )

        def on_failure(failure):
            self.assertEqual(
                failure.trap(error.IncompatibleClient),
                error.IncompatibleClient
            )
            self.addCleanup(no_version_sending_client.disconnect)

        d.addErrback(on_failure)
        return d
